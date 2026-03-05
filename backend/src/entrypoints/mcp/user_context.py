"""Per-request user context for MCP tool authorization (contextvars-safe)."""

import contextvars
from uuid import UUID

from domain.entities.user import User

current_user_var: contextvars.ContextVar[User | None] = contextvars.ContextVar(
    "current_user_var",
    default=None,
)


def can_user_access_service(user: User, service_id: UUID | None) -> bool:
    """Check whether the user can access a service by ID."""
    if user.is_admin:
        return True
    if service_id is None:
        return False
    return service_id in user.allowed_service_ids


async def filter_services_for_user(
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
