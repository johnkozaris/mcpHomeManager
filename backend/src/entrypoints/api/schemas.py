from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

import msgspec

# --- Service schemas ---


class CreateServiceRequest(msgspec.Struct):
    name: Annotated[str, msgspec.Meta(max_length=100)]
    display_name: Annotated[str, msgspec.Meta(max_length=200)]
    service_type: str
    base_url: Annotated[str, msgspec.Meta(max_length=500)]
    api_token: str
    config: dict[str, Any] = {}


class UpdateServiceRequest(msgspec.Struct):
    display_name: str | None = None
    base_url: str | None = None
    api_token: str | None = None
    is_enabled: bool | None = None
    config: dict[str, Any] | None = None


class ServiceResponse(msgspec.Struct):
    id: UUID
    name: str
    display_name: str
    service_type: str
    base_url: str
    is_enabled: bool
    health_status: str
    last_health_check: datetime | None
    tool_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None


# --- Tool schemas ---


class ToolResponse(msgspec.Struct):
    name: str
    service_type: str
    service_id: UUID | None
    service_name: str | None
    description: str
    parameters_schema: dict[str, Any]
    is_enabled: bool
    description_override: str | None = None
    parameters_schema_override: dict[str, Any] | None = None
    http_method: str | None = None
    path_template: str | None = None
    http_method_override: str | None = None
    path_template_override: str | None = None
    is_user_defined: bool = False


class UpdateToolPermission(msgspec.Struct):
    is_enabled: bool
    description_override: str | None = None
    parameters_schema_override: dict[str, Any] | None = None
    http_method_override: str | None = None
    path_template_override: str | None = None


class ServiceDetailResponse(msgspec.Struct):
    id: UUID
    name: str
    display_name: str
    service_type: str
    base_url: str
    is_enabled: bool
    health_status: str
    last_health_check: datetime | None
    config: dict[str, Any]
    tool_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None
    tools: list[ToolResponse] = []


class TestResult(msgspec.Struct):
    success: bool
    message: str
    message_code: str | None = None


# --- Audit schemas ---


class AuditEntryResponse(msgspec.Struct):
    id: UUID
    service_name: str
    tool_name: str
    input_summary: str
    status: str
    duration_ms: int
    error_message: str | None = None
    client_name: str | None = None
    created_at: datetime | None = None


class AuditListResponse(msgspec.Struct):
    items: list[AuditEntryResponse]
    total: int


# --- Import/Export ---


class ImportRequest(msgspec.Struct):
    yaml_content: str
    token_map: dict[str, str] = {}


class ImportResult(msgspec.Struct):
    created: list[str] = []
    skipped: list[str] = []
    errors: list[str] = []


# --- Permission Profiles ---


class ProfileResponse(msgspec.Struct):
    name: str
    label: str
    description: str
    tool_states: dict[str, bool]


class ApplyProfileRequest(msgspec.Struct):
    profile_name: str


class ApplyProfileResponse(msgspec.Struct):
    status: str
    profile: str
    message_code: str | None = None


# --- Health ---


class HealthResponse(msgspec.Struct):
    status: str
    database: str
    mcp_server: str
    services_healthy: int
    services_total: int


class ConfigResponse(msgspec.Struct):
    setup_required: bool
    smtp_enabled: bool
    mcp_server_name: str
    self_mcp_enabled: bool = True
    app_name: str = "MCP Manager"


# --- Users ---


class CreateUserRequest(msgspec.Struct):
    username: Annotated[str, msgspec.Meta(max_length=100)]
    password: Annotated[str, msgspec.Meta(min_length=8, max_length=200)]
    email: str | None = None
    is_admin: bool = False
    self_mcp_enabled: bool = False
    allowed_service_ids: list[str] = []


class UpdateUserRequest(msgspec.Struct):
    is_admin: bool | None = None
    allowed_service_ids: list[str] | None = None
    self_mcp_enabled: bool | None = None


class UserResponse(msgspec.Struct):
    id: UUID
    username: str
    email: str | None
    is_admin: bool
    self_mcp_enabled: bool
    allowed_service_ids: list[str]
    created_at: datetime | None = None


# --- Generic REST tools ---


class CreateGenericToolRequest(msgspec.Struct):
    tool_name: Annotated[str, msgspec.Meta(max_length=200, pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$")]
    http_method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
    path_template: Annotated[str, msgspec.Meta(max_length=500)]
    description: str = ""
    params_schema: dict[str, Any] = {}


class GenericToolResult(msgspec.Struct):
    status: str
    tool_name: str
    tools_count: int
    message_code: str | None = None


class UpdateGenericToolRequest(msgspec.Struct):
    description: str | None = None
    http_method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"] | None = None
    path_template: Annotated[str, msgspec.Meta(max_length=500)] | None = None
    params_schema: dict[str, Any] | None = None


class ImportOpenAPIRequest(msgspec.Struct):
    spec: str


class ImportOpenAPIResult(msgspec.Struct):
    status: str
    imported: list[str]
    tools_count: int
    skipped: list[str] = []
    message_code: str | None = None


# --- MCP Apps ---


class AppResponse(msgspec.Struct):
    name: str
    service_type: str
    service_name: str
    title: str
    description: str
    parameters_schema: dict[str, Any] = {}


class AppActionRequest(msgspec.Struct):
    action: str
    payload: dict[str, Any] = {}
