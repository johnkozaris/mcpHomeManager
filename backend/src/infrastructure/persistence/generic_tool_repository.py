from typing import Any
from uuid import UUID

from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from domain.ports.generic_tool_repository import GenericToolRow, IGenericToolRepository
from infrastructure.persistence.orm_models import GenericToolDefinitionModel


class GenericToolDefinitionRepository(IGenericToolRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_service_id(self, service_id: UUID) -> list[GenericToolRow]:
        result = await self._session.execute(
            select(GenericToolDefinitionModel)
            .where(GenericToolDefinitionModel.service_id == service_id)
            .order_by(GenericToolDefinitionModel.tool_name)
        )
        return [
            GenericToolRow(
                tool_name=row.tool_name,
                description=row.description,
                http_method=row.http_method,
                path_template=row.path_template,
                params_schema=row.params_schema or {},
            )
            for row in result.scalars().all()
        ]

    async def get_by_name(self, service_id: UUID, tool_name: str) -> GenericToolRow | None:
        result = await self._session.execute(
            select(GenericToolDefinitionModel).where(
                GenericToolDefinitionModel.service_id == service_id,
                GenericToolDefinitionModel.tool_name == tool_name,
            )
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return GenericToolRow(
            tool_name=model.tool_name,
            description=model.description,
            http_method=model.http_method,
            path_template=model.path_template,
            params_schema=model.params_schema or {},
        )

    async def create(
        self,
        service_id: UUID,
        tool_name: str,
        description: str,
        http_method: str,
        path_template: str,
        params_schema: dict[str, Any],
    ) -> GenericToolRow:
        model = GenericToolDefinitionModel(
            service_id=service_id,
            tool_name=tool_name,
            description=description,
            http_method=http_method.upper(),
            path_template=path_template,
            params_schema=params_schema,
        )
        self._session.add(model)
        await self._session.flush()
        return GenericToolRow(
            tool_name=model.tool_name,
            description=model.description,
            http_method=model.http_method,
            path_template=model.path_template,
            params_schema=model.params_schema or {},
        )

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
        result = await self._session.execute(
            select(GenericToolDefinitionModel).where(
                GenericToolDefinitionModel.service_id == service_id,
                GenericToolDefinitionModel.tool_name == tool_name,
            )
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None

        if description is not None:
            model.description = description
        if http_method is not None:
            model.http_method = http_method.upper()
        if path_template is not None:
            model.path_template = path_template
        if params_schema is not None:
            model.params_schema = params_schema

        await self._session.flush()
        return GenericToolRow(
            tool_name=model.tool_name,
            description=model.description,
            http_method=model.http_method,
            path_template=model.path_template,
            params_schema=model.params_schema or {},
        )

    async def delete(self, service_id: UUID, tool_name: str) -> bool:
        result = await self._session.execute(
            sa_delete(GenericToolDefinitionModel).where(
                GenericToolDefinitionModel.service_id == service_id,
                GenericToolDefinitionModel.tool_name == tool_name,
            )
        )
        cursor_result = result if isinstance(result, CursorResult) else None
        return (cursor_result.rowcount if cursor_result is not None else 0) > 0
