"""Tests for password reset token lifecycle."""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from conftest import FakeEncryption, FakeUserRepository
from domain.entities.smtp_config import SmtpConfig
from domain.ports.reset_token_repository import IResetTokenRepository
from services.user_service import UserService


class FakeResetTokenRepository(IResetTokenRepository):
    """In-memory fake for password reset tokens."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[UUID, datetime]] = {}

    async def create(self, token_hash: str, user_id: UUID, expires_at: datetime) -> None:
        self._store[token_hash] = (user_id, expires_at)

    async def get_user_id_by_hash(self, token_hash: str) -> tuple[UUID, datetime] | None:
        return self._store.get(token_hash)

    async def delete_by_hash(self, token_hash: str) -> None:
        self._store.pop(token_hash, None)

    async def delete_for_user(self, user_id: UUID) -> None:
        to_delete = [k for k, (uid, _) in self._store.items() if uid == user_id]
        for k in to_delete:
            del self._store[k]

    async def delete_expired(self) -> int:
        now = datetime.now(UTC)
        expired = [k for k, (_, exp) in self._store.items() if exp < now]
        for k in expired:
            del self._store[k]
        return len(expired)


class TestPasswordResetTokens:
    async def test_create_and_retrieve_token(self) -> None:
        repo = FakeResetTokenRepository()
        user_id = uuid4()
        token_hash = hashlib.sha256(b"test-token").hexdigest()
        expires = datetime.now(UTC) + timedelta(hours=1)

        await repo.create(token_hash, user_id, expires)

        result = await repo.get_user_id_by_hash(token_hash)
        assert result is not None
        assert result[0] == user_id

    async def test_unknown_token_returns_none(self) -> None:
        repo = FakeResetTokenRepository()
        result = await repo.get_user_id_by_hash("nonexistent")
        assert result is None

    async def test_delete_token(self) -> None:
        repo = FakeResetTokenRepository()
        token_hash = hashlib.sha256(b"test-token").hexdigest()
        await repo.create(token_hash, uuid4(), datetime.now(UTC) + timedelta(hours=1))

        await repo.delete_by_hash(token_hash)
        assert await repo.get_user_id_by_hash(token_hash) is None

    async def test_delete_expired_tokens(self) -> None:
        repo = FakeResetTokenRepository()

        # One expired, one still valid
        expired_hash = hashlib.sha256(b"expired").hexdigest()
        valid_hash = hashlib.sha256(b"valid").hexdigest()

        await repo.create(expired_hash, uuid4(), datetime.now(UTC) - timedelta(hours=1))
        await repo.create(valid_hash, uuid4(), datetime.now(UTC) + timedelta(hours=1))

        deleted = await repo.delete_expired()
        assert deleted == 1
        assert await repo.get_user_id_by_hash(expired_hash) is None
        assert await repo.get_user_id_by_hash(valid_hash) is not None

    async def test_token_single_use(self) -> None:
        """After using a token to reset password, it should be deleted."""
        repo = FakeResetTokenRepository()
        user_repo = FakeUserRepository()
        enc = FakeEncryption()
        svc = UserService(user_repo, encryption=enc)

        user = await svc.create_user(username="alice", password="oldpassword1", is_admin=False)
        assert user.id is not None

        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        expires = datetime.now(UTC) + timedelta(hours=1)
        await repo.create(token_hash, user.id, expires)

        # Simulate reset: look up token, change password, delete token
        result = await repo.get_user_id_by_hash(token_hash)
        assert result is not None
        found_user_id, found_expires = result
        assert found_expires > datetime.now(UTC)

        await svc.set_password(found_user_id, "newpassword1")
        await repo.delete_by_hash(token_hash)

        # Token is gone
        assert await repo.get_user_id_by_hash(token_hash) is None

        # New password works
        authed = await svc.authenticate_by_password("alice", "newpassword1")
        assert authed is not None

        # Old password doesn't
        authed_old = await svc.authenticate_by_password("alice", "oldpassword1")
        assert authed_old is None


class TestSmtpConfig:
    def test_smtp_config_entity(self) -> None:
        config = SmtpConfig(
            host="smtp.example.com",
            port=587,
            username="user@example.com",
            password_encrypted="enc:secret",
            from_email="noreply@example.com",
        )
        assert config.host == "smtp.example.com"
        assert config.use_tls is True
        assert config.is_enabled is True

    def test_smtp_password_encryption_roundtrip(self) -> None:
        enc = FakeEncryption()
        plaintext = "smtp_password_123"
        encrypted = enc.encrypt(plaintext)
        assert enc.decrypt(encrypted) == plaintext
