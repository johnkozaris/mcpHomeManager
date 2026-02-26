"""Tests for key rotation service."""

from uuid import uuid4

import pytest
from cryptography.fernet import Fernet

from conftest import FakeEncryption, FakeServiceRepository, FakeUserRepository, make_service
from domain.entities.user import User
from domain.exceptions import EncryptionError
from infrastructure.encryption.fernet_encryption import FernetEncryption
from services.key_rotation import KeyRotationService


@pytest.fixture
def old_key() -> str:
    return Fernet.generate_key().decode()


@pytest.fixture
def new_key() -> str:
    return Fernet.generate_key().decode()


@pytest.fixture
def old_enc(old_key: str) -> FernetEncryption:
    return FernetEncryption(old_key)


@pytest.fixture
def new_enc(new_key: str) -> FernetEncryption:
    return FernetEncryption(new_key)


def _make_username(prefix: str = "user") -> str:
    return f"{prefix}-{uuid4().hex[:8]}"


async def test_rotate_service_tokens(old_enc: FernetEncryption, new_enc: FernetEncryption) -> None:
    svc_repo = FakeServiceRepository()
    user_repo = FakeUserRepository()

    encrypted = old_enc.encrypt("my-secret-token")
    svc = make_service(api_token_encrypted=encrypted)
    await svc_repo.create(svc)

    rotation = KeyRotationService(svc_repo, user_repo, old_enc, new_enc)
    summary = await rotation.rotate()

    assert summary == {"services": 1, "users": 0, "smtp": 0}

    updated = (await svc_repo.get_all())[0]
    assert new_enc.decrypt(updated.api_token_encrypted) == "my-secret-token"

    with pytest.raises(EncryptionError):
        old_enc.decrypt(updated.api_token_encrypted)


async def test_rotate_user_encrypted_api_keys(
    old_enc: FernetEncryption,
    new_enc: FernetEncryption,
) -> None:
    svc_repo = FakeServiceRepository()
    user_repo = FakeUserRepository()

    encrypted_key = old_enc.encrypt("mcp_user_api_key_here")
    user = User(username=_make_username(), encrypted_api_key=encrypted_key, id=uuid4())
    await user_repo.create(user)

    rotation = KeyRotationService(svc_repo, user_repo, old_enc, new_enc)
    summary = await rotation.rotate()

    assert summary == {"services": 0, "users": 1, "smtp": 0}

    updated = (await user_repo.get_all())[0]
    assert updated.encrypted_api_key is not None
    assert new_enc.decrypt(updated.encrypted_api_key) == "mcp_user_api_key_here"


async def test_rotate_skips_empty_tokens(
    old_enc: FernetEncryption,
    new_enc: FernetEncryption,
) -> None:
    svc_repo = FakeServiceRepository()
    user_repo = FakeUserRepository()

    svc = make_service(api_token_encrypted="")
    await svc_repo.create(svc)

    user = User(username=_make_username(), encrypted_api_key=None, id=uuid4())
    await user_repo.create(user)

    rotation = KeyRotationService(svc_repo, user_repo, old_enc, new_enc)
    summary = await rotation.rotate()

    assert summary == {"services": 0, "users": 0, "smtp": 0}


async def test_rotate_multiple_records(
    old_enc: FernetEncryption,
    new_enc: FernetEncryption,
) -> None:
    svc_repo = FakeServiceRepository()
    user_repo = FakeUserRepository()

    for i in range(5):
        svc = make_service(
            name=f"svc-{i}",
            api_token_encrypted=old_enc.encrypt(f"token-{i}"),
        )
        await svc_repo.create(svc)

    for i in range(3):
        user = User(
            username=f"user-{i}",
            encrypted_api_key=old_enc.encrypt(f"key-{i}"),
            id=uuid4(),
        )
        await user_repo.create(user)

    rotation = KeyRotationService(svc_repo, user_repo, old_enc, new_enc)
    summary = await rotation.rotate()

    assert summary == {"services": 5, "users": 3, "smtp": 0}

    for svc in await svc_repo.get_all():
        idx = svc.name.split("-")[1]
        assert new_enc.decrypt(svc.api_token_encrypted) == f"token-{idx}"

    for user in await user_repo.get_all():
        idx = user.username.split("-")[1]
        assert user.encrypted_api_key is not None
        assert new_enc.decrypt(user.encrypted_api_key) == f"key-{idx}"


async def test_rotate_with_fake_encryption() -> None:
    """Verify the service works through the IEncryptionPort interface."""
    old = FakeEncryption()
    new = FakeEncryption()

    svc_repo = FakeServiceRepository()
    user_repo = FakeUserRepository()

    svc = make_service(api_token_encrypted="enc:token123")
    await svc_repo.create(svc)

    rotation = KeyRotationService(svc_repo, user_repo, old, new)
    summary = await rotation.rotate()

    assert summary == {"services": 1, "users": 0, "smtp": 0}
    updated = (await svc_repo.get_all())[0]
    # FakeEncryption: decrypt("enc:token123") → "token123", encrypt("token123") → "enc:token123"
    assert updated.api_token_encrypted == "enc:token123"
