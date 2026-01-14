from litestar import Controller, get
from litestar.datastructures import State
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from domain.entities.service_connection import HealthStatus
from entrypoints.api.schemas import ConfigResponse, HealthResponse
from infrastructure.persistence.smtp_repository import SmtpConfigRepository
from infrastructure.persistence.user_repository import UserRepository
from services.service_manager import ServiceManager


class HealthController(Controller):
    path = "/api/health"

    @get("/", exclude_from_auth=True)
    async def health_check(
        self,
        state: State,
        service_manager: ServiceManager,
    ) -> HealthResponse:
        db_ok = state.get("db_healthy", True)
        services = await service_manager.list_all()
        healthy_count = sum(1 for s in services if s.health_status == HealthStatus.HEALTHY)

        return HealthResponse(
            status="ok" if db_ok else "degraded",
            database="connected" if db_ok else "disconnected",
            mcp_server="running",
            services_healthy=healthy_count,
            services_total=len(services),
        )

    @get("/config", exclude_from_auth=True)
    async def get_config(self, db_session: AsyncSession) -> ConfigResponse:
        """Return non-sensitive configuration for the frontend."""
        user_count = await UserRepository(db_session).get_count()
        smtp_config = await SmtpConfigRepository(db_session).get()

        return ConfigResponse(
            setup_required=user_count == 0,
            smtp_enabled=smtp_config is not None and smtp_config.is_enabled,
            mcp_server_name=settings.mcp_server_name,
            self_mcp_enabled=settings.self_mcp_enabled,
            app_name=settings.app_name,
        )
