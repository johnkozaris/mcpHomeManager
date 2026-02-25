"""Admin-only API endpoints for system management."""

import os
from pathlib import Path
from uuid import UUID

import anyio
import msgspec
import structlog
from cryptography.fernet import Fernet
from litestar import Controller, Request, get, post, put
from litestar.datastructures import State
from litestar.exceptions import ClientException
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from domain.entities.smtp_config import SmtpConfig
from entrypoints.api.guards import require_admin
from infrastructure.encryption.fernet_encryption import FernetEncryption
from infrastructure.persistence.service_repository import ServiceRepository
from infrastructure.persistence.smtp_repository import SmtpConfigRepository
from infrastructure.persistence.user_repository import UserRepository
from security.auth_context import AuthContext
from services.email_service import EmailService
from services.key_rotation import KeyRotationService

logger = structlog.get_logger()

SECRETS_KEY_PATH = Path("/app/data/encryption_key")


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------


class RotateKeyRequest(msgspec.Struct):
    new_key: str | None = None


class RotateKeyResponse(msgspec.Struct):
    status: str
    new_key: str
    services_rotated: int
    users_rotated: int
    warning: str | None = None


class SmtpConfigRequest(msgspec.Struct):
    host: str
    port: int = 587
    username: str | None = None
    password: str | None = None  # plaintext — will be Fernet encrypted before storage
    from_email: str = ""
    use_tls: bool = True
    is_enabled: bool = True


class SmtpConfigResponse(msgspec.Struct):
    host: str
    port: int
    username: str | None
    has_password: bool
    from_email: str
    use_tls: bool
    is_enabled: bool


class SmtpTestResponse(msgspec.Struct):
    success: bool
    message: str


class SelfMcpRequest(msgspec.Struct):
    enabled: bool


class SelfMcpResponse(msgspec.Struct):
    enabled: bool


# ---------------------------------------------------------------------------
# Controller
# ---------------------------------------------------------------------------


