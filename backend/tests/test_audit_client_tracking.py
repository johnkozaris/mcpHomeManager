"""Tests for audit client tracking."""

import time
from collections.abc import Set
from datetime import UTC, datetime

from domain.entities.audit_entry import AuditEntry, CallStatus
from domain.ports.audit_repository import IAuditRepository
from services.audit_service import AuditService


class FakeAuditRepository(IAuditRepository):
    """In-memory audit repository for testing."""

    def __init__(self) -> None:
        self.entries: list[AuditEntry] = []

    async def record(self, entry: AuditEntry) -> AuditEntry:
        self.entries.append(entry)
        return entry

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
        filtered = self.entries
        if service_name:
            filtered = [e for e in filtered if e.service_name == service_name]
        if allowed_service_names is not None:
            filtered = [e for e in filtered if e.service_name in allowed_service_names]
        if tool_name:
            filtered = [e for e in filtered if tool_name.lower() in e.tool_name.lower()]
        if status:
            filtered = [e for e in filtered if e.status.value == status]
        return filtered[offset : offset + limit]

    async def count(
        self,
        service_name: str | None = None,
        tool_name: str | None = None,
        status: str | None = None,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
        allowed_service_names: Set[str] | None = None,
    ) -> int:
        filtered = self.entries
        if service_name:
            filtered = [e for e in filtered if e.service_name == service_name]
        if allowed_service_names is not None:
            filtered = [e for e in filtered if e.service_name in allowed_service_names]
        if tool_name:
            filtered = [e for e in filtered if tool_name.lower() in e.tool_name.lower()]
        if status:
            filtered = [e for e in filtered if e.status.value == status]
        return len(filtered)

    async def delete_older_than(self, cutoff: datetime) -> int:
        before = len(self.entries)
        self.entries = [
            entry
            for entry in self.entries
            if entry.created_at is None or entry.created_at >= cutoff.replace(tzinfo=UTC)
        ]
        return before - len(self.entries)


class TestAuditClientTracking:
    async def test_record_success_with_client_name(self) -> None:
        repo = FakeAuditRepository()
        service = AuditService(repository=repo)
        start = time.monotonic()
        entry = await service.record_success(
            "forgejo",
            "list_repos",
            {},
            start,
            client_name="claude-desktop",
        )
        assert entry.client_name == "claude-desktop"
        assert entry.status == CallStatus.SUCCESS

    async def test_record_error_with_client_name(self) -> None:
        repo = FakeAuditRepository()
        service = AuditService(repository=repo)
        start = time.monotonic()
        entry = await service.record_error(
            "forgejo",
            "list_repos",
            {},
            start,
            RuntimeError("fail"),
            client_name="cursor",
        )
        assert entry.client_name == "cursor"
        assert entry.status == CallStatus.ERROR
        assert entry.error_message == "fail"

    async def test_record_success_without_client_name(self) -> None:
        repo = FakeAuditRepository()
        service = AuditService(repository=repo)
        start = time.monotonic()
        entry = await service.record_success("forgejo", "list_repos", {}, start)
        assert entry.client_name is None

    async def test_audit_entry_has_client_name_field(self) -> None:
        entry = AuditEntry(
            service_name="test",
            tool_name="tool",
            input_summary="{}",
            status=CallStatus.SUCCESS,
            duration_ms=10,
            client_name="test-client",
        )
        assert entry.client_name == "test-client"
