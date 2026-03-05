from collections.abc import Set
from datetime import datetime
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from domain.entities.audit_entry import AuditEntry, CallStatus
from domain.ports.audit_repository import IAuditRepository
from infrastructure.persistence.orm_models import AuditLogModel


def _escape_like(value: str) -> str:
    """Escape SQL LIKE/ILIKE metacharacters."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class AuditRepository(IAuditRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(self, entry: AuditEntry) -> AuditEntry:
        model = AuditLogModel(
            service_name=entry.service_name,
            tool_name=entry.tool_name,
            input_summary=entry.input_summary,
            status=entry.status.value,
            duration_ms=entry.duration_ms,
            error_message=entry.error_message,
            client_name=entry.client_name,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    @staticmethod
    def _apply_filters(
        stmt: Select[Any],
        service_name: str | None = None,
        tool_name: str | None = None,
        status: str | None = None,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
        allowed_service_names: Set[str] | None = None,
    ) -> Select[Any]:
        if service_name:
            stmt = stmt.where(AuditLogModel.service_name == service_name)
        if allowed_service_names is not None:
            stmt = stmt.where(AuditLogModel.service_name.in_(allowed_service_names))
        if tool_name:
            stmt = stmt.where(AuditLogModel.tool_name.ilike(f"%{_escape_like(tool_name)}%"))
        if status:
            stmt = stmt.where(AuditLogModel.status == status)
        if created_after:
            stmt = stmt.where(AuditLogModel.created_at >= created_after)
        if created_before:
            stmt = stmt.where(AuditLogModel.created_at <= created_before)
        return stmt

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
        stmt = select(AuditLogModel).order_by(AuditLogModel.created_at.desc())
        stmt = self._apply_filters(
            stmt,
            service_name,
            tool_name,
            status,
            created_after,
            created_before,
            allowed_service_names,
        )
        stmt = stmt.offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return [self._to_entity(row) for row in result.scalars().all()]

    async def count(
        self,
        service_name: str | None = None,
        tool_name: str | None = None,
        status: str | None = None,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
        allowed_service_names: Set[str] | None = None,
    ) -> int:
        stmt = select(func.count(AuditLogModel.id))
        stmt = self._apply_filters(
            stmt,
            service_name,
            tool_name,
            status,
            created_after,
            created_before,
            allowed_service_names,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def delete_older_than(self, cutoff: datetime) -> int:
        result = await self._session.execute(
            delete(AuditLogModel).where(AuditLogModel.created_at < cutoff)
        )
        rowcount = getattr(result, "rowcount", None)
        return rowcount if isinstance(rowcount, int) else 0

    @staticmethod
    def _to_entity(model: AuditLogModel) -> AuditEntry:
        return AuditEntry(
            id=model.id,
            service_name=model.service_name,
            tool_name=model.tool_name,
            input_summary=model.input_summary,
            status=CallStatus(model.status),
            duration_ms=model.duration_ms,
            error_message=model.error_message,
            client_name=model.client_name,
            created_at=model.created_at,
        )
