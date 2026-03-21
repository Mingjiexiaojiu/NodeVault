from enum import Enum


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


class ProbeErrorType(str, Enum):
    CONNECTION_REFUSED = "connection_refused"
    TIMEOUT = "timeout"
    DNS_ERROR = "dns_error"
    SSL_ERROR = "ssl_error"
    SPEC_NOT_FOUND = "spec_not_found"
    PARSE_ERROR = "parse_error"
