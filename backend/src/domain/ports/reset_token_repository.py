from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID


class IResetTokenRepository(ABC):
    @abstractmethod
    async def create(self, token_hash: str, user_id: UUID, expires_at: datetime) -> None: ...

    @abstractmethod
    async def get_user_id_by_hash(self, token_hash: str) -> tuple[UUID, datetime] | None: ...

    @abstractmethod
    async def delete_by_hash(self, token_hash: str) -> None: ...

    @abstractmethod
    async def delete_for_user(self, user_id: UUID) -> None: ...

    @abstractmethod
    async def delete_expired(self) -> int: ...
