"""SQLAlchemy implementation of the user repository."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.user import User
from domain.ports.user_repository import IUserRepository
from infrastructure.persistence.orm_models import UserModel


class UserRepository(IUserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_all(self) -> list[User]:
        result = await self._session.execute(select(UserModel).order_by(UserModel.username))
        return [self._to_entity(row) for row in result.scalars().all()]

    async def get_by_id(self, id: UUID) -> User | None:
        result = await self._session.execute(select(UserModel).where(UserModel.id == id))
        row = result.scalar_one_or_none()
        return self._to_entity(row) if row else None

    async def get_by_username(self, username: str) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.username == username)
        )
        row = result.scalar_one_or_none()
        return self._to_entity(row) if row else None

    async def get_by_api_key_hash(self, api_key_hash: str) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.api_key_hash == api_key_hash)
        )
        row = result.scalar_one_or_none()
        return self._to_entity(row) if row else None

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(UserModel).where(UserModel.email == email))
        row = result.scalar_one_or_none()
        return self._to_entity(row) if row else None

    async def get_count(self) -> int:
        result = await self._session.execute(select(func.count()).select_from(UserModel))
        return result.scalar_one()

    async def create(self, entity: User) -> User:
        model = UserModel(
            username=entity.username,
            email=entity.email,
            api_key_hash=entity.api_key_hash,
            is_admin=entity.is_admin,
            self_mcp_enabled=entity.self_mcp_enabled,
            allowed_service_ids=[str(sid) for sid in entity.allowed_service_ids],
            password_hash=entity.password_hash,
            encrypted_api_key=entity.encrypted_api_key,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def update(self, entity: User) -> User:
        result = await self._session.execute(select(UserModel).where(UserModel.id == entity.id))
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"User not found: {entity.id}")
        model.username = entity.username
        model.email = entity.email
        model.api_key_hash = entity.api_key_hash
        model.is_admin = entity.is_admin
        model.self_mcp_enabled = entity.self_mcp_enabled
        model.allowed_service_ids = [str(sid) for sid in entity.allowed_service_ids]
        model.password_hash = entity.password_hash
        model.encrypted_api_key = entity.encrypted_api_key
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def delete(self, id: UUID) -> None:
        result = await self._session.execute(select(UserModel).where(UserModel.id == id))
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"User not found: {id}")
        await self._session.delete(model)
        await self._session.flush()

    @staticmethod
    def _to_entity(model: UserModel) -> User:
        return User(
            id=model.id,
            username=model.username,
            email=model.email,
            api_key_hash=model.api_key_hash,
            is_admin=model.is_admin,
            self_mcp_enabled=model.self_mcp_enabled,
            allowed_service_ids=[UUID(sid) for sid in (model.allowed_service_ids or [])],
            password_hash=model.password_hash,
            encrypted_api_key=model.encrypted_api_key,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
