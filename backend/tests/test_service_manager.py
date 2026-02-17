"""Tests for ServiceManager — the core orchestration layer."""

from uuid import uuid4

import pytest
from tests.conftest import (
    FakeClientFactory,
    FakeEncryption,
    FakeServiceClient,
    FakeServiceRepository,
    make_service,
)

from domain.entities.service_connection import HealthStatus, ServiceType
from domain.exceptions import ServiceNotFoundError
from services.service_manager import ServiceManager


class TestServiceManagerCRUD:
    @pytest.fixture
    def manager(
        self,
        fake_repo: FakeServiceRepository,
        fake_encryption: FakeEncryption,
        fake_client_factory: FakeClientFactory,
    ) -> ServiceManager:
        return ServiceManager(fake_repo, fake_encryption, fake_client_factory)

    async def test_create_connection(
        self,
        manager: ServiceManager,
        fake_repo: FakeServiceRepository,
    ) -> None:
        svc = await manager.create_connection(
            name="forgejo",
            display_name="Forgejo",
            service_type=ServiceType.FORGEJO,
            base_url="http://forgejo:3000",
            api_token="my-token",
        )
        assert svc.id is not None
        assert svc.name == "forgejo"
        assert svc.api_token_encrypted == "enc:my-token"  # FakeEncryption prefixes with "enc:"
        assert len(await fake_repo.get_all()) == 1

    async def test_list_all(
        self,
        manager: ServiceManager,
        fake_repo: FakeServiceRepository,
    ) -> None:
        await fake_repo.create(make_service(name="svc1"))
        await fake_repo.create(make_service(name="svc2"))
        result = await manager.list_all()
        assert len(result) == 2

    async def test_get_by_id_found(
        self,
        manager: ServiceManager,
        fake_repo: FakeServiceRepository,
    ) -> None:
        svc = await fake_repo.create(make_service())
        assert svc.id is not None
        result = await manager.get_by_id(svc.id)
        assert result.name == svc.name

    async def test_get_by_id_not_found(self, manager: ServiceManager) -> None:
        with pytest.raises(ServiceNotFoundError):
            await manager.get_by_id(uuid4())

    async def test_update_connection(
        self,
        manager: ServiceManager,
        fake_repo: FakeServiceRepository,
    ) -> None:
        svc = await fake_repo.create(make_service(display_name="Old"))
        assert svc.id is not None
        updated = await manager.update_connection(svc.id, display_name="New")
        assert updated.display_name == "New"

    async def test_update_connection_with_new_token(
        self,
        manager: ServiceManager,
        fake_repo: FakeServiceRepository,
    ) -> None:
        svc = await fake_repo.create(make_service())
        assert svc.id is not None
        updated = await manager.update_connection(svc.id, api_token="new-token")
        assert updated.api_token_encrypted == "enc:new-token"

    async def test_delete_connection(
        self,
        manager: ServiceManager,
        fake_repo: FakeServiceRepository,
    ) -> None:
        svc = await fake_repo.create(make_service())
        assert svc.id is not None
        await manager.delete_connection(svc.id)
        assert len(await fake_repo.get_all()) == 0

    async def test_delete_nonexistent_raises(self, manager: ServiceManager) -> None:
        with pytest.raises(ServiceNotFoundError):
            await manager.delete_connection(uuid4())


class TestServiceManagerHealthCheck:
    async def test_test_connection_healthy(
        self,
        fake_repo: FakeServiceRepository,
        fake_encryption: FakeEncryption,
    ) -> None:
        client = FakeServiceClient(healthy=True)
        factory = FakeClientFactory(client)
        manager = ServiceManager(fake_repo, fake_encryption, factory)

        svc = await fake_repo.create(make_service())
        assert svc.id is not None
        success, message = await manager.test_connection(svc.id)
        assert success is True
        assert message == "Connection successful"

        updated = await fake_repo.get_by_id(svc.id)
        assert updated is not None
        assert updated.health_status == HealthStatus.HEALTHY

    async def test_test_connection_unhealthy(
        self,
        fake_repo: FakeServiceRepository,
        fake_encryption: FakeEncryption,
    ) -> None:
        client = FakeServiceClient(healthy=False)
        factory = FakeClientFactory(client)
        manager = ServiceManager(fake_repo, fake_encryption, factory)

        svc = await fake_repo.create(make_service())
        assert svc.id is not None
        success, message = await manager.test_connection(svc.id)
        assert success is False
        assert "unhealthy" in message.lower()

        updated = await fake_repo.get_by_id(svc.id)
        assert updated is not None
        assert updated.health_status == HealthStatus.UNHEALTHY

    async def test_test_connection_empty_token_returns_false(
        self,
        fake_repo: FakeServiceRepository,
        fake_encryption: FakeEncryption,
        fake_client_factory: FakeClientFactory,
    ) -> None:
        """Services with empty api_token_encrypted should fail gracefully, not crash."""
        manager = ServiceManager(fake_repo, fake_encryption, fake_client_factory)
        svc = await fake_repo.create(make_service(api_token_encrypted=""))
        assert svc.id is not None
        success, message = await manager.test_connection(svc.id)
        assert success is False
        assert "No API token" in message

        updated = await fake_repo.get_by_id(svc.id)
        assert updated is not None
        assert updated.health_status == HealthStatus.UNHEALTHY

    async def test_test_connection_not_found(
        self,
        fake_repo: FakeServiceRepository,
        fake_encryption: FakeEncryption,
        fake_client_factory: FakeClientFactory,
    ) -> None:
        manager = ServiceManager(fake_repo, fake_encryption, fake_client_factory)
        with pytest.raises(ServiceNotFoundError):
            await manager.test_connection(uuid4())
