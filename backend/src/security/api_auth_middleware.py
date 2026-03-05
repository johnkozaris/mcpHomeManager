"""API authentication middleware using Litestar's AbstractAuthenticationMiddleware.

Every /api/* request is authenticated via either:

1. Session tokens (from web login) — read from the ``mcp_session`` httpOnly
   cookie, falling back to ``Authorization: Bearer`` for non-browser clients
2. Per-user API keys (for machine clients) — read from ``X-API-Key`` header
   or ``Authorization: Bearer`` header, validated via SHA-256 hash lookup

Sets ``request.user`` to a typed :class:`AuthContext` and ``request.auth``
to the raw token string.
"""

import hashlib
from datetime import UTC, datetime

from litestar.connection import ASGIConnection
from litestar.exceptions import NotAuthorizedException
from litestar.middleware import AbstractAuthenticationMiddleware, AuthenticationResult

from security.auth_helpers import authenticate_api_key, build_auth_context, extract_api_token


class ApiAuthMiddleware(AbstractAuthenticationMiddleware):
    async def authenticate_request(self, connection: ASGIConnection) -> AuthenticationResult:
        cookie_token = connection.cookies.get("mcp_session", "")
        if cookie_token and cookie_token.startswith("mcp_session_"):
            return await self._authenticate_session(connection, cookie_token)

        auth_header = connection.headers.get("authorization", "")
        token = extract_api_token(
            auth_header=auth_header,
            api_key_header=connection.headers.get("x-api-key", ""),
        )

        if not token:
            raise NotAuthorizedException(
                "Authentication required. Provide a session token or API key."
            )

        if token.startswith("mcp_session_"):
            return await self._authenticate_session(connection, token)

        return await self._authenticate_api_key(connection, token)

    async def _authenticate_session(
        self, connection: ASGIConnection, token: str
    ) -> AuthenticationResult:
        from sqlalchemy import select

        from infrastructure.persistence.orm_models import SessionTokenModel
        from infrastructure.persistence.user_repository import UserRepository

        token_hash = hashlib.sha256(token.encode()).hexdigest()
        session_factory = connection.app.state.session_factory

        async with session_factory() as session:
            result = await session.execute(
                select(SessionTokenModel).where(SessionTokenModel.token_hash == token_hash)
            )
            session_token = result.scalar_one_or_none()
            if session_token is None:
                raise NotAuthorizedException("Invalid or expired session.")
            if session_token.expires_at < datetime.now(UTC):
                raise NotAuthorizedException("Session expired. Please sign in again.")

            # Always resolve the live User for current permissions.
            # Session tokens cache username/is_admin, but the User table
            # is authoritative — admin status or deletion must take effect
            # immediately, not wait for session expiry.
            if session_token.user_id is None:
                raise NotAuthorizedException("Invalid session — no linked user.")

            repo = UserRepository(session)
            user = await repo.get_by_id(session_token.user_id)
            if user is None:
                raise NotAuthorizedException("User account has been deleted.")

            ctx = build_auth_context(user)
            return AuthenticationResult(user=ctx, auth=token)

    async def _authenticate_api_key(
        self, connection: ASGIConnection, token: str
    ) -> AuthenticationResult:
        session_factory = connection.app.state.session_factory
        user = await authenticate_api_key(session_factory, token)
        if user is not None:
            ctx = build_auth_context(user)
            return AuthenticationResult(user=ctx, auth=token)

        raise NotAuthorizedException("Invalid credentials.")
