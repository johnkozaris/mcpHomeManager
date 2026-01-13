"""Composition root — wires all dependencies and creates the Litestar app."""

# ruff: noqa: E402

import warnings

# Litestar 2.20 internally imports pydantic.v1 for dual v1/v2 support.
# On Python 3.14 + Pydantic 2.x this triggers a harmless UserWarning.
# Our code is 100% Pydantic v2 — suppress before any Litestar imports.
warnings.filterwarnings(
    "ignore",
    message="Core Pydantic V1 functionality",
    category=UserWarning,
)

import asyncio
import contextlib
import importlib
from collections.abc import AsyncGenerator
from pathlib import Path

import structlog
from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig, SQLAlchemyPlugin
from litestar import Litestar, Request, Response, asgi
from litestar.datastructures import State
from litestar.di import Provide
from litestar.middleware.base import DefineMiddleware
from litestar.middleware.rate_limit import RateLimitConfig
from litestar.plugins.prometheus import PrometheusConfig, PrometheusController
from litestar.plugins.structlog import StructlogConfig, StructlogPlugin
from litestar.static_files import create_static_files_router
from litestar.types import Receive, Scope, Send
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import settings
from domain.exceptions import (
    EncryptionError,
    ServiceConnectionError,
    ServiceNotFoundError,
    ToolExecutionError,
    UnsupportedServiceError,
)
from domain.ports.encryption import IEncryptionPort
from entrypoints.api.admin import AdminController
from entrypoints.api.audit import AuditController
from entrypoints.api.auth import AuthController
from entrypoints.api.discovery import DiscoveryController
from entrypoints.api.health import HealthController
from entrypoints.api.services import ServiceController
from entrypoints.api.setup import SetupController
from entrypoints.api.tools import ToolController
from entrypoints.api.users import UserController
from entrypoints.mcp.server import MCPServerFactory
from infrastructure.encryption.fernet_encryption import FernetEncryption
from infrastructure.persistence.audit_repository import AuditRepository
from infrastructure.persistence.generic_tool_repository import GenericToolDefinitionRepository
from infrastructure.persistence.service_repository import ServiceRepository
from infrastructure.persistence.tool_repository import ToolPermissionRepository
from security.api_auth_middleware import ApiAuthMiddleware
from security.mcp_auth import verify_mcp_request
from services.audit_service import AuditService
from services.client_factory import ServiceClientFactory
from services.health_service import HealthCheckRunner
from services.service_manager import ServiceManager
from services.tool_registry import ToolRegistry

logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# Domain → HTTP exception handlers
# ---------------------------------------------------------------------------


def _not_found_handler(_: Request, exc: ServiceNotFoundError) -> Response:
    return Response(content={"detail": f"Service not found: {exc.identifier}"}, status_code=404)


def _client_error_handler(
    _: Request, exc: ServiceConnectionError | UnsupportedServiceError | ToolExecutionError
) -> Response:
    # Log full detail for operators, return sanitized message to client
    logger.warning("domain_client_error", error=str(exc), exc_type=type(exc).__name__)
    match exc:
        case ServiceConnectionError():
            detail = f"Connection to '{exc.service_name}' failed"
        case UnsupportedServiceError():
            detail = f"Unsupported service type: {exc.service_type}"
        case ToolExecutionError():
            detail = f"Tool '{exc.tool_name}' failed"
        case _:
            detail = "Request failed"
    return Response(content={"detail": detail}, status_code=400)


def _encryption_error_handler(_: Request, exc: EncryptionError) -> Response:
    logger.error("encryption_error", error=str(exc))
    return Response(content={"detail": "Internal error"}, status_code=500)


# ---------------------------------------------------------------------------
# DI Providers — access singletons from app.state
# ---------------------------------------------------------------------------


async def provide_encryption(state: State) -> IEncryptionPort:
    return state.encryption


async def provide_client_factory(state: State) -> ServiceClientFactory:
    return state.client_factory


async def provide_tool_registry(state: State) -> ToolRegistry:
    return state.tool_registry


async def provide_audit_service(db_session: AsyncSession) -> AuditService:
    return AuditService(repository=AuditRepository(db_session))


async def provide_service_manager(
    db_session: AsyncSession,
    state: State,
) -> ServiceManager:
    return ServiceManager(
        repository=ServiceRepository(db_session),
        encryption=state.encryption,
        client_factory=state.client_factory,
    )


# ---------------------------------------------------------------------------
# Lifespan — startup / shutdown
# ---------------------------------------------------------------------------


