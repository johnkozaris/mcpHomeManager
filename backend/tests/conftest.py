"""Shared fixtures for the backend test suite."""

from typing import Any
from uuid import UUID, uuid4

import pytest

from domain.entities.app_definition import AppDefinition
from domain.entities.service_connection import (
    HealthStatus,
    ServiceConnection,
    ServiceType,
)
from domain.entities.tool_definition import ToolDefinition
from domain.entities.user import User
from domain.ports.encryption import IEncryptionPort
from domain.ports.generic_tool_repository import GenericToolRow, IGenericToolRepository
from domain.ports.service_client import IServiceClient
from domain.ports.service_repository import IServiceRepository
from domain.ports.user_repository import IUserRepository
from services.client_factory import ServiceClientFactory

# --- Fake encryption (identity: plaintext == ciphertext) ---


class FakeEncryption(IEncryptionPort):
    def encrypt(self, plaintext: str) -> str:
        return f"enc:{plaintext}"

    def decrypt(self, ciphertext: str) -> str:
        if ciphertext.startswith("enc:"):
            return ciphertext[4:]
        return ciphertext


@pytest.fixture
def fake_encryption() -> FakeEncryption:
    return FakeEncryption()


# --- Fake repository (in-memory) ---


class FakeServiceRepository(IServiceRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, ServiceConnection] = {}

    async def get_all(self) -> list[ServiceConnection]:
        return list(self._store.values())

    async def get_by_id(self, id: UUID) -> ServiceConnection | None:
        return self._store.get(id)

    async def get_by_name(self, name: str) -> ServiceConnection | None:
        return next((s for s in self._store.values() if s.name == name), None)

    async def get_enabled(self) -> list[ServiceConnection]:
        return [s for s in self._store.values() if s.is_enabled]

    async def create(self, entity: ServiceConnection) -> ServiceConnection:
        entity.id = uuid4()
        self._store[entity.id] = entity
        return entity

    async def update(self, entity: ServiceConnection) -> ServiceConnection:
        assert entity.id is not None
        self._store[entity.id] = entity
        return entity

    async def delete(self, id: UUID) -> None:
        self._store.pop(id, None)


@pytest.fixture
def fake_repo() -> FakeServiceRepository:
    return FakeServiceRepository()


# --- Fake service client ---


class FakeServiceClient(IServiceClient):
    def __init__(self, base_url: str = "", api_token: str = "", *, healthy: bool = True) -> None:
        self._healthy = healthy
        self._tools = [
            ToolDefinition(
                name="test_tool",
                service_type=ServiceType.FORGEJO,
                description="A test tool",
            ),
        ]

    async def health_check(self) -> bool:
        return self._healthy

    async def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        return {"result": "ok", "tool": tool_name}

    def get_tool_definitions(self) -> list[ToolDefinition]:
        return self._tools

    async def close(self) -> None:
        pass


@pytest.fixture
def fake_client() -> FakeServiceClient:
    return FakeServiceClient(healthy=True)


# --- Fake app provider client ---


