"""Self-MCP meta-tools — let agents manage the gateway via MCP itself."""

import json
import time
from collections.abc import Callable
from typing import Any

import structlog
from mcp.server import FastMCP
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from config import settings
from domain.entities.service_connection import HealthStatus, ServiceType
from domain.exceptions import ToolExecutionError
from entrypoints.mcp.audit_util import record_audit_safe
from entrypoints.mcp.template_engine import TemplateEngine
from entrypoints.mcp.user_context import current_user_var, filter_services_for_user
from infrastructure.persistence.audit_repository import AuditRepository
from infrastructure.persistence.generic_tool_repository import GenericToolDefinitionRepository
from infrastructure.persistence.service_repository import ServiceRepository
from infrastructure.persistence.tool_repository import ToolPermissionRepository
from services.audit_service import AuditService
from services.client_factory import ServiceClientFactory
from services.generic_tool_service import (
    GenericToolConflictError,
    GenericToolNotFoundError,
    GenericToolService,
    GenericToolValidationError,
)
from services.service_manager import ServiceManager
from services.tool_permission_service import ToolPermissionService
from services.tool_registry import ToolRegistry

logger = structlog.get_logger()

META_TOOL_NAMES = (
    "mcp_home_list_services",
    "mcp_home_add_service",
    "mcp_home_toggle_tool",
    "mcp_home_get_logs",
    "mcp_home_health",
    "mcp_home_ui_dashboard",
    "mcp_home_ui_service_control",
    "mcp_home_ui_config",
    "mcp_home_list_tools",
    "mcp_home_update_service",
    "mcp_home_delete_service",
    "mcp_home_add_generic_tool",
    "mcp_home_delete_generic_tool",
    "mcp_home_update_generic_tool",
)


def _require_admin_user() -> None:
    """Raise if the current user is not an admin."""
    user = current_user_var.get()
    if user is None:
        raise ToolExecutionError(
            "meta_tool",
            "Admin authentication required for this operation",
        )
    if not user.is_admin:
        raise ToolExecutionError(
            "meta_tool",
            f"User '{user.username}' requires admin privileges for this operation",
        )


def _require_self_mcp_access() -> None:
    """Raise if self-MCP is disabled globally or the user lacks access."""
    if not settings.self_mcp_enabled:
        raise ToolExecutionError(
            "meta_tool",
            "Self-MCP tools are disabled. An admin can enable them in Settings.",
        )
    user = current_user_var.get()
    if user is None:
        raise ToolExecutionError(
            "meta_tool",
            "Authentication required for self-MCP tools",
        )
    if not user.self_mcp_enabled:
        raise ToolExecutionError(
            "meta_tool",
            f"User '{user.username}' does not have self-MCP access. "
            "Ask an admin to enable it in user management.",
        )


