from enum import Enum


class NodeType(str, Enum):
    DATA_CLEANING = "data_cleaning"
    ANALYSIS = "analysis"
    RISK = "risk"
    NLP = "nlp"
    VISION = "vision"
    ML = "ml"
    TOOL = "tool"
    UTILITY = "utility"


class RuntimeType(str, Enum):
    HTTP = "http"
    GRPC = "grpc"
    DOCKER = "docker"
    PYTHON = "python"
    MCP = "mcp"


class NodeStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class NodeVisibility(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    PRIVATE = "private"


class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