class AdminController(Controller):
    path = "/api/admin"
    guards = [require_admin]

    @post("/rotate-encryption-key")
    async def rotate_encryption_key(
        self,
        db_session: AsyncSession,
        state: State,
        data: RotateKeyRequest,
    ) -> RotateKeyResponse:
        """Rotate the Fernet encryption key.

        Re-encrypts all service tokens and user API key backups atomically.
        Returns the new key — save it, it won't be shown again.
        """
        old_encryption = state.encryption

        # Generate or validate the new key
        new_key_str = data.new_key or Fernet.generate_key().decode()

        try:
            new_encryption = FernetEncryption(new_key_str)
        except Exception as e:
            raise ClientException(f"Invalid Fernet key: {e}") from e

        # Re-encrypt everything in one transaction
        rotation_service = KeyRotationService(
            service_repo=ServiceRepository(db_session),
            user_repo=UserRepository(db_session),
            old_encryption=old_encryption,
            new_encryption=new_encryption,
            smtp_repo=SmtpConfigRepository(db_session),
        )
        summary = await rotation_service.rotate()

        # Swap in-memory encryption BEFORE commit so concurrent requests
        # that read re-encrypted data can decrypt it immediately.
        state.encryption = new_encryption
        if hasattr(state, "tool_registry"):
            state.tool_registry.update_encryption(new_encryption)
        if hasattr(state, "health_runner"):
            state.health_runner.update_encryption(new_encryption)

        await db_session.commit()

        logger.info(
            "encryption_key_rotated",
            services=summary["services"],
            users=summary["users"],
        )

        # Best-effort: persist new key to secrets volume
        persisted = False
        try:
            async_path = anyio.Path(SECRETS_KEY_PATH)
            if await async_path.parent.exists():
                await async_path.write_text(new_key_str)
                persisted = True
                logger.info("encryption_key_persisted", path=str(SECRETS_KEY_PATH))
        except OSError:
            logger.warning(
                "Could not persist new encryption key to %s. "
                "Update ENCRYPTION_KEY in your .env or secrets volume manually.",
                SECRETS_KEY_PATH,
            )

        # Detect .env override that would revert the rotation on restart
        warning = None
        env_key = os.environ.get("ENCRYPTION_KEY", "")
        if env_key and env_key != new_key_str:
            warning = (
                "ENCRYPTION_KEY is set in your environment (.env file). "
                "On container restart, the old key will take precedence and decryption will fail. "
                "Remove ENCRYPTION_KEY from your .env file or update it to the new key."
            )
            logger.warning("env_override_conflict", detail=warning)
        elif not persisted:
            warning = (
                "New key could not be saved to the secrets volume. "
                "Set ENCRYPTION_KEY in your .env or the key will be lost on restart."
            )

        return RotateKeyResponse(
            status="rotated",
            new_key=new_key_str,
            services_rotated=summary["services"],
            users_rotated=summary["users"],
            warning=warning,
        )

    # ------------------------------------------------------------------
    # SMTP configuration
    # ------------------------------------------------------------------

    @get("/smtp")
    async def get_smtp(
        self,
        db_session: AsyncSession,
    ) -> SmtpConfigResponse:
        """Get the current SMTP configuration (password redacted)."""
        repo = SmtpConfigRepository(db_session)
        config = await repo.get()
        if config is None:
            return SmtpConfigResponse(
                host="",
                port=587,
                username=None,
                has_password=False,
                from_email="",
                use_tls=True,
                is_enabled=False,
            )
        return SmtpConfigResponse(
            host=config.host,
            port=config.port,
            username=config.username,
            has_password=config.password_encrypted is not None,
            from_email=config.from_email,
            use_tls=config.use_tls,
            is_enabled=config.is_enabled,
        )

    @put("/smtp")
    async def update_smtp(
        self,
        db_session: AsyncSession,
        state: State,
        data: SmtpConfigRequest,
    ) -> SmtpConfigResponse:
        """Create or update SMTP configuration."""
        encryption = state.encryption

        # Encrypt password if provided
        password_encrypted = None
        if data.password:
            password_encrypted = encryption.encrypt(data.password)

        config = SmtpConfig(
            host=data.host,
            port=data.port,
            username=data.username,
            password_encrypted=password_encrypted,
            from_email=data.from_email,
            use_tls=data.use_tls,
            is_enabled=data.is_enabled,
        )

        repo = SmtpConfigRepository(db_session)
        saved = await repo.upsert(config)
        await db_session.commit()

        logger.info("smtp_config_updated", host=data.host, port=data.port)

        return SmtpConfigResponse(
            host=saved.host,
            port=saved.port,
            username=saved.username,
            has_password=saved.password_encrypted is not None,
            from_email=saved.from_email,
            use_tls=saved.use_tls,
            is_enabled=saved.is_enabled,
        )

    @post("/smtp/test")
    async def test_smtp(
        self,
        request: Request,
        db_session: AsyncSession,
        state: State,
    ) -> SmtpTestResponse:
        """Send a test email to the admin's email address."""
        ctx: AuthContext = request.user
        if not ctx.user_id:
            raise ClientException("Admin user account required to send test email.")

        user_repo = UserRepository(db_session)
        user = await user_repo.get_by_id(UUID(ctx.user_id))
        if not user or not user.email:
            raise ClientException("Set your email address in your profile before testing SMTP.")

        smtp_repo = SmtpConfigRepository(db_session)
        smtp_config = await smtp_repo.get()
        if not smtp_config or not smtp_config.is_enabled:
            raise ClientException("SMTP is not configured or disabled.")

        try:
            svc = EmailService(smtp_config, state.encryption)
            await svc.send_test(user.email)
            return SmtpTestResponse(success=True, message=f"Test email sent to {user.email}")
        except Exception as e:
            logger.warning("smtp_test_failed", error=str(e))
            return SmtpTestResponse(success=False, message=str(e))

    # --- Self-MCP toggle ---

    @get("/self-mcp")
    async def get_self_mcp(self) -> SelfMcpResponse:
        return SelfMcpResponse(enabled=settings.self_mcp_enabled)

    @put("/self-mcp")
    async def set_self_mcp(self, state: State, data: SelfMcpRequest) -> SelfMcpResponse:
        settings.self_mcp_enabled = data.enabled
        if hasattr(state, "mcp_factory"):
            state.mcp_factory.sync_meta_tools(data.enabled)
        else:
            logger.warning("self_mcp_sync_skipped", reason="missing_mcp_factory")
        logger.info("self_mcp_toggled", enabled=data.enabled)
        return SelfMcpResponse(enabled=data.enabled)
