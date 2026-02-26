"""Tests for ToolRegistry app discovery (ActiveApp tracking)."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from conftest import FakeAppProviderClient, FakeEncryption, FakeServiceClient, make_service
from domain.ports.app_provider import IAppProvider
from services.tool_registry import ActiveApp, ToolRegistry


@pytest.fixture
def mock_session_factory():
    """Create a mock session factory that yields mock sessions."""
    session = MagicMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)

    factory = MagicMock(return_value=session)
    return factory


def _make_registry(
    mock_session_factory, factory, encryption, mock_svc_repo, mock_tool_repo, mock_generic_repo
):
    """Helper to create a ToolRegistry with injected repo factories."""
    return ToolRegistry(
        session_factory=mock_session_factory,
        encryption=encryption,
        client_factory=factory,
        service_repo_factory=lambda _session: mock_svc_repo,
        tool_repo_factory=lambda _session: mock_tool_repo,
        generic_tool_repo_factory=lambda _session: mock_generic_repo,
    )


class TestToolRegistryApps:
    async def test_app_provider_client_discovered(self, mock_session_factory):
        """When a client implements IAppProvider, its apps appear in active_apps."""
        fake_client = FakeAppProviderClient()
        assert isinstance(fake_client, IAppProvider)

        svc = make_service(name="ha", is_enabled=True)

        # Mock the repos
        mock_svc_repo = AsyncMock()
        mock_svc_repo.get_enabled.return_value = [svc]
        mock_tool_repo = AsyncMock()
        mock_tool_repo.get_by_service_id.return_value = {}
        mock_generic_repo = AsyncMock()

        factory = MagicMock()
        factory.create.return_value = fake_client
        encryption = FakeEncryption()

        registry = _make_registry(
            mock_session_factory,
            factory,
            encryption,
            mock_svc_repo,
            mock_tool_repo,
            mock_generic_repo,
        )

        await registry.build()

        # Should have discovered the app
        apps = registry.active_apps
        assert len(apps) == 1
        assert "test_app" in apps
        assert isinstance(apps["test_app"], ActiveApp)
        assert apps["test_app"].definition.name == "test_app"
        assert apps["test_app"].service_name == "ha"

    async def test_non_provider_client_has_no_apps(self, mock_session_factory):
        """A regular client that doesn't implement IAppProvider produces no apps."""
        fake_client = FakeServiceClient()
        assert not isinstance(fake_client, IAppProvider)

        svc = make_service(name="plain", is_enabled=True)

        mock_svc_repo = AsyncMock()
        mock_svc_repo.get_enabled.return_value = [svc]
        mock_tool_repo = AsyncMock()
        mock_tool_repo.get_by_service_id.return_value = {}
        mock_generic_repo = AsyncMock()

        factory = MagicMock()
        factory.create.return_value = fake_client
        encryption = FakeEncryption()

        registry = _make_registry(
            mock_session_factory,
            factory,
            encryption,
            mock_svc_repo,
            mock_tool_repo,
            mock_generic_repo,
        )

        await registry.build()

        assert len(registry.active_apps) == 0

    async def test_cleanup_clears_apps(self, mock_session_factory):
        """cleanup() should also clear active_apps."""
        fake_client = FakeAppProviderClient()
        svc = make_service(name="ha", is_enabled=True)

        mock_svc_repo = AsyncMock()
        mock_svc_repo.get_enabled.return_value = [svc]
        mock_tool_repo = AsyncMock()
        mock_tool_repo.get_by_service_id.return_value = {}
        mock_generic_repo = AsyncMock()

        factory = MagicMock()
        factory.create.return_value = fake_client
        encryption = FakeEncryption()

        registry = _make_registry(
            mock_session_factory,
            factory,
            encryption,
            mock_svc_repo,
            mock_tool_repo,
            mock_generic_repo,
        )

        await registry.build()

        assert len(registry.active_apps) > 0

        await registry.cleanup()
        assert len(registry.active_apps) == 0

    def test_active_apps_returns_copy(self, mock_session_factory):
        """active_apps should return a dict copy (snapshot pattern)."""
        encryption = FakeEncryption()
        factory = MagicMock()

        registry = ToolRegistry(
            session_factory=mock_session_factory,
            encryption=encryption,
            client_factory=factory,
        )

        snap1 = registry.active_apps
        snap2 = registry.active_apps
        assert snap1 is not snap2  # Different dict objects
