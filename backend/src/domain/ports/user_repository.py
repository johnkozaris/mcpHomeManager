"""Port for user persistence."""

from abc import ABC, abstractmethod
from uuid import UUID

from domain.entities.user import User


class IUserRepository(ABC):
    @abstractmethod
    async def get_all(self) -> list[User]: ...

    @abstractmethod
    async def get_by_id(self, id: UUID) -> User | None: ...

    @abstractmethod
    async def get_by_username(self, username: str) -> User | None: ...

    @abstractmethod
    async def get_by_api_key_hash(self, api_key_hash: str) -> User | None: ...

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    async def get_count(self) -> int: ...

    @abstractmethod
    async def create(self, entity: User) -> User: ...

    @abstractmethod
    async def update(self, entity: User) -> User: ...

    @abstractmethod
    async def delete(self, id: UUID) -> None: ...
