"""Tests for stable API message/error codes on user-facing surfaces."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from litestar.exceptions import ClientException, NotAuthorizedException

import entrypoints.api.setup as setup_api_module
from app import (
    _client_error_handler,
    _client_exception_handler,
    _encryption_error_handler,
    _not_found_handler,
)
from domain.exceptions import (
    EncryptionError,
    ServiceConnectionError,
    ServiceNotFoundError,
    ToolExecutionError,
    UnsupportedServiceError,
)
from entrypoints.api.admin import AdminController
from entrypoints.api.auth import AuthController, LoginRequest, ResetPasswordRequest
from entrypoints.api.message_codes import ApiMessageCode, code_fields
from entrypoints.api.schemas import CreateServiceRequest
from entrypoints.api.services import ServiceController
from entrypoints.api.setup import SetupController, SetupRequest
from security.auth_context import AuthContext


class TestAppExceptionHandlers:
    def test_domain_not_found_includes_code(self) -> None:
        response = _not_found_handler(None, ServiceNotFoundError("svc-123"))  # type: ignore[arg-type]
        assert response.status_code == 404
        assert response.content["detail"] == "Service not found: svc-123"
        assert response.content["code"] == ApiMessageCode.SERVICE_NOT_FOUND.value
        assert response.content["message_code"] == ApiMessageCode.SERVICE_NOT_FOUND.value

    @pytest.mark.parametrize(
        ("exc", "expected_code"),
        [
            (
                ServiceConnectionError("forgejo", "connection refused"),
                ApiMessageCode.SERVICE_CONNECTION_FAILED.value,
            ),
            (
                UnsupportedServiceError("unknown"),
                ApiMessageCode.SERVICE_TYPE_UNSUPPORTED.value,
            ),
            (
                ToolExecutionError("list_repos", "timeout"),
                ApiMessageCode.TOOL_EXECUTION_FAILED.value,
            ),
        ],
    )
    def test_domain_client_errors_include_codes(self, exc: Exception, expected_code: str) -> None:
        response = _client_error_handler(None, exc)  # type: ignore[arg-type]
        assert response.status_code == 400
        assert response.content["code"] == expected_code
        assert response.content["message_code"] == expected_code
        assert "detail" in response.content

    def test_encryption_error_includes_code(self) -> None:
        response = _encryption_error_handler(None, EncryptionError("bad key"))  # type: ignore[arg-type]
        assert response.status_code == 500
        assert response.content["detail"] == "Internal error"
        assert response.content["code"] == ApiMessageCode.INTERNAL_ENCRYPTION_ERROR.value

    def test_client_exception_handler_uses_explicit_code(self) -> None:
        exc = ClientException(
            detail="Invalid email address.",
            status_code=400,
            extra=code_fields(ApiMessageCode.SETUP_INVALID_EMAIL),
        )
        response = _client_exception_handler(None, exc)  # type: ignore[arg-type]
        assert response.status_code == 400
        assert response.content["detail"] == "Invalid email address."
        assert response.content["code"] == ApiMessageCode.SETUP_INVALID_EMAIL.value
        assert response.content["message_code"] == ApiMessageCode.SETUP_INVALID_EMAIL.value
        assert response.content["status_code"] == 400

    def test_client_exception_handler_uses_fallback_code(self) -> None:
        exc = NotAuthorizedException("Invalid credentials.")
        response = _client_exception_handler(None, exc)  # type: ignore[arg-type]
        assert response.status_code == 401
        assert response.content["detail"] == "Invalid credentials."
        assert response.content["code"] == ApiMessageCode.HTTP_UNAUTHORIZED.value
        assert response.content["message_code"] == ApiMessageCode.HTTP_UNAUTHORIZED.value


class TestControllerErrorCodes:
    async def test_auth_login_invalid_credentials_code(self) -> None:
        user_service = SimpleNamespace(authenticate_by_password=AsyncMock(return_value=None))
        with pytest.raises(NotAuthorizedException) as exc_info:
            await AuthController.login.fn(
                SimpleNamespace(),
                db_session=AsyncMock(),
                data=LoginRequest(username="admin", password="wrong"),
                user_service=user_service,
            )
        assert exc_info.value.extra == code_fields(ApiMessageCode.AUTH_INVALID_CREDENTIALS)

    async def test_auth_reset_password_too_short_code(self) -> None:
        with pytest.raises(ClientException) as exc_info:
            await AuthController.reset_password.fn(
                SimpleNamespace(),
                db_session=AsyncMock(),
                data=ResetPasswordRequest(token="abc", password="short"),
                user_service=MagicMock(),
            )
        assert exc_info.value.extra == code_fields(ApiMessageCode.AUTH_PASSWORD_TOO_SHORT)

    async def test_setup_already_completed_code(self, monkeypatch: pytest.MonkeyPatch) -> None:
        class ExistingUsersRepo:
            def __init__(self, _db_session) -> None: ...

            async def get_count(self) -> int:
                return 1

        monkeypatch.setattr(setup_api_module, "UserRepository", ExistingUsersRepo)

        with pytest.raises(ClientException) as exc_info:
            await SetupController.setup.fn(
                SimpleNamespace(),
                db_session=AsyncMock(),
                data=SetupRequest(
                    username="admin",
                    password="securepass123",
                    email="admin@example.com",
                ),
                user_service=MagicMock(),
            )
        assert exc_info.value.status_code == 409
        assert exc_info.value.extra == code_fields(ApiMessageCode.SETUP_ALREADY_COMPLETED)

    async def test_service_create_admin_required_code(self) -> None:
        request = SimpleNamespace(
            user=AuthContext(
                is_admin=False,
                allowed_service_ids=set(),
                username="viewer",
                user_id=None,
            )
        )
        with pytest.raises(ClientException) as exc_info:
            await ServiceController.create_service.fn(
                SimpleNamespace(),
                request=request,
                db_session=AsyncMock(),
                service_manager=MagicMock(),
                tool_registry=MagicMock(),
                data=CreateServiceRequest(
                    name="forgejo",
                    display_name="Forgejo",
                    service_type="forgejo",
                    base_url="http://forgejo.local",
                    api_token="token",
                    config={},
                ),
            )
        assert exc_info.value.status_code == 403
        assert exc_info.value.extra == code_fields(ApiMessageCode.SERVICES_ADMIN_REQUIRED_CREATE)

    async def test_admin_smtp_test_requires_user_id_code(self) -> None:
        request = SimpleNamespace(
            user=AuthContext(
                is_admin=True,
                allowed_service_ids=set(),
                username="admin",
                user_id=None,
            )
        )
        with pytest.raises(ClientException) as exc_info:
            await AdminController.test_smtp.fn(
                SimpleNamespace(),
                request=request,
                db_session=AsyncMock(),
                state=SimpleNamespace(encryption=MagicMock()),
            )
        assert exc_info.value.extra == code_fields(ApiMessageCode.ADMIN_SMTP_TEST_USER_REQUIRED)

    async def test_service_connection_test_sets_message_code(self) -> None:
        service_id = uuid4()
        request = SimpleNamespace(
            user=AuthContext(
                is_admin=True,
                allowed_service_ids=set(),
                username="admin",
                user_id=None,
            )
        )
        service_manager = SimpleNamespace(
            test_connection=AsyncMock(return_value=(False, "Connection failed"))
        )
        db_session = AsyncMock()
        tool_registry = SimpleNamespace(refresh=AsyncMock())

        result = await ServiceController.test_connection.fn(
            SimpleNamespace(),
            request=request,
            db_session=db_session,
            service_manager=service_manager,
            tool_registry=tool_registry,
            service_id=service_id,
        )

        assert result.success is False
        assert result.message == "Connection failed"
        assert result.message_code == ApiMessageCode.SERVICES_CONNECTION_TEST_FAILED.value
        tool_registry.refresh.assert_not_called()
