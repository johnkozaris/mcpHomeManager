import json
import time
from collections.abc import Set
from datetime import datetime
from typing import Any

from domain.entities.audit_entry import AuditEntry, CallStatus
from domain.ports.audit_repository import IAuditRepository


class AuditService:
    """Records and queries MCP tool call audit entries."""

    def __init__(self, repository: IAuditRepository) -> None:
        self._repo = repository

    async def record_success(
        self,
        service_name: str,
        tool_name: str,
        arguments: dict,
        start_time: float,
        *,
        client_name: str | None = None,
    ) -> AuditEntry:
        duration_ms = int((time.monotonic() - start_time) * 1000)
        entry = AuditEntry(
            service_name=service_name,
            tool_name=tool_name,
            input_summary=self._summarize(arguments),
            status=CallStatus.SUCCESS,
            duration_ms=duration_ms,
            client_name=client_name,
        )
        return await self._repo.record(entry)

    async def record_error(
        self,
        service_name: str,
        tool_name: str,
        arguments: dict,
        start_time: float,
        error: Exception,
        *,
        client_name: str | None = None,
    ) -> AuditEntry:
        duration_ms = int((time.monotonic() - start_time) * 1000)
        entry = AuditEntry(
            service_name=service_name,
            tool_name=tool_name,
            input_summary=self._summarize(arguments),
            status=CallStatus.ERROR,
            duration_ms=duration_ms,
            error_message=str(error)[:500],
            client_name=client_name,
        )
        return await self._repo.record(entry)

    async def get_recent(
        self,
        limit: int = 50,
        offset: int = 0,
        service_name: str | None = None,
        tool_name: str | None = None,
        status: str | None = None,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
        allowed_service_names: Set[str] | None = None,
    ) -> list[AuditEntry]:
        return await self._repo.get_recent(
            limit=limit,
            offset=offset,
            service_name=service_name,
            tool_name=tool_name,
            status=status,
            created_after=created_after,
            created_before=created_before,
            allowed_service_names=allowed_service_names,
        )

    async def count(
        self,
        service_name: str | None = None,
        tool_name: str | None = None,
        status: str | None = None,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
        allowed_service_names: Set[str] | None = None,
    ) -> int:
        return await self._repo.count(
            service_name=service_name,
            tool_name=tool_name,
            status=status,
            created_after=created_after,
            created_before=created_before,
            allowed_service_names=allowed_service_names,
        )

    _SENSITIVE_KEYS = frozenset(
        {
            "password",
            "token",
            "secret",
            "api_key",
            "apikey",
            "api_token",
            "authorization",
            "credential",
            "private_key",
            "access_token",
            "refresh_token",
            "ssn",
            "credit_card",
        }
    )

    @staticmethod
    def _summarize(arguments: dict, max_len: int = 500) -> str:
        redacted = AuditService._redact(arguments)
        text = json.dumps(redacted, default=str)
        return text[:max_len] if len(text) > max_len else text

    @staticmethod
    def _redact(obj: dict[str, Any]) -> dict[str, Any]:
        """Recursively redact values for keys that look sensitive."""
        result: dict[str, Any] = {}
        for key, value in obj.items():
            if key.lower() in AuditService._SENSITIVE_KEYS:
                result[key] = "***REDACTED***"
            elif isinstance(value, dict):
                result[key] = AuditService._redact(value)
            else:
                result[key] = value
        return result
