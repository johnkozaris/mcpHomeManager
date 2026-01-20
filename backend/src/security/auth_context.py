"""Typed authentication context available via request.user."""

from dataclasses import dataclass
from uuid import UUID

from litestar.exceptions import PermissionDeniedException


@dataclass(frozen=True, slots=True)
class AuthContext:
    """Typed user context set by the API auth middleware.

    Available on any authenticated request as ``request.user``.
    """

    is_admin: bool
    allowed_service_ids: set[str]
    username: str
    user_id: str | None
    self_mcp_enabled: bool = False

    def can_access_service(self, service_id: UUID | None) -> bool:
        if service_id is None:
            return self.is_admin
        return self.is_admin or str(service_id) in self.allowed_service_ids

    def require_service_access(self, service_id: UUID) -> None:
        if not self.can_access_service(service_id):
            raise PermissionDeniedException("You do not have access to this service.")
