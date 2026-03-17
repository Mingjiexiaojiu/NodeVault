from abc import ABC, abstractmethod
from typing import Any


class BaseExporter(ABC):
    """所有 Skill 导出器的基类"""

    @abstractmethod
    def export_node(self, node: dict[str, Any], version: dict[str, Any]) -> Any:
        """将单个 Node 导出为目标格式"""

    @abstractmethod
    def export_nodes(self, nodes: list[dict[str, Any]]) -> Any:
        """将多个 Node 批量导出。每个元素形如 {"node": {...}, "version": {...}}"""

    def _clean_schema(self, schema: dict[str, Any]) -> dict[str, Any]:
        """清理 schema，移除 NodeVault 内部字段"""
        cleaned = dict(schema)
        cleaned.pop("$schema", None)
        cleaned.pop("$id", None)
        return cleaned
