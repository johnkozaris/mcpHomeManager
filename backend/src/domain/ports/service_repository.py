from abc import ABC, abstractmethod
from uuid import UUID

from domain.entities.service_connection import ServiceConnection


class IServiceRepository(ABC):
    @abstractmethod
    async def get_all(self) -> list[ServiceConnection]: ...

    @abstractmethod
    async def get_by_id(self, id: UUID) -> ServiceConnection | None: ...

    @abstractmethod
    async def get_by_name(self, name: str) -> ServiceConnection | None: ...

    @abstractmethod
    async def get_enabled(self) -> list[ServiceConnection]: ...

    @abstractmethod
    async def create(self, entity: ServiceConnection) -> ServiceConnection: ...

    @abstractmethod
    async def update(self, entity: ServiceConnection) -> ServiceConnection: ...

    @abstractmethod
    async def delete(self, id: UUID) -> None: ...
