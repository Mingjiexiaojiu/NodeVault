"""Map OpenAPI spec operations to Node drafts for batch import."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

# Noise endpoint patterns — default deselected
_NOISE_PATTERNS = [
    re.compile(r"^/health", re.IGNORECASE),
    re.compile(r"^/ready", re.IGNORECASE),
    re.compile(r"^/metrics$", re.IGNORECASE),
    re.compile(r"^/prometheus", re.IGNORECASE),
    re.compile(r"^/favicon\.ico$", re.IGNORECASE),
    re.compile(r"^/openapi\.json$", re.IGNORECASE),
    re.compile(r"^/swagger", re.IGNORECASE),
    re.compile(r"^/docs$", re.IGNORECASE),
    re.compile(r"^/redoc$", re.IGNORECASE),
]

HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}


@dataclass
class NodeDraft:
    """A proposed Node derived from a single OpenAPI operation."""

    suggested_name: str
    display_name: str
    description: str
    endpoint: str  # relative path, e.g. /pets/{petId}
    method: str  # GET, POST, etc.
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    category: str | None = None
    tags: list[str] = field(default_factory=list)
    selected: bool = True


def _is_noise(path: str) -> bool:
    return any(p.search(path) for p in _NOISE_PATTERNS)


def _make_name(operation_id: str | None, method: str, path: str) -> str:
    """Generate a suggested name from operationId or method+path."""
    if operation_id:
        return operation_id
    # Fallback: method_path_segments
    cleaned = re.sub(r"[{}]", "", path)
    parts = [p for p in cleaned.strip("/").split("/") if p]
    return f"{method.lower()}_{'_'.join(parts)}" if parts else f"{method.lower()}_root"


def _resolve_ref(ref: str, spec: dict[str, Any]) -> dict[str, Any]:
    """Resolve a $ref pointer like '#/components/schemas/Pet'."""
    if not ref.startswith("#/"):
        return {}
    parts = ref.lstrip("#/").split("/")
    obj: Any = spec
    for p in parts:
        if isinstance(obj, dict):
            obj = obj.get(p, {})
        else:
            return {}
    return obj if isinstance(obj, dict) else {}


def _extract_request_schema(operation: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    """Extract input schema from requestBody (OAS 3.x) or parameters (Swagger 2.x)."""
    # OpenAPI 3.x
    rb = operation.get("requestBody", {})
    if isinstance(rb, dict):
        content = rb.get("content", {})
        json_media = content.get("application/json", {})
        schema = json_media.get("schema", {})
        if "$ref" in schema:
            return _resolve_ref(schema["$ref"], spec)
        if schema:
            return schema

    # Swagger 2.x — body parameter
    for param in operation.get("parameters", []):
        if param.get("in") == "body":
            schema = param.get("schema", {})
            if "$ref" in schema:
                return _resolve_ref(schema["$ref"], spec)
            return schema

    return {}


def _extract_response_schema(operation: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    """Extract output schema from the success response."""
    responses = operation.get("responses", {})
    for code in ("200", "201", "default"):
        resp = responses.get(code, {})
        if not resp:
            continue
        # OpenAPI 3.x
        content = resp.get("content", {})
        json_media = content.get("application/json", {})
        schema = json_media.get("schema", {})
        if "$ref" in schema:
            return _resolve_ref(schema["$ref"], spec)
        if schema:
            return schema
        # Swagger 2.x
        schema = resp.get("schema", {})
        if "$ref" in schema:
            return _resolve_ref(schema["$ref"], spec)
        if schema:
            return schema
    return {}


def parse_operations(spec: dict[str, Any]) -> list[NodeDraft]:
    """Parse all operations from an OpenAPI/Swagger spec into NodeDrafts."""
    drafts: list[NodeDraft] = []
    paths = spec.get("paths", {})

    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        for method in HTTP_METHODS:
            operation = path_item.get(method)
            if not operation or not isinstance(operation, dict):
                continue

            op_id = operation.get("operationId")
            summary = operation.get("summary", "")
            description = operation.get("description", "")
            op_tags = operation.get("tags", [])

            draft = NodeDraft(
                suggested_name=_make_name(op_id, method, path),
                display_name=summary or _make_name(op_id, method, path),
                description=description,
                endpoint=path,
                method=method.upper(),
                input_schema=_extract_request_schema(operation, spec),
                output_schema=_extract_response_schema(operation, spec),
                category=op_tags[0] if op_tags else None,
                tags=op_tags,
                selected=not _is_noise(path),
            )
            drafts.append(draft)

    return drafts
