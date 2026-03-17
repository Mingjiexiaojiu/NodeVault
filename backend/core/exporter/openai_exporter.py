import re
from typing import Any

from backend.core.exporter.base import BaseExporter


class OpenAIExporter(BaseExporter):
    """将 Node 导出为 OpenAI Function Calling 格式"""

    def export_node(self, node: dict[str, Any], version: dict[str, Any]) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self._safe_name(node["name"]),
                "description": self._build_description(node),
                "parameters": self._clean_schema(version.get("input_schema") or {}),
            },
        }

    def export_nodes(self, nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [self.export_node(item["node"], item["version"]) for item in nodes]

    def _safe_name(self, name: str) -> str:
        """确保函数名符合 OpenAI 规范：仅含 [a-z0-9_]，最长 64 字符"""
        safe = re.sub(r"[^a-z0-9_]", "_", name.lower())
        return safe[:64]

    def _build_description(self, node: dict[str, Any]) -> str:
        desc = node.get("description") or ""
        tags: list[str] = node.get("tags") or []
        if tags:
            tag_str = ", ".join(tags)
            desc = f"{desc} [标签: {tag_str}]" if desc else f"[标签: {tag_str}]"
        return desc[:1024]
