"""Application service for tool permission and override updates."""

from uuid import UUID

from domain.ports.tool_repository import IToolPermissionRepository
from domain.validation import validate_tool_name


class ToolPermissionService:
    """Owns validation + persistence for tool permission updates."""

    def __init__(self, repository: IToolPermissionRepository) -> None:
        self._repo = repository

    async def set_permission(
        self,
        service_id: UUID,
        *,
        tool_name: str,
        is_enabled: bool,
        description_override: str | None = None,
        parameters_schema_override: dict | None = None,
        http_method_override: str | None = None,
        path_template_override: str | None = None,
    ) -> None:
        validated_name = validate_tool_name(tool_name)
        await self._repo.set_permission(
            service_id=service_id,
            tool_name=validated_name,
            is_enabled=is_enabled,
            description_override=description_override,
            parameters_schema_override=parameters_schema_override,
            http_method_override=http_method_override,
            path_template_override=path_template_override,
        )
