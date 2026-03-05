import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, replace
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from domain.entities.app_definition import AppDefinition
from domain.entities.generic_tool_spec import GenericToolSpec
from domain.entities.service_connection import ServiceType
from domain.entities.tool_definition import ToolDefinition
from domain.ports.app_provider import IAppProvider
from domain.ports.encryption import IEncryptionPort
from domain.ports.generic_tool_repository import IGenericToolRepository
from domain.ports.service_client import IServiceClient
from domain.ports.service_repository import IServiceRepository
from domain.ports.tool_repository import IToolPermissionRepository
from services.client_factory import ServiceClientFactory

logger = structlog.get_logger()


@dataclass(frozen=True, slots=True)
class ActiveTool:
    """An immutable snapshot of a resolved tool: its definition + the client that can execute it."""

    definition: ToolDefinition
    client: IServiceClient | None
    service_name: str
    service_id: UUID | None = None
    description_override: str | None = None
    parameters_schema_override: dict[str, Any] | None = None
    http_method_override: str | None = None
    path_template_override: str | None = None
    # Original (pre-override) values for the UI to show defaults
    original_http_method: str | None = None
    original_path_template: str | None = None


@dataclass(frozen=True, slots=True)
class ActiveApp:
    """An immutable snapshot of a resolved app: its definition + the provider that serves it."""

    definition: AppDefinition
    provider: IAppProvider
    client: IServiceClient
    service_name: str
    service_id: UUID | None = None


