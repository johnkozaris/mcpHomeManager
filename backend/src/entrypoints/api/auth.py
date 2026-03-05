"""Authentication endpoints for web dashboard login.

- Login with username + password → receive an opaque session token
- MCP API keys remain separate and long-lived for machine clients
- GET /me returns current user info from the session
- Password reset via email (when SMTP is configured)
"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

import msgspec
import structlog
from litestar import Controller, Request, Response, delete, get, post
from litestar.datastructures import State
from litestar.exceptions import ClientException, NotAuthorizedException
from sqlalchemy import delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from infrastructure.persistence.orm_models import SessionTokenModel
from infrastructure.persistence.reset_token_repository import ResetTokenRepository
from infrastructure.persistence.smtp_repository import SmtpConfigRepository
from infrastructure.persistence.user_repository import UserRepository
from security.auth_context import AuthContext
from services.email_service import EmailService
from services.user_service import UserService

logger = structlog.get_logger()

SESSION_LIFETIME_HOURS = 24 * 7  # 7-day sessions (homelab-friendly)
SESSION_COOKIE_NAME = "mcp_session"
SESSION_COOKIE_MAX_AGE = SESSION_LIFETIME_HOURS * 3600  # seconds


class LoginRequest(msgspec.Struct):
    username: str
    password: str


class LoginResponse(msgspec.Struct):
    token: str
    username: str
    is_admin: bool


class MeResponse(msgspec.Struct):
    username: str
    is_admin: bool
    allowed_service_ids: list[str]
    has_api_key: bool
    can_reveal_api_key: bool = False


class ApiKeyResponse(msgspec.Struct):
    api_key: str


class ForgotPasswordRequest(msgspec.Struct):
    email: str


class ResetPasswordRequest(msgspec.Struct):
    token: str
    password: str


RESET_TOKEN_TTL_HOURS = 1


async def create_session(
    db_session: AsyncSession,
    *,
    username: str,
    is_admin: bool,
    user_id: str | None = None,
) -> str:
    """Create a session token and store its hash in the DB."""
    token = f"mcp_session_{secrets.token_urlsafe(32)}"
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    expires_at = datetime.now(UTC) + timedelta(hours=SESSION_LIFETIME_HOURS)

    session_model = SessionTokenModel(
        token_hash=token_hash,
        user_id=UUID(user_id) if user_id else None,
        expires_at=expires_at,
        is_admin=is_admin,
        username=username,
    )
    db_session.add(session_model)
    await db_session.flush()
    return token


def apply_session_cookie(response: Response, token: str) -> None:
    """Set the httpOnly session cookie on a response."""
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_COOKIE_MAX_AGE,
        httponly=True,
        secure=settings.public_url.startswith("https"),
        samesite="lax",
        path="/",
    )


class AuthController(Controller):
    path = "/api/auth"

    @post("/login", exclude_from_auth=True)
    async def login(
        self,
        db_session: AsyncSession,
        data: LoginRequest,
        user_service: UserService,
    ) -> Response[LoginResponse]:
        """Authenticate with username + password, receive a session token.

        The session token is set as an httpOnly cookie for browser clients
        (XSS-safe). The token is also returned in the response body for API
        clients that cannot access cookies, but browser frontends should
        rely on the cookie.
        """
        user = await user_service.authenticate_by_password(data.username, data.password)

        if user is None:
            logger.warning("login_failed", username=data.username)
            raise NotAuthorizedException("Invalid username or password.")

        token = await create_session(
            db_session,
            username=user.username,
            is_admin=user.is_admin,
            user_id=str(user.id),
        )
        await db_session.commit()
        logger.info("login_success", username=user.username)
        body = LoginResponse(
            token=token,
            username=user.username,
            is_admin=user.is_admin,
        )
        response = Response(content=body)
        apply_session_cookie(response, token)
        return response

    @get("/me")
    async def me(self, request: Request, user_service: UserService) -> MeResponse:
        """Return the current authenticated user's info from the session."""
        ctx: AuthContext = request.user

        has_api_key = False
        can_reveal = False
        if ctx.user_id:
            user = await user_service.get_by_id(UUID(ctx.user_id))
            if user and user.api_key_hash:
                has_api_key = True
                can_reveal = bool(user.encrypted_api_key)

        return MeResponse(
            username=ctx.username,
            is_admin=ctx.is_admin,
            allowed_service_ids=sorted(ctx.allowed_service_ids),
            has_api_key=has_api_key,
            can_reveal_api_key=can_reveal,
        )

    @post("/api-key")
    async def create_api_key(
        self,
        request: Request,
        db_session: AsyncSession,
        user_service: UserService,
    ) -> ApiKeyResponse:
        """Generate a new MCP API key for the current user. Replaces any existing key."""
        ctx: AuthContext = request.user
        if not ctx.user_id:
            raise NotAuthorizedException("A user account is required for API key management.")

        try:
            _, api_key = await user_service.generate_api_key(UUID(ctx.user_id))
        except ValueError as e:
            raise NotAuthorizedException(str(e)) from e
        await db_session.commit()
        logger.info("api_key_generated", username=ctx.username)
        return ApiKeyResponse(api_key=api_key)

    @get("/api-key")
    async def get_api_key(
        self,
        request: Request,
        user_service: UserService,
    ) -> ApiKeyResponse:
        """Reveal the current user's MCP API key (decrypted from storage)."""
        ctx: AuthContext = request.user
        if not ctx.user_id:
            raise NotAuthorizedException("A user account is required for API key management.")

        try:
            plaintext = await user_service.reveal_api_key(UUID(ctx.user_id))
        except ValueError as e:
            raise ClientException(str(e), status_code=404) from e
        return ApiKeyResponse(api_key=plaintext)

    @delete("/api-key")
    async def revoke_api_key(
        self,
        request: Request,
        db_session: AsyncSession,
        user_service: UserService,
    ) -> None:
        """Revoke the current user's MCP API key."""
        ctx: AuthContext = request.user
        if not ctx.user_id:
            raise NotAuthorizedException("A user account is required for API key management.")

        try:
            await user_service.revoke_api_key(UUID(ctx.user_id))
        except ValueError as e:
            raise NotAuthorizedException(str(e)) from e
        await db_session.commit()
        logger.info("api_key_revoked", username=ctx.username)

    @delete("/logout")
    async def logout(self, request: Request, db_session: AsyncSession) -> Response[None]:
        """Invalidate the current session token and clear the session cookie."""
        token: str = request.auth
        ctx: AuthContext = request.user

        if token.startswith("mcp_session_"):
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            await db_session.execute(
                sa_delete(SessionTokenModel).where(SessionTokenModel.token_hash == token_hash)
            )
            await db_session.commit()
            logger.info("session_logout", username=ctx.username)

        response = Response(content=None, status_code=204)
        response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
        return response

    # ------------------------------------------------------------------
    # Password reset
    # ------------------------------------------------------------------

    @post("/forgot-password", exclude_from_auth=True)
    async def forgot_password(
        self,
        db_session: AsyncSession,
        state: State,
        data: ForgotPasswordRequest,
    ) -> dict[str, str]:
        """Request a password reset email. Always returns 200 to prevent email enumeration."""
        smtp_repo = SmtpConfigRepository(db_session)
        smtp_config = await smtp_repo.get()

        if smtp_config and smtp_config.is_enabled and data.email:
            user_repo = UserRepository(db_session)
            user = await user_repo.get_by_email(data.email)

            if user and user.id:
                raw_token = secrets.token_urlsafe(32)
                token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
                expires_at = datetime.now(UTC) + timedelta(hours=RESET_TOKEN_TTL_HOURS)

                reset_repo = ResetTokenRepository(db_session)
                await reset_repo.delete_for_user(user.id)
                await reset_repo.create(token_hash, user.id, expires_at)
                await db_session.commit()

                # Send email — failure is non-fatal (token is persisted, user can retry)
                try:
                    email_svc = EmailService(smtp_config, state.encryption)
                    await email_svc.send_password_reset(
                        to_email=data.email,
                        token=raw_token,
                        username=user.username,
                        public_url=settings.public_url,
                    )
                except Exception:
                    logger.exception("password_reset_email_failed")

        return {"status": "ok"}

    @post("/reset-password", exclude_from_auth=True)
    async def reset_password(
        self,
        db_session: AsyncSession,
        data: ResetPasswordRequest,
        user_service: UserService,
    ) -> dict[str, str]:
        """Reset password using a token from email."""
        if len(data.password) < 8:
            raise ClientException("Password must be at least 8 characters.")

        token_hash = hashlib.sha256(data.token.encode()).hexdigest()
        reset_repo = ResetTokenRepository(db_session)
        result = await reset_repo.get_user_id_by_hash(token_hash)

        if result is None:
            raise ClientException("Invalid or expired reset token.", status_code=400)

        user_id, expires_at = result
        if expires_at < datetime.now(UTC):
            await reset_repo.delete_by_hash(token_hash)
            await db_session.commit()
            raise ClientException("This reset link has expired.", status_code=400)

        await user_service.set_password(user_id, data.password)

        await reset_repo.delete_by_hash(token_hash)
        await db_session.commit()

        logger.info("password_reset_success", user_id=str(user_id))
        return {"status": "ok"}