@contextlib.asynccontextmanager
async def app_lifespan(app: Litestar) -> AsyncGenerator[None]:
    logger.info("Starting %s...", settings.app_name)

    if not settings.encryption_key:
        raise RuntimeError(
            "ENCRYPTION_KEY is required. Set it in .env or let the Docker entrypoint generate it."
        )

    try:
        encryption = FernetEncryption(settings.encryption_key)
    except (ValueError, Exception) as e:
        raise RuntimeError(
            f"Invalid ENCRYPTION_KEY: {e}. "
            "If using Docker, check /app/data/encryption_key for corruption. "
            'Generate a new key with: python -c "from cryptography.fernet import Fernet; '
            'print(Fernet.generate_key().decode())"'
        ) from e

    if "REPLACE_WITH_POSTGRES_PASSWORD" in settings.database_url:
        logger.warning(
            "Using default database password 'REPLACE_WITH_POSTGRES_PASSWORD'. "
            "Set POSTGRES_PASSWORD in .env for production deployments."
        )

    # Build singletons and store in app.state
    client_factory = ServiceClientFactory()

    # Create engine for background use (separate from Litestar's request-scoped sessions)
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    # Create all tables from ORM models (no Alembic migrations needed for fresh installs)
    from advanced_alchemy.base import UUIDAuditBase

    importlib.import_module("infrastructure.persistence.orm_models")

    async with engine.begin() as conn:
        await conn.run_sync(UUIDAuditBase.metadata.create_all)

    # Build tool registry and MCP server
    tool_registry = ToolRegistry(
        session_factory=session_factory,
        encryption=encryption,
        client_factory=client_factory,
        service_repo_factory=ServiceRepository,
        tool_repo_factory=ToolPermissionRepository,
        generic_tool_repo_factory=GenericToolDefinitionRepository,
    )
    mcp_factory = MCPServerFactory(
        tool_registry=tool_registry,
        session_factory=session_factory,
        encryption=encryption,
        client_factory=client_factory,
    )
    tool_registry.set_on_rebuild(mcp_factory.sync_tools)
    await mcp_factory.initialize()

    # Store in app.state for DI providers and ASGI handler
    app.state.encryption = encryption
    app.state.client_factory = client_factory
    app.state.tool_registry = tool_registry
    app.state.mcp_factory = mcp_factory
    app.state.session_factory = session_factory
    app.state.db_healthy = True

    # Ensure ASGI app is built (lazily creates session manager)
    mcp_factory.get_asgi_app()

    # Background health check
    health_runner = HealthCheckRunner(
        session_factory,
        encryption,
        client_factory,
        interval_seconds=settings.health_check_interval_seconds,
        service_repo_factory=ServiceRepository,
    )
    app.state.health_runner = health_runner
    health_task = asyncio.create_task(health_runner.run_forever())

    async with mcp_factory.session_manager.run():
        logger.info("%s is ready", settings.app_name)
        try:
            yield
        finally:
            health_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await health_task

    logger.info("Shutting down %s...", settings.app_name)
    await tool_registry.cleanup()
    await engine.dispose()


# ---------------------------------------------------------------------------
# MCP ASGI mount
# ---------------------------------------------------------------------------


@asgi("/mcp", is_mount=True, copy_scope=False)
async def mcp_asgi_handler(scope: Scope, receive: Receive, send: Send) -> None:
    """Forward /mcp/* to the MCP SDK's Streamable HTTP app."""
    app: Litestar = scope["litestar_app"]
    mcp_factory: MCPServerFactory = app.state.mcp_factory

    if not await verify_mcp_request(scope, receive, send):
        return

    # Pass authenticated user for per-tool authorization (contextvars — request-scoped)
    user = scope.get("state", {}).get("authenticated_user")
    MCPServerFactory.set_current_user(user)
    try:
        asgi_app = mcp_factory.get_asgi_app()
        await asgi_app(scope, receive, send)
    finally:
        MCPServerFactory.set_current_user(None)


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------


def create_app() -> Litestar:
    db_config = SQLAlchemyAsyncConfig(
        connection_string=settings.database_url,
        create_all=False,  # Tables created in lifespan before registry build
    )
    db_plugin = SQLAlchemyPlugin(config=db_config)

    # Litestar's built-in StructlogPlugin — auto-configures structlog + stdlib,
    # handles TTY detection, coloured dev output, JSON in prod, request middleware.
    structlog_plugin = StructlogPlugin(
        config=StructlogConfig(
            enable_middleware_logging=settings.debug,
        ),
    )

    # Litestar's built-in Prometheus plugin — auto-instruments HTTP requests
    # with request count, duration histograms, and exposes /metrics endpoint.
    prometheus_config = PrometheusConfig(
        app_name="mcp_home",
        prefix="mcp_home",
        exclude=["/mcp/*"],  # MCP endpoint has its own metrics
    )

    rate_limit_config = RateLimitConfig(
        rate_limit=("minute", 120),
        exclude=["/metrics", "/api/health/config", "/api/setup/status"],
    )

    # Serve built frontend as SPA — backend serves everything on one port.
    # In production, frontend/dist is copied into the container at build time.
    # In dev, use `pnpm dev` which proxies /api and /mcp to :8000.
    static_dir = Path(__file__).resolve().parent.parent / "static"
    route_handlers: list = [
        AdminController,
        SetupController,
        ServiceController,
        ToolController,
        AuditController,
        HealthController,
        PrometheusController,
        DiscoveryController,
        UserController,
        AuthController,
        mcp_asgi_handler,
    ]
    if static_dir.is_dir():
        route_handlers.append(
            create_static_files_router(
                path="/",
                directories=[static_dir],
                html_mode=True,
                opt={"exclude_from_auth": True},
            )
        )
        logger.info("Serving frontend from %s", static_dir)

    return Litestar(
        debug=settings.debug,
        route_handlers=route_handlers,
        plugins=[db_plugin, structlog_plugin],
        middleware=[
            prometheus_config.middleware,
            rate_limit_config.middleware,
            DefineMiddleware(ApiAuthMiddleware, exclude=["/mcp", "/metrics"]),
        ],
        dependencies={
            "encryption": Provide(provide_encryption),
            "client_factory": Provide(provide_client_factory),
            "tool_registry": Provide(provide_tool_registry),
            "audit_service": Provide(provide_audit_service),
            "service_manager": Provide(provide_service_manager),
        },
        exception_handlers={
            ServiceNotFoundError: _not_found_handler,
            ServiceConnectionError: _client_error_handler,
            UnsupportedServiceError: _client_error_handler,
            ToolExecutionError: _client_error_handler,
            EncryptionError: _encryption_error_handler,
        },
        lifespan=[app_lifespan],
        openapi_config=None,
    )


app = create_app()
