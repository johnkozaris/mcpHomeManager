from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass
class GenericToolRow:
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
        """Returns True if deleted, False if not found."""
        ...

    @abstractmethod
    async def get_by_name(self, service_id: UUID, tool_name: str) -> GenericToolRow | None:
        """Returns None if not found."""
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
        """Returns None if not found."""
        ...