class FakeAppProviderClient(IServiceClient):
    """A fake client that also implements IAppProvider for testing."""

    def __init__(self, base_url: str = "", api_token: str = "") -> None:
        self._tools = [
            ToolDefinition(
                name="test_app_tool",
                service_type=ServiceType.HOME_ASSISTANT,
                description="A tool from an app provider",
            ),
        ]
        self._apps = [
            AppDefinition(
                name="test_app",
                service_type="homeassistant",
                title="Test App",
                description="A test app",
                template_name="test_app.html",
                parameters_schema={"type": "object", "properties": {}},
            ),
        ]
        self._app_data = {"test_key": "test_value"}

    async def health_check(self) -> bool:
        return True

    async def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        return {"result": "ok"}

    def get_tool_definitions(self) -> list[ToolDefinition]:
        return self._tools

    async def close(self) -> None:
        pass

    # IAppProvider methods
    def get_app_definitions(self) -> list[AppDefinition]:
        return self._apps

    async def fetch_app_data(self, app_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        return dict(self._app_data)

    async def handle_app_action(
        self, app_name: str, action: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        return {"action": action, "handled": True}


# --- Fake client factory ---


class FakeClientFactory(ServiceClientFactory):
    def __init__(self, client: IServiceClient) -> None:
        super().__init__()
        self._fixed_client = client

    def create(
        self, service_type: ServiceType, base_url: str, api_token: str, **kwargs: Any
    ) -> IServiceClient:
        return self._fixed_client


class FakeUserRepository(IUserRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, User] = {}

    async def get_all(self) -> list[User]:
        return list(self._store.values())

    async def get_by_id(self, id: UUID) -> User | None:
        return self._store.get(id)

    async def get_by_username(self, username: str) -> User | None:
        return next((u for u in self._store.values() if u.username == username), None)

    async def get_by_api_key_hash(self, api_key_hash: str) -> User | None:
        return next(
            (u for u in self._store.values() if u.api_key_hash == api_key_hash),
            None,
        )

    async def get_by_email(self, email: str) -> User | None:
        return next((u for u in self._store.values() if u.email == email), None)

    async def get_count(self) -> int:
        return len(self._store)

    async def create(self, entity: User) -> User:
        entity.id = uuid4()
        self._store[entity.id] = entity
        return entity

    async def update(self, entity: User) -> User:
        assert entity.id is not None
        self._store[entity.id] = entity
        return entity

    async def delete(self, id: UUID) -> None:
        self._store.pop(id, None)


@pytest.fixture
def fake_user_repo() -> FakeUserRepository:
    return FakeUserRepository()


@pytest.fixture
def fake_client_factory(fake_client: FakeServiceClient) -> FakeClientFactory:
    return FakeClientFactory(fake_client)


# --- Fake generic tool repository (in-memory) ---


class FakeGenericToolRepository(IGenericToolRepository):
    def __init__(self) -> None:
        self._store: dict[tuple[UUID, str], GenericToolRow] = {}

    async def get_by_service_id(self, service_id: UUID) -> list[GenericToolRow]:
        return sorted(
            [row for (sid, _), row in self._store.items() if sid == service_id],
            key=lambda r: r.tool_name,
        )

    async def get_by_name(self, service_id: UUID, tool_name: str) -> GenericToolRow | None:
        return self._store.get((service_id, tool_name))

    async def create(
        self,
        service_id: UUID,
        tool_name: str,
        description: str,
        http_method: str,
        path_template: str,
        params_schema: dict[str, Any],
    ) -> GenericToolRow:
        row = GenericToolRow(
            tool_name=tool_name,
            description=description,
            http_method=http_method.upper(),
            path_template=path_template,
            params_schema=params_schema,
        )
        self._store[(service_id, tool_name)] = row
        return row

    async def update(
        self,
        service_id: UUID,
        tool_name: str,
        *,
        description: str | None = None,
        http_method: str | None = None,
        path_template: str | None = None,
        params_schema: dict[str, Any] | None = None,
    ) -> GenericToolRow | None:
        key = (service_id, tool_name)
        existing = self._store.get(key)
        if existing is None:
            return None

        self._store[key] = GenericToolRow(
            tool_name=existing.tool_name,
            description=description if description is not None else existing.description,
            http_method=http_method.upper() if http_method is not None else existing.http_method,
            path_template=path_template if path_template is not None else existing.path_template,
            params_schema=params_schema if params_schema is not None else existing.params_schema,
        )
        return self._store[key]

    async def delete(self, service_id: UUID, tool_name: str) -> bool:
        key = (service_id, tool_name)
        if key in self._store:
            del self._store[key]
            return True
        return False


@pytest.fixture
def fake_generic_tool_repo() -> FakeGenericToolRepository:
    return FakeGenericToolRepository()


# --- Helper to build a ServiceConnection ---


def make_service(
    *,
    name: str = "forgejo",
    display_name: str = "Forgejo",
    service_type: ServiceType = ServiceType.FORGEJO,
    base_url: str = "http://forgejo:3000",
    api_token_encrypted: str = "enc:test-token",
    is_enabled: bool = True,
    health_status: HealthStatus = HealthStatus.UNKNOWN,
    id: UUID | None = None,
) -> ServiceConnection:
    return ServiceConnection(
        name=name,
        display_name=display_name,
        service_type=service_type,
        base_url=base_url,
        api_token_encrypted=api_token_encrypted,
        is_enabled=is_enabled,
        health_status=health_status,
        id=id or uuid4(),
    )
