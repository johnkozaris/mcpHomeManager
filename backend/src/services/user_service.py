"""User management service — account CRUD, authentication, and API key lifecycle."""

import hashlib
import os
import secrets
from uuid import UUID

from domain.entities.user import User
from domain.ports.encryption import IEncryptionPort
from domain.ports.user_repository import IUserRepository


class UserService:
    """Manages user accounts and API key lifecycle."""

    def __init__(
        self,
        repository: IUserRepository,
        encryption: IEncryptionPort | None = None,
    ) -> None:
        self._repo = repository
        self._encryption = encryption

    async def list_all(self) -> list[User]:
        return await self._repo.get_all()

    async def get_by_id(self, user_id: UUID) -> User | None:
        return await self._repo.get_by_id(user_id)

    async def create_user(
        self,
        username: str,
        is_admin: bool = False,
        allowed_service_ids: list[UUID] | None = None,
        password: str | None = None,
        email: str | None = None,
        self_mcp_enabled: bool = False,
    ) -> User:
        """No API key is generated — call generate_api_key separately."""
        existing = await self._repo.get_by_username(username)
        if existing is not None:
            raise ValueError(f"User '{username}' already exists")

        password_hash = self._hash_password(password) if password else None

        user = User(
            username=username,
            email=email,
            api_key_hash=None,
            is_admin=is_admin,
            self_mcp_enabled=self_mcp_enabled,
            allowed_service_ids=allowed_service_ids or [],
            password_hash=password_hash,
        )
        return await self._repo.create(user)

    async def generate_api_key(self, user_id: UUID) -> tuple[User, str]:
        """Generate a new API key for a user. Replaces any existing key.

        Returns (user, plaintext_api_key). The plaintext key is shown once.
        """
        user = await self._repo.get_by_id(user_id)
        if user is None:
            raise ValueError(f"User not found: {user_id}")

        api_key = self._generate_api_key()
        user.api_key_hash = self._hash_key(api_key)
        user.encrypted_api_key = self._encryption.encrypt(api_key) if self._encryption else None
        updated = await self._repo.update(user)
        return updated, api_key

    async def reveal_api_key(self, user_id: UUID) -> str:
        """Decrypt and return the user's existing API key."""
        if self._encryption is None:
            raise ValueError("Encryption not configured")
        user = await self._repo.get_by_id(user_id)
        if user is None:
            raise ValueError(f"User not found: {user_id}")
        if not user.encrypted_api_key:
            raise ValueError("No API key set")
        return self._encryption.decrypt(user.encrypted_api_key)

    async def revoke_api_key(self, user_id: UUID) -> User:
        """Revoke the user's API key."""
        user = await self._repo.get_by_id(user_id)
        if user is None:
            raise ValueError(f"User not found: {user_id}")

        user.api_key_hash = None
        user.encrypted_api_key = None
        return await self._repo.update(user)

    async def set_password(self, user_id: UUID, password: str) -> User:
        """Set or update a user's login password."""
        user = await self._repo.get_by_id(user_id)
        if user is None:
            raise ValueError(f"User not found: {user_id}")
        user.password_hash = self._hash_password(password)
        return await self._repo.update(user)

    async def authenticate_by_password(self, username: str, password: str) -> User | None:
        """Authenticate a user by username + password. Returns None if invalid."""
        user = await self._repo.get_by_username(username)
        if user is None or user.password_hash is None:
            return None
        if self._verify_password(password, user.password_hash):
            return user
        return None

    async def delete_user(self, user_id: UUID) -> None:
        await self._repo.delete(user_id)

    async def update_user(
        self,
        user_id: UUID,
        *,
        is_admin: bool | None = None,
        allowed_service_ids: list[UUID] | None = None,
        self_mcp_enabled: bool | None = None,
    ) -> User:
        user = await self._repo.get_by_id(user_id)
        if user is None:
            raise ValueError(f"User not found: {user_id}")
        if is_admin is not None:
            user.is_admin = is_admin
        if allowed_service_ids is not None:
            user.allowed_service_ids = allowed_service_ids
        if self_mcp_enabled is not None:
            user.self_mcp_enabled = self_mcp_enabled
        return await self._repo.update(user)

    async def authenticate_by_key(self, api_key: str) -> User | None:
        """Look up a user by their API key. Returns None if not found."""
        key_hash = self._hash_key(api_key)
        return await self._repo.get_by_api_key_hash(key_hash)

    @staticmethod
    def _generate_api_key() -> str:
        return f"mcp_{secrets.token_urlsafe(32)}"

    @staticmethod
    def _hash_key(key: str) -> str:
        """SHA-256 hash of an API key (keys are high-entropy, not passwords)."""
        return hashlib.sha256(key.encode()).hexdigest()

    @staticmethod
    def _hash_password(password: str) -> str:
        salt = os.urandom(16)
        dk = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1, dklen=32)
        return f"{salt.hex()}${dk.hex()}"

    @staticmethod
    def _verify_password(password: str, stored_hash: str) -> bool:
        try:
            salt_hex, dk_hex = stored_hash.split("$", 1)
            salt = bytes.fromhex(salt_hex)
            expected = bytes.fromhex(dk_hex)
            dk = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1, dklen=32)
            return secrets.compare_digest(dk, expected)
        except ValueError, TypeError:
            return False
