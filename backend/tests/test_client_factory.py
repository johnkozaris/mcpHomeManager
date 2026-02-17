"""Tests for ServiceClientFactory."""

import pytest

from domain.entities.service_connection import ServiceType
from services.client_factory import ServiceClientFactory


class TestServiceClientFactory:
    @pytest.fixture
    def factory(self) -> ServiceClientFactory:
        return ServiceClientFactory()

    def test_all_builtin_service_types_supported(self, factory: ServiceClientFactory) -> None:
        """Every built-in ServiceType enum value should have a registered client."""
        for stype in ServiceType:
            client = factory.create(stype, "http://test:8080", "test-token")
            assert client is not None

    def test_creates_correct_client_type(self, factory: ServiceClientFactory) -> None:
        from infrastructure.clients.forgejo_client import ForgejoClient
        from infrastructure.clients.paperless_client import PaperlessClient

        assert isinstance(factory.create(ServiceType.FORGEJO, "http://f", "t"), ForgejoClient)
        assert isinstance(factory.create(ServiceType.PAPERLESS, "http://p", "t"), PaperlessClient)

    def test_each_call_creates_new_instance(self, factory: ServiceClientFactory) -> None:
        c1 = factory.create(ServiceType.FORGEJO, "http://f", "t")
        c2 = factory.create(ServiceType.FORGEJO, "http://f", "t")
        assert c1 is not c2
