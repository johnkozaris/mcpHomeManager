from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.service_connection import (
    HealthStatus,
    ServiceConnection,
    ServiceType,
)
from domain.ports.service_repository import IServiceRepository
from infrastructure.persistence.orm_models import ServiceConnectionModel


class ServiceRepository(IServiceRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_all(self) -> list[ServiceConnection]:
        result = await self._session.execute(
            select(ServiceConnectionModel).order_by(ServiceConnectionModel.name)
        )
        return [self._to_entity(row) for row in result.scalars().all()]

    async def get_by_id(self, id: UUID) -> ServiceConnection | None:
        result = await self._session.execute(
            select(ServiceConnectionModel).where(ServiceConnectionModel.id == id)
        )
        row = result.scalar_one_or_none()
        return self._to_entity(row) if row else None

    async def get_by_name(self, name: str) -> ServiceConnection | None:
        result = await self._session.execute(
            select(ServiceConnectionModel).where(ServiceConnectionModel.name == name)
        )
        row = result.scalar_one_or_none()
        return self._to_entity(row) if row else None

    async def get_enabled(self) -> list[ServiceConnection]:
        result = await self._session.execute(
            select(ServiceConnectionModel)
            .where(ServiceConnectionModel.is_enabled.is_(True))
            .order_by(ServiceConnectionModel.name)
        )
        return [self._to_entity(row) for row in result.scalars().all()]

    async def create(self, entity: ServiceConnection) -> ServiceConnection:
        model = self._to_model(entity)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def update(self, entity: ServiceConnection) -> ServiceConnection:
        result = await self._session.execute(
            select(ServiceConnectionModel).where(ServiceConnectionModel.id == entity.id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"Service not found: {entity.id}")
        model.name = entity.name
        model.display_name = entity.display_name
        model.service_type = entity.service_type.value
        model.base_url = entity.base_url
        model.api_token_encrypted = entity.api_token_encrypted
        model.is_enabled = entity.is_enabled
        model.health_status = entity.health_status.value
        model.last_health_check = entity.last_health_check
        model.config_json = entity.config
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def delete(self, id: UUID) -> None:
        result = await self._session.execute(
            select(ServiceConnectionModel).where(ServiceConnectionModel.id == id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"Service not found: {id}")
        await self._session.delete(model)
        await self._session.flush()

    @staticmethod
    def _to_entity(model: ServiceConnectionModel) -> ServiceConnection:
        return ServiceConnection(
            id=model.id,
            name=model.name,
            display_name=model.display_name,
            service_type=ServiceType(model.service_type),
            base_url=model.base_url,
            api_token_encrypted=model.api_token_encrypted,
            is_enabled=model.is_enabled,
            health_status=HealthStatus(model.health_status),
            last_health_check=model.last_health_check,
            config=model.config_json or {},
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _to_model(entity: ServiceConnection) -> ServiceConnectionModel:
        return ServiceConnectionModel(
            name=entity.name,
            display_name=entity.display_name,
            service_type=entity.service_type.value,
            base_url=entity.base_url,
            api_token_encrypted=entity.api_token_encrypted,
            is_enabled=entity.is_enabled,
            health_status=entity.health_status.value,
            last_health_check=entity.last_health_check,
            config_json=entity.config,
        )
