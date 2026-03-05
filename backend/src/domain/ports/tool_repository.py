from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ToolOverride:
    is_enabled: bool = True
    description_override: str | None = None
    parameters_schema_override: dict[str, Any] | None = None
    http_method_override: str | None = None
    path_template_override: str | None = None


class IToolPermissionRepository(ABC):
    @abstractmethod
    async def get_by_service_id(self, service_id: UUID) -> dict[str, ToolOverride]: ...

    @abstractmethod
    async def set_permission(
        self,
        service_id: UUID,
        tool_name: str,
        is_enabled: bool,
        description_override: str | None = None,
        parameters_schema_override: dict[str, Any] | None = None,
        http_method_override: str | None = None,
        path_template_override: str | None = None,
    ) -> None: ...
