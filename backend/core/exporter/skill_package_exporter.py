import io
import textwrap
import zipfile
from typing import Any

import yaml

from backend.core.exporter.base import BaseExporter


def _generate_skill_yaml(node: dict[str, Any], version: dict[str, Any]) -> str:
    input_schema: dict[str, Any] = version.get("input_schema") or {}
    output_schema: dict[str, Any] = version.get("output_schema") or {}

    input_fields = {
        k: {"type": v.get("type", "any"), "description": v.get("description", "")}
        for k, v in (input_schema.get("properties") or {}).items()
    }
    output_fields = {
        k: {"type": v.get("type", "any"), "description": v.get("description", "")}
        for k, v in (output_schema.get("properties") or {}).items()
    }

    data = {
        "name": node["name"],
        "version": version.get("version", "1.0.0"),
        "description": node.get("description") or "",
        "category": node.get("category") or "general",
        "tags": node.get("tags") or [],
        "entrypoint": "skill.execute",
        "input": input_fields,
        "output": output_fields,
        "requires": [],
    }
    return yaml.dump(data, allow_unicode=True, sort_keys=False)


def _generate_skill_py(node: dict[str, Any], version: dict[str, Any]) -> str:
    name = node["name"]
    description = node.get("description") or ""
    input_schema: dict[str, Any] = version.get("input_schema") or {}
    props: dict[str, Any] = input_schema.get("properties") or {}
    required: list[str] = input_schema.get("required") or []

    params: list[str] = []
    for field_name, field_info in props.items():
        if field_name in required:
            params.append(field_name)
        else:
            default = field_info.get("default", "None")
            params.append(f"{field_name}={default!r}")

    params_str = ", ".join(params) if params else "**kwargs"
    kwargs_dict = "{" + ", ".join(f'"{p.split("=")[0]}": {p.split("=")[0]}' for p in params) + "}" if params else "kwargs"

    return textwrap.dedent(f"""\
        \"\"\"
        NodeVault Skill: {name}
        自动生成 by NodeVault
        \"\"\"
        import os
        from nodevault import NodeVaultClient

        _vault = None


        def _get_vault():
            global _vault
            if _vault is None:
                _vault = NodeVaultClient(
                    base_url=os.environ["NODEVAULT_URL"],
                    api_key=os.environ["NODEVAULT_API_KEY"],
                )
            return _vault


        def execute({params_str}) -> dict:
            \"\"\"
            {description}
            \"\"\"
            result = _get_vault().invoke(
                "{name}",
                input_data={kwargs_dict},
            )
            return result.output
    """)


def _generate_readme(node: dict[str, Any], version: dict[str, Any]) -> str:
    name = node["name"]
    description = node.get("description") or ""
    ver = version.get("version", "1.0.0")
    return textwrap.dedent(f"""\
        # {name}

        **Version:** {ver}

        {description}

        ## Usage

        ```python
        import os
        os.environ["NODEVAULT_URL"] = "http://your-nodevault-url"
        os.environ["NODEVAULT_API_KEY"] = "your-api-key"

        from skill import execute

        result = execute(...)
        print(result)
        ```

        ## Requirements

        - `nodevault` Python SDK
        - `NODEVAULT_URL` and `NODEVAULT_API_KEY` environment variables
    """)


def _generate_test_py(node: dict[str, Any]) -> str:
    name = node["name"]
    return textwrap.dedent(f"""\
        import os
        import pytest
        from unittest.mock import MagicMock, patch

        os.environ.setdefault("NODEVAULT_URL", "http://localhost:8000")
        os.environ.setdefault("NODEVAULT_API_KEY", "test-key")


        @pytest.fixture
        def mock_vault():
            with patch("skill._get_vault") as mock:
                client = MagicMock()
                mock.return_value = client
                yield client


        def test_{name}_execute(mock_vault):
            mock_vault.invoke.return_value = MagicMock(output={{"result": "ok"}})
            from skill import execute
            # TODO: Replace with actual test inputs
            result = execute()
            assert result is not None
    """)


class SkillPackageExporter(BaseExporter):
    """将 Node 导出为可安装的 Skill Package ZIP"""

    def export_node(self, node: dict[str, Any], version: dict[str, Any]) -> bytes:
        """生成 ZIP 字节流"""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("skill.yaml", _generate_skill_yaml(node, version))
            zf.writestr("skill.py", _generate_skill_py(node, version))
            zf.writestr("README.md", _generate_readme(node, version))
            zf.writestr("tests/test_skill.py", _generate_test_py(node))
        buf.seek(0)
        return buf.read()

    def export_nodes(self, nodes: list[dict[str, Any]]) -> list[bytes]:
        return [self.export_node(item["node"], item["version"]) for item in nodes]
