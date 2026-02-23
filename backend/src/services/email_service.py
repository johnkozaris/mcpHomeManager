"""Email service for sending password reset and test emails via SMTP."""

from email.message import EmailMessage

import aiosmtplib
import structlog

from config import settings
from domain.entities.smtp_config import SmtpConfig
from domain.ports.encryption import IEncryptionPort

logger = structlog.get_logger()


class EmailService:
    """Sends emails using an SMTP configuration from the database."""

    def __init__(self, smtp_config: SmtpConfig, encryption: IEncryptionPort) -> None:
        self._config = smtp_config
        self._encryption = encryption

    def _decrypt_password(self) -> str | None:
        if not self._config.password_encrypted:
            return None
        return self._encryption.decrypt(self._config.password_encrypted)

    async def _send(self, msg: EmailMessage) -> None:
        password = self._decrypt_password()
        # Port 465 uses implicit TLS (SMTPS); port 587 uses STARTTLS
        use_implicit_tls = self._config.port == 465
        await aiosmtplib.send(
            msg,
            hostname=self._config.host,
            port=self._config.port,
            username=self._config.username,
            password=password,
            use_tls=use_implicit_tls,
            start_tls=self._config.use_tls and not use_implicit_tls,
        )

    async def send_password_reset(
        self,
        to_email: str,
        token: str,
        username: str,
        public_url: str,
    ) -> None:
        """Send a password reset email with a link containing the token."""
        reset_url = f"{public_url.rstrip('/')}/reset-password?token={token}"

        msg = EmailMessage()
        msg["Subject"] = f"{settings.app_name} — Password Reset"
        msg["From"] = self._config.from_email
        msg["To"] = to_email
        msg.set_content(
            f"Hi {username},\n\n"
            f"A password reset was requested for your account.\n\n"
            f"Click the link below to set a new password:\n"
            f"{reset_url}\n\n"
            f"This link expires in 1 hour.\n\n"
            f"If you did not request this, you can safely ignore this email.\n"
        )

        await self._send(msg)
        logger.info("password_reset_email_sent", to=to_email, username=username)

    async def send_test(self, to_email: str) -> None:
        """Send a test email to verify SMTP configuration."""
        msg = EmailMessage()
        msg["Subject"] = f"{settings.app_name} — SMTP Test"
        msg["From"] = self._config.from_email
        msg["To"] = to_email
        msg.set_content(
            f"This is a test email from {settings.app_name}.\n\n"
            "If you received this, your SMTP configuration is working correctly.\n"
        )

        await self._send(msg)
        logger.info("test_email_sent", to=to_email)