class ToolRegistry:
    """Manages the lifecycle of MCP tool registration.

    Concurrency-safe via an asyncio.Lock that serialises build/refresh cycles.
    Readers get an immutable snapshot via ``active_tools`` so they never
    observe a half-built registry.
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        encryption: IEncryptionPort,
        client_factory: ServiceClientFactory,
        *,
        service_repo_factory: Callable[[AsyncSession], IServiceRepository] | None = None,
        tool_repo_factory: Callable[[AsyncSession], IToolPermissionRepository] | None = None,
        generic_tool_repo_factory: Callable[[AsyncSession], IGenericToolRepository] | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._encryption = encryption
        self._client_factory = client_factory
        self._service_repo_factory = service_repo_factory
        self._tool_repo_factory = tool_repo_factory
        self._generic_tool_repo_factory = generic_tool_repo_factory
        self._active_tools: dict[str, ActiveTool] = {}
        self._all_tools: dict[str, ActiveTool] = {}
        self._active_apps: dict[str, ActiveApp] = {}
        self._clients: list[IServiceClient] = []
        self._lock = asyncio.Lock()
        self._on_rebuild: Callable[[], Awaitable[None]] | None = None

    def update_encryption(self, encryption: IEncryptionPort) -> None:
        """Update encryption instance after key rotation."""
        self._encryption = encryption

    @property
    def active_tools(self) -> dict[str, ActiveTool]:
        """Return an immutable snapshot of enabled tools.

        Safe to read while a rebuild is in progress.
        """
        return dict(self._active_tools)

    @property
    def all_tools(self) -> dict[str, ActiveTool]:
        """Return an immutable snapshot of all tools (enabled + disabled)."""
        return dict(self._all_tools)

    @property
    def active_apps(self) -> dict[str, ActiveApp]:
        """Return an immutable snapshot of active MCP apps — safe to read during rebuilds."""
        return dict(self._active_apps)

    async def build(self) -> list[ActiveTool]:
        """Scan DB -> build clients -> collect tools -> apply overrides.

        Acquires the registry lock so concurrent callers block rather than
        corrupt internal state.  The old registry remains readable until
        the new one is fully built (swap-on-success).
        """
        async with self._lock:
            return await self._build_locked()

    async def refresh(self) -> list[ActiveTool]:
        """Re-scan DB and rebuild the tool set with a fresh session."""
        return await self.build()

    def set_on_rebuild(self, callback: Callable[[], Awaitable[None]]) -> None:
        """Register a callback that fires after every successful build."""
        self._on_rebuild = callback

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    async def _build_locked(self) -> list[ActiveTool]:
        """Build a new tool set, then atomically swap it in.

        If the build fails the old registry stays intact.
        """
        new_clients: list[IServiceClient] = []
        new_tools: dict[str, ActiveTool] = {}
        new_all_tools: dict[str, ActiveTool] = {}
        new_apps: dict[str, ActiveApp] = {}
        result: list[ActiveTool] = []

        try:
            async with self._session_factory() as session:
                if self._service_repo_factory:
                    service_repo = self._service_repo_factory(session)
                else:
                    from infrastructure.persistence.service_repository import ServiceRepository

                    service_repo = ServiceRepository(session)

                if self._tool_repo_factory:
                    tool_repo = self._tool_repo_factory(session)
                else:
                    from infrastructure.persistence.tool_repository import ToolPermissionRepository

                    tool_repo = ToolPermissionRepository(session)

                services = await service_repo.get_enabled()

                if self._generic_tool_repo_factory:
                    generic_tool_repo = self._generic_tool_repo_factory(session)
                else:
                    from infrastructure.persistence.generic_tool_repository import (
                        GenericToolDefinitionRepository,
                    )

                    generic_tool_repo = GenericToolDefinitionRepository(session)

                for svc in services:
                    if svc.id is None:
                        logger.warning("Service %s has no ID, skipping", svc.name)
                        continue

                    try:
                        token = self._encryption.decrypt(svc.api_token_encrypted)

                        db_tool_defs = await generic_tool_repo.get_by_service_id(svc.id)
                        custom_specs = [
                            GenericToolSpec(
                                tool_name=td.tool_name,
                                description=td.description,
                                http_method=td.http_method,
                                path_template=td.path_template,
                                params_schema=td.params_schema,
                            )
                            for td in db_tool_defs
                        ]

                        if svc.service_type == ServiceType.GENERIC_REST:
                            from infrastructure.clients.generic_rest_client import (
                                validate_base_url as _validate_url,
                            )

                            await _validate_url(svc.base_url)
                            client = self._client_factory.create(
                                svc.service_type,
                                svc.base_url,
                                token,
                                tool_definitions=custom_specs,
                                config=svc.config,
                            )
                            custom_tool_client = client
                        else:
                            client = self._client_factory.create(
                                svc.service_type,
                                svc.base_url,
                                token,
                            )
                            custom_tool_client = None
                            if custom_specs:
                                from infrastructure.clients.generic_rest_client import (
                                    GenericRestClient,
                                    validate_base_url,
                                )

                                await validate_base_url(svc.base_url)
                                custom_tool_client = GenericRestClient(
                                    svc.base_url,
                                    token,
                                    custom_specs,
                                    config=svc.config,
                                )
                                new_clients.append(custom_tool_client)
                    except Exception:
                        logger.exception(
                            "Failed to create client for service %s, skipping",
                            svc.name,
                        )
                        continue

                    new_clients.append(client)

                    overrides = await tool_repo.get_by_service_id(svc.id)

                    # Collect endpoint-overridden tools that need a GenericRestClient
                    endpoint_override_specs: list[GenericToolSpec] = []

                    def _register_tools(
                        src_client: IServiceClient,
                        svc_overrides: dict,
                        svc_ref: Any,
                    ) -> None:
                        for tool_def in src_client.get_tool_definitions():
                            override = svc_overrides.get(tool_def.name)
                            is_enabled = override.is_enabled if override else tool_def.is_enabled
                            desc_override = override.description_override if override else None
                            schema_override = (
                                override.parameters_schema_override if override else None
                            )
                            method_override = (
                                override.http_method_override if override else None
                            )
                            path_override = (
                                override.path_template_override if override else None
                            )

                            resolved = tool_def
                            if desc_override:
                                resolved = replace(
                                    resolved,
                                    description=desc_override,
                                )
                            if schema_override:
                                resolved = replace(
                                    resolved,
                                    parameters_schema=schema_override,
                                )
                            if method_override:
                                resolved = replace(resolved, http_method=method_override)
                            if path_override:
                                resolved = replace(resolved, path_template=path_override)
                            resolved = replace(resolved, is_enabled=is_enabled)

                            # Determine execution client: if endpoint is overridden
                            # on a built-in tool, route through GenericRestClient
                            exec_client: IServiceClient | None = src_client
                            has_endpoint_override = method_override or path_override
                            # Only reroute tools that originally have HTTP endpoints
                            is_http_tool = tool_def.http_method is not None or tool_def.path_template is not None
                            if has_endpoint_override and is_http_tool and src_client is not custom_tool_client:
                                # Will be routed through a per-service override client
                                final_method = method_override or tool_def.http_method or "GET"
                                final_path = path_override or tool_def.path_template or "/"
                                endpoint_override_specs.append(
                                    GenericToolSpec(
                                        tool_name=tool_def.name,
                                        description=resolved.description,
                                        http_method=final_method,
                                        path_template=final_path,
                                        params_schema=resolved.parameters_schema,
                                    )
                                )
                                exec_client = None  # placeholder, set after loop

                            active = ActiveTool(
                                definition=resolved,
                                client=exec_client,
                                service_name=svc_ref.name,
                                service_id=svc_ref.id,
                                description_override=desc_override,
                                parameters_schema_override=schema_override,
                                http_method_override=method_override,
                                path_template_override=path_override,
                                original_http_method=tool_def.http_method,
                                original_path_template=tool_def.path_template,
                            )

                            new_all_tools[tool_def.name] = active
                            if not is_enabled:
                                continue

                            if tool_def.name in new_tools:
                                existing = new_tools[tool_def.name]
                                logger.warning(
                                    "Tool name collision: '%s' from '%s' shadows '%s'",
                                    tool_def.name,
                                    svc_ref.name,
                                    existing.service_name,
                                )
                            new_tools[tool_def.name] = active
                            result.append(active)

                    _register_tools(client, overrides, svc)

                    if custom_tool_client is not None and custom_tool_client is not client:
                        _register_tools(custom_tool_client, overrides, svc)

                    if endpoint_override_specs:
                        from infrastructure.clients.generic_rest_client import (
                            GenericRestClient,
                        )

                        override_client = GenericRestClient(
                            svc.base_url,
                            token,
                            endpoint_override_specs,
                            config=svc.config,
                        )
                        new_clients.append(override_client)

                        # Patch the client reference on overridden tools
                        for spec in endpoint_override_specs:
                            for store in (new_tools, new_all_tools):
                                if spec.tool_name in store:
                                    old = store[spec.tool_name]
                                    if old.client is None:
                                        store[spec.tool_name] = replace(
                                            old, client=override_client
                                        )
                            # Also patch in result list
                            for i, at in enumerate(result):
                                if at.definition.name == spec.tool_name and at.client is None:
                                    result[i] = replace(at, client=override_client)

                    if isinstance(client, IAppProvider):
                        try:
                            for app_def in client.get_app_definitions():
                                if app_def.name in new_apps:
                                    existing_app = new_apps[app_def.name]
                                    logger.warning(
                                        "App name collision: '%s' from '%s' shadows '%s'",
                                        app_def.name,
                                        svc.name,
                                        existing_app.service_name,
                                    )
                                new_apps[app_def.name] = ActiveApp(
                                    definition=app_def,
                                    provider=client,
                                    client=client,
                                    service_name=svc.name,
                                    service_id=svc.id,
                                )
                        except Exception:
                            logger.exception("Failed to discover apps from service %s", svc.name)
        except Exception:
            # Build failed — close any clients we already created and re-raise.
            await self._close_clients(new_clients)
            raise

        # Success — swap in atomically and clean up old clients.
        old_clients = self._clients
        self._clients = new_clients
        self._active_tools = new_tools
        self._all_tools = new_all_tools
        self._active_apps = new_apps
        await self._close_clients(old_clients)

        logger.info("Tool registry built: %d tools from %d services", len(result), len(services))

        from infrastructure import metrics as prom_metrics

        prom_metrics.tools_enabled.set(len(result))

        if self._on_rebuild is not None:
            await self._on_rebuild()

        return result

    async def cleanup(self) -> None:
        """Close all clients and clear the registry.  Called on shutdown."""
        async with self._lock:
            await self._close_clients(self._clients)
            self._clients.clear()
            self._active_tools.clear()
            self._all_tools.clear()
            self._active_apps.clear()

    @staticmethod
    async def _close_clients(clients: list[IServiceClient]) -> None:
        """Best-effort close of a list of service clients."""
        for client in clients:
            try:
                await client.close()
            except Exception:
                logger.exception("Error closing service client")
