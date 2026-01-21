from abc import ABC, abstractmethod
from collections.abc import Set
from datetime import datetime

from domain.entities.audit_entry import AuditEntry


class IAuditRepository(ABC):
    @abstractmethod
    async def record(self, entry: AuditEntry) -> AuditEntry: ...

    @abstractmethod
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
    ) -> list[AuditEntry]: ...

    @abstractmethod
    async def count(
        self,
        service_name: str | None = None,
        tool_name: str | None = None,
        status: str | None = None,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
        allowed_service_names: Set[str] | None = None,
    ) -> int: ...

    @abstractmethod
    async def delete_older_than(self, cutoff: datetime) -> int:
        """Delete entries older than cutoff. Returns number of rows deleted."""
        ...