def register_meta_tools(
    mcp: FastMCP,
    session_factory: async_sessionmaker[AsyncSession] | Callable[[], Any],
    encryption: Any,
    client_factory: ServiceClientFactory,
    tool_registry: ToolRegistry | Any,
) -> None:
    """Register management tools on the MCP server."""

    async def _audit_meta_tool(
        tool_name: str, kwargs: dict, start: float, *, error: Exception | None = None
    ) -> None:
        """Record audit for a meta-tool call."""
        user = current_user_var.get()
        client_name = f"self-mcp:{user.username}" if user else "self-mcp:unknown"
        await record_audit_safe(
            session_factory,
            "mcp_home",
            tool_name,
            kwargs,
            start,
            error=error,
            client_name=client_name,
        )

    @mcp.tool(
        name="mcp_home_list_services",
        description="List all connected services with health status and tool counts",
    )
    async def list_services() -> str:
        _require_self_mcp_access()
        async with session_factory() as session:
            repo = ServiceRepository(session)
            services = await repo.get_all()

        services = await filter_services_for_user(services)

        active = tool_registry.active_tools
        user = current_user_var.get()
        is_admin = user is not None and user.is_admin
        result = []
        for svc in services:
            tool_count = sum(1 for t in active.values() if t.service_name == svc.name)
            result.append(
                {
                    "name": svc.name,
                    "display_name": svc.display_name,
                    "service_type": svc.service_type.value,
                    "base_url": svc.base_url if is_admin else "(hidden)",
                    "health_status": svc.health_status.value,
                    "is_enabled": svc.is_enabled,
                    "tool_count": tool_count,
                }
            )
        return json.dumps(result, indent=2)

    @mcp.tool(
        name="mcp_home_add_service",
        description=f"Connect a new service to {settings.app_name}",
    )
    async def add_service(
        name: str,
        display_name: str,
        service_type: str,
        base_url: str,
        api_token: str,
    ) -> str:
        _require_self_mcp_access()
        _require_admin_user()
        start = time.monotonic()
        svc_type = ServiceType(service_type)
        async with session_factory() as session:
            manager = ServiceManager(
                repository=ServiceRepository(session),
                encryption=encryption,
                client_factory=client_factory,
            )
            svc = await manager.create_connection(
                name=name,
                display_name=display_name,
                service_type=svc_type,
                base_url=base_url,
                api_token=api_token,
            )
            await session.commit()

        await tool_registry.refresh()
        await _audit_meta_tool(
            "mcp_home_add_service",
            {"name": name, "service_type": service_type},
            start,
        )
        active = tool_registry.active_tools
        tool_count = sum(1 for t in active.values() if t.service_name == svc.name)
        return json.dumps(
            {
                "status": "created",
                "name": svc.name,
                "service_type": svc.service_type.value,
                "tools_registered": tool_count,
                "note": (
                    f"Service '{display_name}' connected with {tool_count} tools. "
                    "New tools are available immediately for MCP clients with active sessions. "
                    "Some clients (Claude Code, Copilot CLI) may require a restart to discover them."
                ),
            }
        )

    @mcp.tool(
        name="mcp_home_update_service",
        description=(
            "Update an existing service connection. "
            "Only provided fields are changed — omit fields you don't want to update."
        ),
    )
    async def update_service(
        name: str,
        display_name: str | None = None,
        base_url: str | None = None,
        api_token: str | None = None,
        is_enabled: bool | None = None,
    ) -> str:
        _require_self_mcp_access()
        _require_admin_user()
        start = time.monotonic()
        async with session_factory() as session:
            repo = ServiceRepository(session)
            svc = await repo.get_by_name(name)
            if svc is None or svc.id is None:
                return json.dumps({"error": f"Service '{name}' not found"})

            manager = ServiceManager(
                repository=repo,
                encryption=encryption,
                client_factory=client_factory,
            )
            svc = await manager.update_connection(
                svc.id,
                display_name=display_name,
                base_url=base_url,
                api_token=api_token,
                is_enabled=is_enabled,
            )
            await session.commit()

        await tool_registry.refresh()
        await _audit_meta_tool(
            "mcp_home_update_service",
            {"name": name},
            start,
        )
        return json.dumps(
            {
                "status": "updated",
                "name": svc.name,
                "service_type": svc.service_type.value,
            }
        )

    @mcp.tool(
        name="mcp_home_delete_service",
        description="Permanently delete a service connection and all its tools",
    )
    async def delete_service(name: str) -> str:
        _require_self_mcp_access()
        _require_admin_user()
        start = time.monotonic()
        async with session_factory() as session:
            repo = ServiceRepository(session)
            svc = await repo.get_by_name(name)
            if svc is None or svc.id is None:
                return json.dumps({"error": f"Service '{name}' not found"})

            manager = ServiceManager(
                repository=repo,
                encryption=encryption,
                client_factory=client_factory,
            )
            await manager.delete_connection(svc.id)
            await session.commit()

        await tool_registry.refresh()
        await _audit_meta_tool(
            "mcp_home_delete_service",
            {"name": name},
            start,
        )
        return json.dumps({"status": "deleted", "name": name})

    @mcp.tool(
        name="mcp_home_toggle_tool",
        description="Enable or disable an MCP tool by service name and tool name",
    )
    async def toggle_tool(
        service_name: str,
        tool_name: str,
        enabled: bool,
    ) -> str:
        _require_self_mcp_access()
        _require_admin_user()
        start = time.monotonic()
        async with session_factory() as session:
            repo = ServiceRepository(session)
            svc = await repo.get_by_name(service_name)
            if svc is None or svc.id is None:
                return json.dumps({"error": f"Service '{service_name}' not found"})

            permission_service = ToolPermissionService(ToolPermissionRepository(session))
            try:
                await permission_service.set_permission(
                    svc.id,
                    tool_name=tool_name,
                    is_enabled=enabled,
                )
            except ValueError as e:
                return json.dumps({"error": str(e)})
            await session.commit()

        await tool_registry.refresh()
        await _audit_meta_tool(
            "mcp_home_toggle_tool",
            {"service_name": service_name, "tool_name": tool_name, "enabled": enabled},
            start,
        )
        return json.dumps(
            {
                "status": "updated",
                "tool_name": tool_name,
                "enabled": enabled,
            }
        )

    @mcp.tool(
        name="mcp_home_get_logs",
        description="Get recent audit logs of MCP tool calls",
    )
    async def get_logs(
        limit: int = 20,
        service_name: str | None = None,
    ) -> str:
        _require_self_mcp_access()
        async with session_factory() as session:
            audit = AuditService(repository=AuditRepository(session))
            entries = await audit.get_recent(
                limit=limit,
                service_name=service_name,
            )

        user = current_user_var.get()
        if user is None:
            entries = []
        elif not user.is_admin:
            async with session_factory() as session:
                repo = ServiceRepository(session)
                all_services = await repo.get_all()
            allowed_services = await filter_services_for_user(all_services)
            allowed_names = {s.name for s in allowed_services}
            entries = [e for e in entries if e.service_name in allowed_names]

        result = [
            {
                "tool_name": e.tool_name,
                "service_name": e.service_name,
                "status": e.status.value,
                "duration_ms": e.duration_ms,
                "error_message": e.error_message,
                "client_name": e.client_name,
                "created_at": str(e.created_at) if e.created_at else None,
            }
            for e in entries
        ]
        return json.dumps(result, indent=2)

    @mcp.tool(
        name="mcp_home_health",
        description=f"Get the overall health status of {settings.app_name}",
    )
    async def health() -> str:
        _require_self_mcp_access()
        async with session_factory() as session:
            repo = ServiceRepository(session)
            services = await repo.get_all()

        services = await filter_services_for_user(services)

        active = tool_registry.active_tools
        healthy = sum(1 for s in services if s.health_status == HealthStatus.HEALTHY)

        return json.dumps(
            {
                "services_total": len(services),
                "services_healthy": healthy,
                "tools_enabled": len(active),
                "service_types": list({s.service_type.value for s in services}),
            },
            indent=2,
        )

    template_engine = TemplateEngine()

    @mcp.tool(
        name="mcp_home_ui_dashboard",
        description=(
            "Interactive HTML dashboard showing service health, recent tool calls, and system stats"
        ),
    )
    async def ui_dashboard() -> str:
        _require_self_mcp_access()
        async with session_factory() as session:
            repo = ServiceRepository(session)
            all_services = await repo.get_all()

            audit = AuditService(repository=AuditRepository(session))
            recent = await audit.get_recent(limit=10)

        services = await filter_services_for_user(all_services)

        # Filter audit logs to only show entries for accessible services
        allowed_names = {s.name for s in services}
        recent = [e for e in recent if e.service_name in allowed_names]

        active = tool_registry.active_tools
        svc_data = []
        for svc in services:
            tool_count = sum(1 for t in active.values() if t.service_name == svc.name)
            svc_data.append(
                {
                    "name": svc.name,
                    "display_name": svc.display_name,
                    "service_type": svc.service_type.value,
                    "health_status": svc.health_status.value,
                    "is_enabled": svc.is_enabled,
                    "tool_count": tool_count,
                }
            )

        healthy = sum(1 for s in services if s.health_status == HealthStatus.HEALTHY)
        log_data = [
            {
                "tool_name": e.tool_name,
                "service_name": e.service_name,
                "status": e.status.value,
                "duration_ms": e.duration_ms,
                "client_name": e.client_name,
                "created_at": e.created_at,
            }
            for e in recent
        ]

        return template_engine.render(
            "dashboard.html",
            services=svc_data,
            recent_logs=log_data,
            stats={
                "services_total": len(services),
                "services_healthy": healthy,
                "tools_enabled": len(active),
            },
            app_name=settings.app_name,
        )

    @mcp.tool(
        name="mcp_home_ui_service_control",
        description=(
            "Interactive HTML control panel for a specific service — "
            "shows tools, health, and configuration"
        ),
    )
    async def ui_service_control(service_name: str) -> str:
        _require_self_mcp_access()
        async with session_factory() as session:
            repo = ServiceRepository(session)
            svc = await repo.get_by_name(service_name)

        if svc is None:
            return json.dumps({"error": f"Service '{service_name}' not found"})

        allowed = await filter_services_for_user([svc])
        if not allowed:
            return json.dumps({"error": f"Access denied to service '{service_name}'"})

        active = tool_registry.active_tools
        tools = [
            {
                "name": t.definition.name,
                "description": t.definition.description,
                "is_enabled": t.definition.is_enabled,
            }
            for t in active.values()
            if t.service_name == svc.name
        ]

        user = current_user_var.get()
        is_admin = user is not None and user.is_admin
        return template_engine.render(
            "control.html",
            service={
                "name": svc.name,
                "display_name": svc.display_name,
                "service_type": svc.service_type.value,
                "health_status": svc.health_status.value,
                "base_url": svc.base_url if is_admin else "(hidden)",
            },
            tools=tools,
            app_name=settings.app_name,
        )

    @mcp.tool(
        name="mcp_home_ui_config",
        description=(
            "Interactive HTML view of service configuration — "
            "shows one or all services with their settings"
        ),
    )
    async def ui_config(service_name: str | None = None) -> str:
        _require_self_mcp_access()
        async with session_factory() as session:
            repo = ServiceRepository(session)
            if service_name:
                svc = await repo.get_by_name(service_name)
                raw_services = [svc] if svc else []
            else:
                raw_services = await repo.get_all()

        services = await filter_services_for_user(raw_services)

        if service_name and not services:
            return json.dumps({"error": f"Service '{service_name}' not found"})

        user = current_user_var.get()
        is_admin = user is not None and user.is_admin
        svc_data = [
            {
                "name": s.name,
                "display_name": s.display_name,
                "service_type": s.service_type.value,
                "base_url": s.base_url if is_admin else "(hidden)",
                "config": s.config if is_admin else {},
                "config_json": json.dumps(s.config, indent=2, default=str) if is_admin else "{}",
            }
            for s in services
        ]

        return template_engine.render(
            "config.html",
            services=svc_data,
            single=bool(service_name),
            app_name=settings.app_name,
        )

    @mcp.tool(
        name="mcp_home_list_tools",
        description="List all MCP tools with their status, optionally filtered by service name",
    )
    async def list_tools(service_name: str | None = None) -> str:
        _require_self_mcp_access()
        all_t = tool_registry.all_tools

        async with session_factory() as session:
            repo = ServiceRepository(session)
            all_services = await repo.get_all()
        accessible = await filter_services_for_user(all_services)
        accessible_names = {s.name for s in accessible}

        tools_list = []
        for name, t in all_t.items():
            if t.service_name not in accessible_names:
                continue
            if service_name and t.service_name != service_name:
                continue
            tools_list.append(
                {
                    "name": name,
                    "service_name": t.service_name,
                    "service_type": t.definition.service_type.value,
                    "is_enabled": t.definition.is_enabled,
                    "description": t.definition.description[:200],
                }
            )
        return json.dumps(tools_list, indent=2)

    @mcp.tool(
        name="mcp_home_add_generic_tool",
        description=(
            "Add a custom tool definition to any service. "
            "Requires service_name, tool_name, description, http_method "
            "(GET/POST/PUT/PATCH/DELETE), path_template, and optional "
            "params_schema (JSON string)."
        ),
    )
    async def add_generic_tool(
        service_name: str,
        tool_name: str,
        description: str,
        http_method: str,
        path_template: str,
        params_schema: str = "{}",
    ) -> str:
        _require_self_mcp_access()
        _require_admin_user()
        start = time.monotonic()

        async with session_factory() as session:
            repo = ServiceRepository(session)
            svc = await repo.get_by_name(service_name)
            if svc is None or svc.id is None:
                return json.dumps({"error": f"Service '{service_name}' not found"})

            generic_tools = GenericToolService(GenericToolDefinitionRepository(session))
            try:
                schema = generic_tools.parse_params_schema_json(params_schema)
                await generic_tools.create_tool(
                    svc.id,
                    tool_name=tool_name,
                    description=description,
                    http_method=http_method,
                    path_template=path_template,
                    params_schema=schema,
                )
                await session.commit()
            except GenericToolConflictError as e:
                return json.dumps({"error": str(e)})
            except GenericToolValidationError as e:
                return json.dumps({"error": str(e)})

        await tool_registry.refresh()
        await _audit_meta_tool(
            "mcp_home_add_generic_tool",
            {"service_name": service_name, "tool_name": tool_name, "http_method": http_method},
            start,
        )
        return json.dumps(
            {"status": "created", "tool_name": tool_name, "service_name": service_name}
        )

    @mcp.tool(
        name="mcp_home_delete_generic_tool",
        description=(
            "Delete a custom tool definition from any service by service name and tool name"
        ),
    )
    async def delete_generic_tool(
        service_name: str,
        tool_name: str,
    ) -> str:
        _require_self_mcp_access()
        _require_admin_user()
        start = time.monotonic()

        async with session_factory() as session:
            repo = ServiceRepository(session)
            svc = await repo.get_by_name(service_name)
            if svc is None or svc.id is None:
                return json.dumps({"error": f"Service '{service_name}' not found"})

            generic_tools = GenericToolService(GenericToolDefinitionRepository(session))
            try:
                await generic_tools.delete_tool(svc.id, tool_name)
            except GenericToolNotFoundError as e:
                return json.dumps({"error": str(e)})
            await session.commit()

        await tool_registry.refresh()
        await _audit_meta_tool(
            "mcp_home_delete_generic_tool",
            {"service_name": service_name, "tool_name": tool_name},
            start,
        )
        return json.dumps(
            {"status": "deleted", "tool_name": tool_name, "service_name": service_name}
        )

    @mcp.tool(
        name="mcp_home_update_generic_tool",
        description=(
            "Update a custom tool definition on any service. Only provided fields are updated."
        ),
    )
    async def update_generic_tool(
        service_name: str,
        tool_name: str,
        description: str | None = None,
        http_method: str | None = None,
        path_template: str | None = None,
        params_schema: str | None = None,
    ) -> str:
        _require_self_mcp_access()
        _require_admin_user()
        start = time.monotonic()

        async with session_factory() as session:
            repo = ServiceRepository(session)
            svc = await repo.get_by_name(service_name)
            if svc is None or svc.id is None:
                return json.dumps({"error": f"Service '{service_name}' not found"})

            generic_tools = GenericToolService(GenericToolDefinitionRepository(session))
            try:
                schema = (
                    generic_tools.parse_params_schema_json(params_schema)
                    if params_schema is not None
                    else None
                )
                await generic_tools.update_tool(
                    svc.id,
                    tool_name,
                    description=description,
                    http_method=http_method,
                    path_template=path_template,
                    params_schema=schema,
                )
                await session.commit()
            except GenericToolNotFoundError as e:
                return json.dumps({"error": str(e)})
            except GenericToolValidationError as e:
                return json.dumps({"error": str(e)})

        await tool_registry.refresh()
        await _audit_meta_tool(
            "mcp_home_update_generic_tool",
            {"service_name": service_name, "tool_name": tool_name},
            start,
        )
        return json.dumps(
            {"status": "updated", "tool_name": tool_name, "service_name": service_name}
        )

    logger.info("meta_tools_registered", count=len(META_TOOL_NAMES))
