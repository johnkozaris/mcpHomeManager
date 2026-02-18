"""Port interface for generic tool definition persistence."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass
class GenericToolRow:
    """Lightweight row representation of a generic tool definition."""

    tool_name: str
    description: str
    http_method: str
    path_template: str
    params_schema: dict[str, Any]


class IGenericToolRepository(ABC):
    @abstractmethod
    async def get_by_service_id(self, service_id: UUID) -> list[GenericToolRow]: ...

    @abstractmethod
    async def create(
        self,
        service_id: UUID,
        tool_name: str,
        description: str,
        http_method: str,
        path_template: str,
        params_schema: dict[str, Any],
    ) -> GenericToolRow: ...

    @abstractmethod
    async def delete(self, service_id: UUID, tool_name: str) -> bool:
        """Delete a tool by service_id and name. Returns True if deleted."""
        ...

    @abstractmethod
    async def get_by_name(self, service_id: UUID, tool_name: str) -> GenericToolRow | None:
        """Get a single tool by service_id and tool_name. Returns None if not found."""
        ...

    @abstractmethod
    async def update(
        self,
        service_id: UUID,
        tool_name: str,
        *,
        description: str | None = None,
        http_method: str | None = None,
        path_template: str | None = None,
        params_schema: dict[str, Any] | None = None,
    ) -> GenericToolRow | None:
        """Update a tool's fields. Returns None if not found."""
        ...
