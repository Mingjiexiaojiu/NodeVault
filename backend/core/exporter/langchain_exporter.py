import textwrap
from typing import Any

from backend.core.exporter.base import BaseExporter

_TYPE_MAP: dict[str, str] = {
    "string": "str",
    "integer": "int",
    "number": "float",
    "boolean": "bool",
    "array": "list",
    "object": "dict",
}


def _json_type_to_python(json_type: str) -> str:
    return _TYPE_MAP.get(json_type, "Any")


def _model_class_name(node_name: str) -> str:
    return "".join(w.capitalize() for w in node_name.split("_")) + "Input"


def _generate_pydantic_model(name: str, schema: dict[str, Any]) -> str:
    class_name = _model_class_name(name)
    props: dict[str, Any] = schema.get("properties") or {}
    required: list[str] = schema.get("required") or []

    fields: list[str] = []
    for field_name, field_info in props.items():
        py_type = _json_type_to_python(field_info.get("type", "any"))
        field_desc = field_info.get("description", "")
        default = field_info.get("default")
        if field_name in required:
            fields.append(
                f'    {field_name}: {py_type} = Field(..., description="{field_desc}")'
            )
        else:
            default_repr = repr(default) if default is not None else "None"
            fields.append(
                f'    {field_name}: {py_type} | None = Field({default_repr}, description="{field_desc}")'
            )

    fields_str = "\n".join(fields) if fields else "    pass"
    return f"class {class_name}(BaseModel):\n{fields_str}"


class LangChainExporter(BaseExporter):
    """将 Node 导出为 LangChain StructuredTool Python 代码"""

    def export_node(self, node: dict[str, Any], version: dict[str, Any]) -> str:
        name = node["name"]
        description = node.get("description") or ""
        input_schema: dict[str, Any] = version.get("input_schema") or {}
        class_name = _model_class_name(name)
        pydantic_model = _generate_pydantic_model(name, input_schema)

        code = textwrap.dedent(f"""\
            from langchain_core.tools import StructuredTool
            from pydantic import BaseModel, Field
            from typing import Any
            from nodevault import NodeVaultClient

            vault = NodeVaultClient(base_url="{{NODEVAULT_URL}}", api_key="{{NODEVAULT_API_KEY}}")

            {pydantic_model}

            def _invoke_{name}(**kwargs):
                result = vault.invoke("{name}", kwargs)
                return result.output

            {name}_tool = StructuredTool(
                name="{name}",
                description=\"\"\"{description}\"\"\",
                args_schema={class_name},
                func=_invoke_{name},
            )
        """)
        return code

    def export_nodes(self, nodes: list[dict[str, Any]]) -> str:
        parts = [self.export_node(item["node"], item["version"]) for item in nodes]
        tool_names = [f"{item['node']['name']}_tool" for item in nodes]
        tools_list = f"\ntools = [{', '.join(tool_names)}]\n"
        return "\n".join(parts) + tools_list
