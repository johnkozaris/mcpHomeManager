"""Per-request user context for MCP tool authorization (contextvars-safe)."""

import contextvars
from collections.abc import Callable
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from domain.entities.user import User

# Per-request user context — safe across concurrent async tasks
current_user_var: contextvars.ContextVar[User | None] = contextvars.ContextVar(
    "current_user_var",
    default=None,
)


async def check_user_service_access(
    session_factory: async_sessionmaker[AsyncSession],
    user: User,
    service_name: str,
) -> bool:
    """Check if a non-admin user has access to a given service by name."""
    from infrastructure.persistence.service_repository import ServiceRepository

    async with session_factory() as session:
        repo = ServiceRepository(session)
        svc = await repo.get_by_name(service_name)
        if svc is None or svc.id is None:
            return False
        return svc.id in user.allowed_service_ids


async def filter_services_for_user(
    session_factory: async_sessionmaker[AsyncSession] | Callable[[], Any] | None,
    services: list,
    *,
    id_attr: str = "id",
) -> list:
    """Filter a list of service entities to only those the current user can access.

    Returns the full list if user is admin, empty list if no user.
    """
    user = current_user_var.get()
    if user is None:
        return []
    if user.is_admin:
        return services

    return [s for s in services if getattr(s, id_attr) in user.allowed_service_ids]
