import pytest
from pydantic import ValidationError

from backend.schemas.node_schema import NodeSchemaBase, RuntimeConfig
from backend.schemas.enums import NodeType, RuntimeType, HttpMethod


def _make_node(**overrides) -> dict:
    """Helper to build a valid node schema dict with overrides."""
    base = {
        "name": "detect_fund_pool",
        "version": "1.0.0",
        "type": "analysis",
        "input_schema": {
            "type": "object",
            "properties": {"data": {"type": "string"}},
        },
        "output_schema": {
            "type": "object",
            "properties": {"result": {"type": "string"}},
        },
        "runtime": {
            "type": "http",
            "endpoint": "http://example.com/api",
            "method": "POST",
        },
    }
    base.update(overrides)
    return base


class TestNodeName:
    def test_valid_name(self):
        node = NodeSchemaBase(**_make_node(name="detect_fund_pool"))
        assert node.name == "detect_fund_pool"

    def test_valid_name_with_digits(self):
        node = NodeSchemaBase(**_make_node(name="clean_v2_data"))
        assert node.name == "clean_v2_data"

    def test_invalid_name_uppercase(self):
        with pytest.raises(ValidationError, match="snake_case"):
            NodeSchemaBase(**_make_node(name="Detect-Fund-Pool"))

    def test_invalid_name_too_short(self):
        with pytest.raises(ValidationError):
            NodeSchemaBase(**_make_node(name="a"))

    def test_invalid_name_with_spaces(self):
        with pytest.raises(ValidationError, match="snake_case"):
            NodeSchemaBase(**_make_node(name="detect fund pool"))

    def test_invalid_name_starts_with_digit(self):
        with pytest.raises(ValidationError, match="snake_case"):
            NodeSchemaBase(**_make_node(name="1detect"))


class TestNodeVersion:
    def test_valid_version(self):
        node = NodeSchemaBase(**_make_node(version="1.0.0"))
        assert node.version == "1.0.0"

    def test_valid_version_large_numbers(self):
        node = NodeSchemaBase(**_make_node(version="10.20.30"))
        assert node.version == "10.20.30"

    def test_invalid_version_two_parts(self):
        with pytest.raises(ValidationError, match="SemVer"):
            NodeSchemaBase(**_make_node(version="1.0"))

    def test_invalid_version_with_prefix(self):
        with pytest.raises(ValidationError, match="SemVer"):
            NodeSchemaBase(**_make_node(version="v1.0.0"))

    def test_invalid_version_text(self):
        with pytest.raises(ValidationError, match="SemVer"):
            NodeSchemaBase(**_make_node(version="abc"))


class TestNodeType:
    def test_valid_type(self):
        node = NodeSchemaBase(**_make_node(type="analysis"))
        assert node.type == NodeType.ANALYSIS

    def test_all_valid_types(self):
        for t in NodeType:
            node = NodeSchemaBase(**_make_node(type=t.value))
            assert node.type == t

    def test_invalid_type(self):
        with pytest.raises(ValidationError):
            NodeSchemaBase(**_make_node(type="unknown_type"))


class TestRuntimeConfig:
    def test_http_valid(self):
        node = NodeSchemaBase(**_make_node())
        assert node.runtime.type == RuntimeType.HTTP
        assert node.runtime.endpoint == "http://example.com/api"

    def test_http_missing_endpoint(self):
        with pytest.raises(ValidationError, match="endpoint"):
            NodeSchemaBase(
                **_make_node(runtime={"type": "http", "method": "POST"})
            )

    def test_http_missing_method(self):
        with pytest.raises(ValidationError, match="method"):
            NodeSchemaBase(
                **_make_node(
                    runtime={"type": "http", "endpoint": "http://example.com"}
                )
            )

    def test_grpc_no_endpoint_required(self):
        node = NodeSchemaBase(**_make_node(runtime={"type": "grpc"}))
        assert node.runtime.type == RuntimeType.GRPC


class TestInputOutputSchema:
    def test_valid_schema(self):
        node = NodeSchemaBase(**_make_node())
        assert node.input_schema["type"] == "object"

    def test_invalid_input_schema_type(self):
        with pytest.raises(ValidationError, match="object"):
            NodeSchemaBase(
                **_make_node(
                    input_schema={"type": "array", "items": {"type": "string"}}
                )
            )

    def test_invalid_output_schema_type(self):
        with pytest.raises(ValidationError, match="object"):
            NodeSchemaBase(
                **_make_node(
                    output_schema={"type": "string"}
                )
            )


class TestDefaults:
    def test_default_status(self):
        node = NodeSchemaBase(**_make_node())
        assert node.status.value == "draft"

    def test_default_visibility(self):
        node = NodeSchemaBase(**_make_node())
        assert node.visibility.value == "internal"

    def test_explicit_status(self):
        node = NodeSchemaBase(**_make_node(status="active"))
        assert node.status.value == "active"

    def test_explicit_visibility(self):
        node = NodeSchemaBase(**_make_node(visibility="public"))
        assert node.visibility.value == "public"


class TestFullSchema:
    def test_complete_valid_schema(self):
        """Test a complete node schema with all fields."""
        node = NodeSchemaBase(
            **_make_node(
                display_name="资金池检测",
                description="基于图算法检测交易数据中的可疑资金归集行为",
                tags=["finance", "risk"],
                category="风控分析",
                keywords=["资金池", "反洗钱"],
                author="张三",
                team="RiskTeam",
                namespace="finance",
                status="active",
                visibility="internal",
                timeout="30s",
            )
        )
        assert node.display_name == "资金池检测"
        assert node.tags == ["finance", "risk"]
        assert node.namespace == "finance"

    def test_missing_required_field(self):
        with pytest.raises(ValidationError):
            NodeSchemaBase(
                name="test_node",
                version="1.0.0",
                # missing type, input_schema, output_schema, runtime
            )
