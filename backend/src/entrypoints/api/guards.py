"""API route guards.

Authentication is handled by :class:`ApiAuthMiddleware` which sets
``request.user`` to an :class:`AuthContext`. Guards here only perform
authorization checks on the already-authenticated user.
"""

from litestar.connection import ASGIConnection
from litestar.exceptions import PermissionDeniedException
from litestar.handlers import BaseRouteHandler

from security.auth_context import AuthContext


def require_admin(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    """Guard that restricts a route to admin users only."""
    user: AuthContext = connection.user
    if not user.is_admin:
        raise PermissionDeniedException("Admin access required")
