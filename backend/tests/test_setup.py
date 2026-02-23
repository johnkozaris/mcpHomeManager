"""Tests for the first-run setup wizard."""

import pytest

from conftest import FakeEncryption, FakeUserRepository
from services.user_service import UserService


class TestSetupWizard:
    """Test the setup wizard service-layer logic (no HTTP, no DB)."""

    async def test_setup_creates_admin_user(self) -> None:
        repo = FakeUserRepository()
        enc = FakeEncryption()
        svc = UserService(repo, encryption=enc)

        assert await repo.get_count() == 0

        user = await svc.create_user(
            username="admin",
            is_admin=True,
            password="securepass123",
            email="admin@example.com",
        )

        assert user.username == "admin"
        assert user.is_admin is True
        assert user.email == "admin@example.com"
        assert user.password_hash is not None
        assert await repo.get_count() == 1

    async def test_setup_generates_api_key(self) -> None:
        repo = FakeUserRepository()
        enc = FakeEncryption()
        svc = UserService(repo, encryption=enc)

        user = await svc.create_user(
            username="admin",
            is_admin=True,
            password="securepass123",
        )
        assert user.id is not None
        updated_user, api_key = await svc.generate_api_key(user.id)

        assert api_key.startswith("mcp_")
        assert updated_user.api_key_hash is not None
        assert updated_user.encrypted_api_key is not None

    async def test_setup_rejects_duplicate_username(self) -> None:
        repo = FakeUserRepository()
        enc = FakeEncryption()
        svc = UserService(repo, encryption=enc)

        await svc.create_user(username="admin", is_admin=True, password="pass12345678")

        with pytest.raises(ValueError, match="already exists"):
            await svc.create_user(username="admin", is_admin=True, password="pass12345678")

    async def test_setup_status_required_when_no_users(self) -> None:
        repo = FakeUserRepository()
        assert await repo.get_count() == 0

    async def test_setup_status_not_required_when_users_exist(self) -> None:
        repo = FakeUserRepository()
        enc = FakeEncryption()
        svc = UserService(repo, encryption=enc)

        await svc.create_user(username="admin", is_admin=True, password="pass12345678")
        assert await repo.get_count() == 1

    async def test_setup_email_is_optional(self) -> None:
        repo = FakeUserRepository()
        enc = FakeEncryption()
        svc = UserService(repo, encryption=enc)

        user = await svc.create_user(
            username="admin",
            is_admin=True,
            password="securepass123",
        )
        assert user.email is None

    async def test_setup_admin_can_authenticate(self) -> None:
        repo = FakeUserRepository()
        enc = FakeEncryption()
        svc = UserService(repo, encryption=enc)

        await svc.create_user(
            username="admin",
            is_admin=True,
            password="securepass123",
        )

        user = await svc.authenticate_by_password("admin", "securepass123")
        assert user is not None
        assert user.username == "admin"
        assert user.is_admin is True

    async def test_setup_admin_can_authenticate_by_key(self) -> None:
        repo = FakeUserRepository()
        enc = FakeEncryption()
        svc = UserService(repo, encryption=enc)

        user = await svc.create_user(
            username="admin",
            is_admin=True,
            password="securepass123",
        )
        assert user.id is not None
        _, api_key = await svc.generate_api_key(user.id)

        authed = await svc.authenticate_by_key(api_key)
        assert authed is not None
        assert authed.username == "admin"
