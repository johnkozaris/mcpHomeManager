"""Tests for domain exceptions."""

from domain.exceptions import (
    DomainError,
    EncryptionError,
    ServiceConnectionError,
    ServiceNotFoundError,
    ToolExecutionError,
    UnsupportedServiceError,
)


class TestExceptions:
    def test_service_not_found(self) -> None:
        exc = ServiceNotFoundError("abc-123")
        assert "abc-123" in str(exc)
        assert exc.identifier == "abc-123"
        assert isinstance(exc, DomainError)

    def test_service_connection_error(self) -> None:
        exc = ServiceConnectionError("forgejo", "Connection refused")
        assert "forgejo" in str(exc)
        assert "Connection refused" in str(exc)
        assert exc.service_name == "forgejo"
        assert exc.reason == "Connection refused"

    def test_unsupported_service(self) -> None:
        exc = UnsupportedServiceError("unknown_type")
        assert "unknown_type" in str(exc)
        assert exc.service_type == "unknown_type"

    def test_encryption_error(self) -> None:
        exc = EncryptionError("bad key")
        assert "bad key" in str(exc)
        assert isinstance(exc, DomainError)

    def test_tool_execution_error(self) -> None:
        exc = ToolExecutionError("list_repos", "timeout")
        assert "list_repos" in str(exc)
        assert "timeout" in str(exc)
        assert exc.tool_name == "list_repos"
        assert exc.reason == "timeout"
