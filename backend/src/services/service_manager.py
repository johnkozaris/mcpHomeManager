from typing import Any
from uuid import UUID

import structlog

from domain.entities.service_connection import (
    ServiceConnection,
    ServiceType,
)
from domain.exceptions import ServiceConnectionError, ServiceNotFoundError
from domain.ports.encryption import IEncryptionPort
from domain.ports.service_repository import IServiceRepository
from services.client_factory import ServiceClientFactory

logger = structlog.get_logger()


class ServiceManager:
    """Orchestrates service connection CRUD and health checking."""

    def __init__(
        self,
        repository: IServiceRepository,
        encryption: IEncryptionPort,
        client_factory: ServiceClientFactory,
    ) -> None:
        self._repo = repository
        self._encryption = encryption
        self._client_factory = client_factory

    async def list_all(self) -> list[ServiceConnection]:
        return await self._repo.get_all()

    async def get_by_id(self, service_id: UUID) -> ServiceConnection:
        svc = await self._repo.get_by_id(service_id)
        if svc is None:
            raise ServiceNotFoundError(str(service_id))
        return svc

    async def create_connection(
        self,
        name: str,
        display_name: str,
        service_type: ServiceType,
        base_url: str,
        api_token: str,
        config: dict[str, Any] | None = None,
    ) -> ServiceConnection:
        # Validate URL safety for generic_rest services
        if service_type == ServiceType.GENERIC_REST:
            from infrastructure.clients.generic_rest_client import validate_base_url

            await validate_base_url(base_url)

        encrypted_token = self._encryption.encrypt(api_token.strip())
        entity = ServiceConnection(
            name=name,
            display_name=display_name,
            service_type=service_type,
            base_url=base_url,
            api_token_encrypted=encrypted_token,
            config=config or {},
        )
        return await self._repo.create(entity)

    async def update_connection(
        self,
        service_id: UUID,
        *,
        display_name: str | None = None,
        base_url: str | None = None,
        api_token: str | None = None,
        is_enabled: bool | None = None,
        config: dict[str, Any] | None = None,
    ) -> ServiceConnection:
        entity = await self.get_by_id(service_id)

        # Validate URL safety when updating generic_rest services
        if base_url is not None and entity.service_type == ServiceType.GENERIC_REST:
            from infrastructure.clients.generic_rest_client import validate_base_url

            await validate_base_url(base_url)

        encrypted_token = self._encryption.encrypt(api_token.strip()) if api_token else None
        entity.update_connection(
            display_name=display_name,
            base_url=base_url,
            api_token_encrypted=encrypted_token,
            is_enabled=is_enabled,
            config=config,
        )
        return await self._repo.update(entity)

    async def delete_connection(self, service_id: UUID) -> None:
        await self.get_by_id(service_id)
        await self._repo.delete(service_id)

    async def test_connection(self, service_id: UUID) -> tuple[bool, str]:
        entity = await self.get_by_id(service_id)
        if not entity.api_token_encrypted:
            logger.warning("Service %s has no API token configured", entity.name)
            entity.mark_unhealthy()
            await self._repo.update(entity)
            return False, "No API token configured"
        token = self._encryption.decrypt(entity.api_token_encrypted)
        client = self._client_factory.create(entity.service_type, entity.base_url, token)
        try:
            result = await client.health_check()
            if result:
                entity.mark_healthy()
            else:
                entity.mark_unhealthy()
            await self._repo.update(entity)
            return result, "Connection successful" if result else "Health check returned unhealthy"
        except ServiceConnectionError as exc:
            entity.mark_unhealthy()
            await self._repo.update(entity)
            return False, str(exc)
        except Exception as exc:
            entity.mark_unhealthy()
            await self._repo.update(entity)
            return False, f"Unexpected error: {type(exc).__name__}: {exc}"
        finally:
            try:
                await client.close()
            except Exception:
                logger.warning("Failed to close client for %s", entity.name)
