"""Tests for the user service (multi-user mode)."""

import pytest

from conftest import FakeUserRepository
from services.user_service import UserService


@pytest.fixture
def user_service(fake_user_repo: FakeUserRepository) -> UserService:
    return UserService(fake_user_repo)


class TestUserService:
    async def test_create_user(self, user_service: UserService):
        user = await user_service.create_user("alice")
        assert user.username == "alice"
        assert user.api_key_hash is None  # No API key on creation

    async def test_generate_api_key(self, user_service: UserService):
        user = await user_service.create_user("alice")
        assert user.id is not None
        updated, api_key = await user_service.generate_api_key(user.id)
        assert api_key.startswith("mcp_")
        assert len(api_key) > 20
        assert updated.api_key_hash != ""
        assert updated.api_key_hash is not None
        assert api_key not in updated.api_key_hash  # stored as hash
        assert len(updated.api_key_hash) == 64  # SHA-256 hex

    async def test_create_duplicate_username_raises(self, user_service: UserService):
        await user_service.create_user("alice")
        with pytest.raises(ValueError, match="already exists"):
            await user_service.create_user("alice")

    async def test_authenticate_by_key(self, user_service: UserService):
        user = await user_service.create_user("alice")
        assert user.id is not None
        _, api_key = await user_service.generate_api_key(user.id)
        found = await user_service.authenticate_by_key(api_key)
        assert found is not None
        assert found.username == "alice"

    async def test_authenticate_wrong_key(self, user_service: UserService):
        await user_service.create_user("alice")
        found = await user_service.authenticate_by_key("wrong-key")
        assert found is None

    async def test_revoke_api_key(self, user_service: UserService):
        user = await user_service.create_user("alice")
        assert user.id is not None
        _, api_key = await user_service.generate_api_key(user.id)
        # Key works before revoke
        assert await user_service.authenticate_by_key(api_key) is not None
        await user_service.revoke_api_key(user.id)
        # Key no longer works after revoke
        assert await user_service.authenticate_by_key(api_key) is None

    async def test_delete_user(self, user_service: UserService):
        user = await user_service.create_user("temp")
        assert user.id is not None
        await user_service.delete_user(user.id)
        found = await user_service.get_by_id(user.id)
        assert found is None
