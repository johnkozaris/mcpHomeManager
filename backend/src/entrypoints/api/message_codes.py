# ruff: noqa: S105

"""Stable API message codes for user-facing responses."""

from enum import StrEnum
from typing import Any


class ApiMessageCode(StrEnum):
    # Generic HTTP fallback codes
    HTTP_BAD_REQUEST = "http.bad_request"
    HTTP_UNAUTHORIZED = "http.unauthorized"
    HTTP_FORBIDDEN = "http.forbidden"
    HTTP_NOT_FOUND = "http.not_found"
    HTTP_CONFLICT = "http.conflict"
    HTTP_UNPROCESSABLE_ENTITY = "http.unprocessable_entity"
    HTTP_CLIENT_ERROR = "http.client_error"

    # Domain error handlers
    SERVICE_NOT_FOUND = "service.not_found"
    SERVICE_CONNECTION_FAILED = "service.connection_failed"
    SERVICE_TYPE_UNSUPPORTED = "service.type_unsupported"
    TOOL_EXECUTION_FAILED = "tool.execution_failed"
    INTERNAL_ENCRYPTION_ERROR = "internal.encryption_error"

    # Auth
    AUTH_INVALID_CREDENTIALS = "auth.invalid_credentials"
    AUTH_API_KEY_USER_REQUIRED = "auth.api_key.user_required"
    AUTH_API_KEY_OPERATION_FORBIDDEN = "auth.api_key.operation_forbidden"
    AUTH_API_KEY_NOT_FOUND = "auth.api_key.not_found"
    AUTH_PASSWORD_TOO_SHORT = "auth.password.too_short"
    AUTH_RESET_TOKEN_INVALID = "auth.reset_token.invalid_or_expired"
    AUTH_RESET_TOKEN_EXPIRED = "auth.reset_token.expired"
    AUTH_RESET_REQUEST_ACCEPTED = "auth.reset.request_accepted"
    AUTH_PASSWORD_RESET_COMPLETED = "auth.password.reset_completed"

    # Setup
    SETUP_ALREADY_COMPLETED = "setup.already_completed"
    SETUP_INVALID_EMAIL = "setup.email.invalid"

    # Services
    SERVICES_ADMIN_REQUIRED_CREATE = "services.create.admin_required"
    SERVICES_ADMIN_REQUIRED_IMPORT = "services.import.admin_required"
    SERVICES_VALIDATION_ERROR = "services.validation_error"
    SERVICES_PROFILE_NOT_FOUND = "services.profile.not_found"
    SERVICES_GENERIC_TOOL_CONFLICT = "services.generic_tool.conflict"
    SERVICES_GENERIC_TOOL_VALIDATION_ERROR = "services.generic_tool.validation_error"
    SERVICES_GENERIC_TOOL_NOT_FOUND = "services.generic_tool.not_found"
    SERVICES_CONNECTION_TEST_SUCCESS = "services.connection_test.success"
    SERVICES_CONNECTION_TEST_FAILED = "services.connection_test.failed"
    SERVICES_GENERIC_TOOL_TEST_URL_VALIDATION_FAILED = (
        "services.generic_tool_test.url_validation_failed"
    )
    SERVICES_GENERIC_TOOL_TEST_SUCCESS = "services.generic_tool_test.success"
    SERVICES_GENERIC_TOOL_TEST_SERVER_ERROR = "services.generic_tool_test.server_error"
    SERVICES_GENERIC_TOOL_TEST_CONNECTION_FAILED = "services.generic_tool_test.connection_failed"
    SERVICES_GENERIC_TOOL_TEST_ERROR = "services.generic_tool_test.error"
    SERVICES_GENERIC_TOOL_CREATED = "services.generic_tool.created"
    SERVICES_GENERIC_TOOL_UPDATED = "services.generic_tool.updated"
    SERVICES_OPENAPI_IMPORT_INVALID = "services.openapi_import.invalid"
    SERVICES_OPENAPI_IMPORTED = "services.openapi_import.imported"
    SERVICES_PROFILE_APPLIED = "services.profile.applied"

    # Admin
    ADMIN_ENCRYPTION_KEY_INVALID = "admin.encryption_key.invalid"
    ADMIN_SMTP_TEST_USER_REQUIRED = "admin.smtp_test.user_required"
    ADMIN_SMTP_TEST_EMAIL_REQUIRED = "admin.smtp_test.email_required"
    ADMIN_SMTP_NOT_CONFIGURED = "admin.smtp.not_configured"
    ADMIN_SMTP_TEST_SUCCESS = "admin.smtp_test.success"
    ADMIN_SMTP_TEST_FAILED = "admin.smtp_test.failed"


def code_fields(code: str | ApiMessageCode) -> dict[str, str]:
    value = str(code)
    return {"code": value, "message_code": value}


def exception_extra(code: str | ApiMessageCode) -> dict[str, str]:
    return code_fields(code)


def extract_message_code(extra: dict[str, Any] | list[Any] | None) -> str | None:
    if not isinstance(extra, dict):
        return None
    message_code = extra.get("message_code")
    if isinstance(message_code, str):
        return message_code
    code = extra.get("code")
    if isinstance(code, str):
        return code
    return None


def default_client_error_code(status_code: int) -> ApiMessageCode:
    match status_code:
        case 400:
            return ApiMessageCode.HTTP_BAD_REQUEST
        case 401:
            return ApiMessageCode.HTTP_UNAUTHORIZED
        case 403:
            return ApiMessageCode.HTTP_FORBIDDEN
        case 404:
            return ApiMessageCode.HTTP_NOT_FOUND
        case 409:
            return ApiMessageCode.HTTP_CONFLICT
        case 422:
            return ApiMessageCode.HTTP_UNPROCESSABLE_ENTITY
        case _:
            return ApiMessageCode.HTTP_CLIENT_ERROR


def error_response_content(
    *,
    detail: str,
    code: str | ApiMessageCode,
    status_code: int | None = None,
    extra: dict[str, Any] | list[Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"detail": detail, **code_fields(code)}
    if status_code is not None:
        payload["status_code"] = status_code
    if extra is not None:
        payload["extra"] = extra
    return payload
