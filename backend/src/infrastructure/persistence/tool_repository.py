from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.ports.tool_repository import IToolPermissionRepository, ToolOverride
from infrastructure.persistence.orm_models import ToolPermissionModel


class ToolPermissionRepository(IToolPermissionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_service_id(self, service_id: UUID) -> dict[str, ToolOverride]:
        result = await self._session.execute(
            select(ToolPermissionModel).where(ToolPermissionModel.service_id == service_id)
        )
        return {
            row.tool_name: ToolOverride(
                is_enabled=row.is_enabled,
                description_override=row.description_override,
                parameters_schema_override=row.parameters_schema_override,
            )
            for row in result.scalars().all()
        }

    async def set_permission(
        self,
        service_id: UUID,
        tool_name: str,
        is_enabled: bool,
        description_override: str | None = None,
        parameters_schema_override: dict[str, Any] | None = None,
    ) -> None:
        result = await self._session.execute(
            select(ToolPermissionModel).where(
                ToolPermissionModel.service_id == service_id,
                ToolPermissionModel.tool_name == tool_name,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.is_enabled = is_enabled
            existing.description_override = description_override
            existing.parameters_schema_override = parameters_schema_override
        else:
            self._session.add(
                ToolPermissionModel(
                    service_id=service_id,
                    tool_name=tool_name,
                    is_enabled=is_enabled,
                    description_override=description_override,
                    parameters_schema_override=parameters_schema_override,
                )
            )
        await self._session.flush()
