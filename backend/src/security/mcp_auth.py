"""MCP endpoint authentication guard — per-user API key verification."""

import asyncio
import time
from collections import deque

import structlog
from litestar.response.base import ASGIResponse
from litestar.types import Receive, Scope, Send

logger = structlog.get_logger()

_AUTH_FAIL_WINDOW_SECONDS = 60
_AUTH_FAIL_MAX_ATTEMPTS = 10
_AUTH_BLOCK_SECONDS = 300
_MAX_TRACKED_CLIENTS = 10_000  # Cap to prevent memory exhaustion from IP rotation attacks
_auth_failures: dict[str, deque[float]] = {}
_auth_blocked_until: dict[str, float] = {}
_auth_rate_lock = asyncio.Lock()


def _client_identifier(scope: Scope) -> str:
    """Best-effort client identifier for auth throttling.

    Uses the TCP remote address (not X-Forwarded-For) to prevent
    attacker-controlled header spoofing from bypassing rate limits.
    """
    client = scope.get("client")
    if isinstance(client, tuple) and client:
        return str(client[0])
    return "unknown"


async def _is_auth_rate_limited(scope: Scope) -> bool:
    """Return True when the client has exceeded auth failure threshold."""
    client_id = _client_identifier(scope)
    now = time.monotonic()

    async with _auth_rate_lock:
        _prune_blocked_clients(now)
        return _auth_blocked_until.get(client_id, 0) > now


def _prune_blocked_clients(now: float) -> None:
    """Prune expired/overflow blocked-client entries to keep memory bounded."""
    expired = [
        client_id
        for client_id, blocked_until in _auth_blocked_until.items()
        if blocked_until <= now
    ]
    for client_id in expired:
        _auth_blocked_until.pop(client_id, None)

    overflow = len(_auth_blocked_until) - _MAX_TRACKED_CLIENTS
    if overflow > 0:
        # Remove entries that expire soonest first.
        ordered = sorted(_auth_blocked_until.items(), key=lambda item: item[1])
        for client_id, _ in ordered[:overflow]:
            _auth_blocked_until.pop(client_id, None)


async def _record_auth_failure(scope: Scope) -> None:
    """Record failed auth attempt and apply temporary block when threshold is exceeded."""
    client_id = _client_identifier(scope)
    now = time.monotonic()

    async with _auth_rate_lock:
        _prune_blocked_clients(now)
        attempts = _auth_failures.setdefault(client_id, deque())
        cutoff = now - _AUTH_FAIL_WINDOW_SECONDS
        while attempts and attempts[0] < cutoff:
            attempts.popleft()
        attempts.append(now)

        if len(attempts) >= _AUTH_FAIL_MAX_ATTEMPTS:
            _auth_blocked_until[client_id] = now + _AUTH_BLOCK_SECONDS
            _auth_failures.pop(client_id, None)

        # Evict oldest entries if tracking too many clients (prevents memory exhaustion)
        if len(_auth_failures) > _MAX_TRACKED_CLIENTS:
            oldest = next(iter(_auth_failures))
            _auth_failures.pop(oldest, None)
        _prune_blocked_clients(now)


async def _clear_auth_failures(scope: Scope) -> None:
    """Reset failure tracking after successful authentication."""
    client_id = _client_identifier(scope)
    async with _auth_rate_lock:
        _auth_failures.pop(client_id, None)
        _auth_blocked_until.pop(client_id, None)


async def _send_unauthorized(scope: Scope, receive: Receive, send: Send) -> None:
    response = ASGIResponse(body=b'{"error":"Unauthorized"}', status_code=401)
    await response(scope, receive, send)


async def _deny_auth(scope: Scope, receive: Receive, send: Send, *, reason: str) -> bool:
    logger.warning("mcp_auth_failed", reason=reason, client_id=_client_identifier(scope))
    await _record_auth_failure(scope)
    await _send_unauthorized(scope, receive, send)
    return False


async def verify_mcp_request(
    scope: Scope,
    receive: Receive,
    send: Send,
) -> bool:
    """Verify MCP request authentication via per-user API key. Returns True if authorized."""
    if await _is_auth_rate_limited(scope):
        response = ASGIResponse(
            body=b'{"error":"Too many authentication attempts"}',
            status_code=429,
        )
        await response(scope, receive, send)
        return False

    # Extract API key from headers
    headers_dict = dict(scope.get("headers", []))
    auth_header = headers_dict.get(b"authorization", b"").decode()
    api_key_header = headers_dict.get(b"x-api-key", b"").decode()
    bearer_token = auth_header[7:].strip() if auth_header.lower().startswith("bearer ") else ""
    provided_key = api_key_header or bearer_token

    if not provided_key:
        return await _deny_auth(scope, receive, send, reason="missing_api_key")

    # Look up user by API key hash
    app = scope.get("litestar_app")
    if not app or not hasattr(app, "state") or not hasattr(app.state, "session_factory"):
        logger.error("Session factory not available for MCP auth")
        await _send_unauthorized(scope, receive, send)
        return False

    from infrastructure.persistence.user_repository import UserRepository
    from services.user_service import UserService

    async with app.state.session_factory() as session:
        user_svc = UserService(UserRepository(session))
        user = await user_svc.authenticate_by_key(provided_key)

    if user is None:
        return await _deny_auth(scope, receive, send, reason="invalid_api_key")

    # Store authenticated user in scope for downstream authorization
    scope.setdefault("state", {})
    scope["state"]["authenticated_user"] = user
    await _clear_auth_failures(scope)
    return True
