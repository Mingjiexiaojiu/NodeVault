"""Unit tests for Exporter classes (1.6)"""
import io
import zipfile

import pytest

from backend.core.exporter.openai_exporter import OpenAIExporter
from backend.core.exporter.langchain_exporter import LangChainExporter
from backend.core.exporter.skill_package_exporter import SkillPackageExporter


SAMPLE_NODE = {
    "name": "detect_fund_pool",
    "display_name": "Detect Fund Pool",
    "description": "基于图算法检测可疑资金归集行为",
    "tags": ["finance", "risk"],
    "category": "risk-analysis",
}

SAMPLE_VERSION = {
    "version": "1.0.0",
    "input_schema": {
        "type": "object",
        "properties": {
            "transactions": {"type": "array", "description": "交易流水列表"},
            "threshold": {"type": "number", "description": "风险阈值", "default": 0.7},
        },
        "required": ["transactions"],
    },
    "output_schema": {
        "type": "object",
        "properties": {
            "suspicious_accounts": {"type": "array", "description": "可疑账户"},
        },
    },
}


class TestOpenAIExporter:
    def setup_method(self):
        self.exporter = OpenAIExporter()

    def test_export_node_structure(self):
        result = self.exporter.export_node(SAMPLE_NODE, SAMPLE_VERSION)
        assert result["type"] == "function"
        assert "function" in result
        fn = result["function"]
        assert "name" in fn
        assert "description" in fn
        assert "parameters" in fn

    def test_safe_name_lowercase(self):
        assert self.exporter._safe_name("MyNode-v1") == "mynode_v1"

    def test_safe_name_max_length(self):
        long_name = "a" * 100
        assert len(self.exporter._safe_name(long_name)) == 64

    def test_safe_name_special_chars(self):
        assert self.exporter._safe_name("node.name/test") == "node_name_test"

    def test_description_includes_tags(self):
        desc = self.exporter._build_description(SAMPLE_NODE)
        assert "finance" in desc
        assert "risk" in desc

    def test_description_max_length(self):
        node = {**SAMPLE_NODE, "description": "x" * 2000}
        desc = self.exporter._build_description(node)
        assert len(desc) <= 1024

    def test_export_nodes_batch(self):
        items = [
            {"node": SAMPLE_NODE, "version": SAMPLE_VERSION},
            {"node": {**SAMPLE_NODE, "name": "node_two"}, "version": SAMPLE_VERSION},
        ]
        result = self.exporter.export_nodes(items)
        assert len(result) == 2
        assert all(r["type"] == "function" for r in result)

    def test_clean_schema_removes_internal_fields(self):
        schema = {"$schema": "...", "$id": "...", "type": "object"}
        cleaned = self.exporter._clean_schema(schema)
        assert "$schema" not in cleaned
        assert "$id" not in cleaned
        assert cleaned["type"] == "object"


class TestLangChainExporter:
    def setup_method(self):
        self.exporter = LangChainExporter()

    def test_export_node_contains_class_name(self):
        code = self.exporter.export_node(SAMPLE_NODE, SAMPLE_VERSION)
        assert "DetectFundPoolInput" in code
        assert "StructuredTool" in code
        assert "detect_fund_pool_tool" in code

    def test_required_field_uses_ellipsis(self):
        code = self.exporter.export_node(SAMPLE_NODE, SAMPLE_VERSION)
        assert "Field(...," in code

    def test_optional_field_has_none_type(self):
        code = self.exporter.export_node(SAMPLE_NODE, SAMPLE_VERSION)
        assert "| None" in code

    def test_export_nodes_adds_tools_list(self):
        items = [
            {"node": SAMPLE_NODE, "version": SAMPLE_VERSION},
            {"node": {**SAMPLE_NODE, "name": "node_two"}, "version": SAMPLE_VERSION},
        ]
        code = self.exporter.export_nodes(items)
        assert "tools = [" in code
        assert "detect_fund_pool_tool" in code
        assert "node_two_tool" in code


class TestSkillPackageExporter:
    def setup_method(self):
        self.exporter = SkillPackageExporter()

    def test_returns_valid_zip(self):
        data = self.exporter.export_node(SAMPLE_NODE, SAMPLE_VERSION)
        assert isinstance(data, bytes)
        buf = io.BytesIO(data)
        with zipfile.ZipFile(buf) as zf:
            names = zf.namelist()
        assert "skill.yaml" in names
        assert "skill.py" in names
        assert "README.md" in names
        assert "tests/test_skill.py" in names

    def test_skill_yaml_contains_node_name(self):
        data = self.exporter.export_node(SAMPLE_NODE, SAMPLE_VERSION)
        buf = io.BytesIO(data)
        with zipfile.ZipFile(buf) as zf:
            content = zf.read("skill.yaml").decode()
        assert "detect_fund_pool" in content
        assert "entrypoint" in content

    def test_skill_py_uses_sdk(self):
        data = self.exporter.export_node(SAMPLE_NODE, SAMPLE_VERSION)
        buf = io.BytesIO(data)
        with zipfile.ZipFile(buf) as zf:
            content = zf.read("skill.py").decode()
        assert "NodeVaultClient" in content
        assert "detect_fund_pool" in content
