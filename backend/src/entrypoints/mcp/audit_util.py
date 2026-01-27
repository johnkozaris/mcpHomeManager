"""Shared audit recording utility for MCP tool calls."""

import time
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from infrastructure import metrics as prom_metrics
from infrastructure.persistence.audit_repository import AuditRepository
from services.audit_service import AuditService

logger = structlog.get_logger()


async def record_audit_safe(
    session_factory: async_sessionmaker[AsyncSession] | Any,
    svc_name: str,
    tool_name: str,
    kwargs: dict,
    start: float,
    *,
    error: Exception | None = None,
    client_name: str | None = None,
) -> None:
    """Record audit entry and prometheus metrics. Never raises — logs failures instead."""
    duration_s = time.monotonic() - start
    status = "error" if error else "success"
    prom_metrics.record_tool_call(tool_name, svc_name, status, duration_s)

    try:
        async with session_factory() as session:
            audit = AuditService(repository=AuditRepository(session))
            if error:
                await audit.record_error(
                    svc_name,
                    tool_name,
                    kwargs,
                    start,
                    error,
                    client_name=client_name,
                )
            else:
                await audit.record_success(
                    svc_name,
                    tool_name,
                    kwargs,
                    start,
                    client_name=client_name,
                )
            await session.commit()
    except Exception:
        logger.exception("Failed to record audit for %s", tool_name)
