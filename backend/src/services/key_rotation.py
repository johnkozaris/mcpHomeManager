"""Service for rotating the Fernet encryption key.

Re-encrypts all encrypted fields in the database within a single transaction.
The caller is responsible for committing the DB session.
"""

import structlog

from domain.ports.encryption import IEncryptionPort
from domain.ports.service_repository import IServiceRepository
from domain.ports.smtp_repository import ISmtpConfigRepository
from domain.ports.user_repository import IUserRepository

logger = structlog.get_logger()


class KeyRotationService:
    """Re-encrypts all stored secrets when the encryption key changes."""

    def __init__(
        self,
        service_repo: IServiceRepository,
        user_repo: IUserRepository,
        old_encryption: IEncryptionPort,
        new_encryption: IEncryptionPort,
        smtp_repo: ISmtpConfigRepository | None = None,
    ) -> None:
        self._service_repo = service_repo
        self._user_repo = user_repo
        self._smtp_repo = smtp_repo
        self._old = old_encryption
        self._new = new_encryption

    async def rotate(self) -> dict[str, int]:
        """Re-encrypt all secrets from old key to new key.

        Returns a summary: ``{"services": N, "users": N, "smtp": N}``.
        """
        services_count = await self._rotate_service_tokens()
        users_count = await self._rotate_user_keys()
        smtp_count = await self._rotate_smtp_password()

        logger.info(
            "key_rotation_complete",
            services_rotated=services_count,
            users_rotated=users_count,
            smtp_rotated=smtp_count,
        )
        return {
            "services": services_count,
            "users": users_count,
            "smtp": smtp_count,
        }

    async def _rotate_service_tokens(self) -> int:
        services = await self._service_repo.get_all()
        count = 0
        for svc in services:
            if not svc.api_token_encrypted:
                continue
            plaintext = self._old.decrypt(svc.api_token_encrypted)
            svc.api_token_encrypted = self._new.encrypt(plaintext)
            await self._service_repo.update(svc)
            count += 1
        return count

    async def _rotate_user_keys(self) -> int:
        users = await self._user_repo.get_all()
        count = 0
        for user in users:
            if not user.encrypted_api_key:
                continue
            plaintext = self._old.decrypt(user.encrypted_api_key)
            user.encrypted_api_key = self._new.encrypt(plaintext)
            await self._user_repo.update(user)
            count += 1
        return count

    async def _rotate_smtp_password(self) -> int:
        if self._smtp_repo is None:
            return 0
        config = await self._smtp_repo.get()
        if config is None or not config.password_encrypted:
            return 0
        plaintext = self._old.decrypt(config.password_encrypted)
        config.password_encrypted = self._new.encrypt(plaintext)
        await self._smtp_repo.upsert(config)
        return 1
