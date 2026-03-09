import json
import time
from typing import Any

import structlog
from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from mcp.server.fastmcp.exceptions import ToolError
from mcp.server.fastmcp.utilities.func_metadata import ArgModelBase, FuncMetadata
from pydantic import ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from config import settings
from domain.entities.user import User
from domain.exceptions import ToolExecutionError
from domain.ports.encryption import IEncryptionPort
from entrypoints.mcp.audit_util import record_audit_safe
from entrypoints.mcp.meta_tools import META_TOOL_NAMES, register_meta_tools
from entrypoints.mcp.template_engine import TemplateEngine
from entrypoints.mcp.user_context import can_user_access_service, current_user_var
from services.client_factory import ServiceClientFactory
from services.tool_registry import ToolRegistry

logger = structlog.get_logger()


class _PermissiveArgs(ArgModelBase):
    """Accepts arbitrary kwargs and passes them all through to the tool handler."""

    model_config = ConfigDict(extra="allow", arbitrary_types_allowed=True)

    def model_dump_one_level(self) -> dict[str, Any]:
        result = super().model_dump_one_level()
        if self.model_extra:
            result.update(self.model_extra)
        return result


_PERMISSIVE_METADATA = FuncMetadata(arg_model=_PermissiveArgs)


def _build_server_instructions(
    registry: ToolRegistry | None = None,
    self_mcp_enabled: bool = False,
) -> str:
    """Generate MCP server instructions based on current server state."""
    from domain.entities.service_connection import ServiceType

    service_types = ", ".join(t.value for t in ServiceType)

    parts: list[str] = [
        "Central MCP gateway that gives AI agents access to self-hosted homelab services "
        "through a single endpoint.",
    ]

    # Short descriptions so the LLM understands what each service type is
    _type_labels: dict[str, str] = {
        "forgejo": "Git hosting",
        "homeassistant": "home automation",
        "paperless": "document management",
        "immich": "photo library",
        "nextcloud": "file storage",
        "uptimekuma": "uptime monitoring",
        "adguard": "DNS ad-blocking",
        "nginxproxymanager": "reverse proxy",
        "portainer": "container management",
        "freshrss": "RSS reader",
        "wallabag": "read-it-later",
        "stirlingpdf": "PDF tools",
        "wikijs": "wiki",
        "calibreweb": "e-book library",
        "tailscale": "VPN mesh network",
        "cloudflare": "DNS & CDN",
        "generic_rest": "custom REST API",
    }

    # Describe connected services
    has_services = False
    if registry is not None:
        active = registry.active_tools
        # Collect unique (service_name, service_type) pairs
        svc_info: dict[str, str] = {}
        for t in active.values():
            if t.service_name not in svc_info:
                svc_info[t.service_name] = t.definition.service_type.value

        has_services = bool(svc_info)
        if has_services:
            svc_parts = []
            for name, stype in sorted(svc_info.items()):
                label = _type_labels.get(stype, stype)
                svc_parts.append(f"{name} ({label})")
            first_name = sorted(svc_info.keys())[0]
            parts.append(
                f"Connected services: {', '.join(svc_parts)}. "
                f"Tools are prefixed by service name (e.g. {first_name}_). "
                f"Use mcp_home_list_tools to see what's available."
            )

    # Management guidance depends on both self-MCP and service state
    if self_mcp_enabled:
        if not has_services:
            parts.append(
                "No services are connected yet. "
                "Use mcp_home_add_service to connect one."
            )
        parts.append(
            f"You can manage this gateway: add, update, or remove services and toggle tools. "
            f"Supported service_type values: {service_types}. "
            f"For unlisted services, use generic_rest with mcp_home_add_generic_tool to define custom endpoints."
        )
    else:
        if not has_services:
            parts.append(
                "No services are connected yet. "
                "Use the web UI (Services page) to connect one."
            )
        parts.append(
            "Self-management tools are disabled. "
            "Services can be managed through the web UI, or an admin can enable self-MCP in Settings."
        )

    parts.append(
        "New tools register immediately but some clients (Claude Code, Cursor, Copilot) "
        "need a restart to discover them."
    )

    return " ".join(parts)


class MCPServerFactory:
    """Builds and manages the FastMCP server with dynamically registered tools."""

    def __init__(
        self,
        tool_registry: ToolRegistry,
        session_factory: async_sessionmaker[AsyncSession],
        encryption: IEncryptionPort | None = None,
        client_factory: ServiceClientFactory | None = None,
    ) -> None:
        self._registry = tool_registry
        self._session_factory = session_factory
        self._encryption = encryption
        self._client_factory = client_factory
        self._registered_tools: set[str] = set()
        self._registered_apps: set[str] = set()
        self._template_engine = TemplateEngine()
        self._mcp = FastMCP(
            name=settings.mcp_server_name,
            instructions=_build_server_instructions(),
            streamable_http_path="/",
            json_response=True,
            stateless_http=True,
        )

    def _refresh_instructions(self) -> None:
        """Update server instructions to reflect current state."""
        self._mcp._mcp_server.instructions = _build_server_instructions(
            registry=self._registry,
            self_mcp_enabled=settings.self_mcp_enabled,
        )

    async def initialize(self) -> None:
        """Register tools from DB-configured services onto the MCP server."""
        await self._registry.build()
        self.sync_meta_tools(settings.self_mcp_enabled)
        self._refresh_instructions()

        logger.info("MCP server initialized with %d service tools", len(self._registered_tools))

    def sync_meta_tools(self, enabled: bool) -> None:
        """Register or remove self-MCP meta-tools based on the global toggle."""
        if enabled:
            if not self._encryption or not self._client_factory:
                logger.warning("self_mcp_meta_tools_skipped", reason="missing_dependencies")
                return
            register_meta_tools(
                self._mcp,
                self._session_factory,
                self._encryption,
                self._client_factory,
                self._registry,
            )
            return

        for tool_name in META_TOOL_NAMES:
            try:
                self._mcp.remove_tool(tool_name)
            except ToolError as e:
                if str(e).startswith("Unknown tool:"):
                    continue
                logger.exception("Failed to remove meta tool %s", tool_name)

    def _register_tool(self, tool_name: str) -> None:
        """Register a single service tool on FastMCP with correct schema."""
        active = self._registry.active_tools.get(tool_name)
        if active is None:
            return

        registry = self._registry
        session_factory = self._session_factory

        async def handler(ctx: Context, **kwargs: Any) -> str:
            current = registry.active_tools.get(tool_name)
            if current is None:
                raise ToolExecutionError(tool_name, "Tool is no longer active")

            user = current_user_var.get()
            if user is not None and not user.is_admin:
                svc_name = current.service_name
                allowed = can_user_access_service(user, current.service_id)
                if not allowed:
                    raise ToolExecutionError(
                        tool_name,
                        f"User '{user.username}' does not have access to service '{svc_name}'",
                    )

            client_name = ctx.client_id or "unknown"
            client = current.client
            if client is None:
                raise ToolExecutionError(tool_name, "Tool has no execution client configured")
            svc_name = current.service_name
            start = time.monotonic()
            try:
                result = await client.execute_tool(tool_name, kwargs)
            except Exception as e:
                await record_audit_safe(
                    session_factory,
                    svc_name,
                    tool_name,
                    kwargs,
                    start,
                    error=e,
                    client_name=client_name,
                )
                raise

            await record_audit_safe(
                session_factory,
                svc_name,
                tool_name,
                kwargs,
                start,
                client_name=client_name,
            )

            if isinstance(result, str):
                return result
            return json.dumps(result, default=str, indent=2)

        self._mcp.add_tool(handler, name=tool_name, description=active.definition.description)

        # Override auto-generated schema with actual tool parameters
        tool = self._mcp._tool_manager.get_tool(tool_name)
        if tool is not None:
            tool.parameters = active.definition.parameters_schema or {}
            tool.fn_metadata = _PERMISSIVE_METADATA

        self._registered_tools.add(tool_name)

    def _register_app(self, app_name: str) -> None:
        """Register a per-service app tool on FastMCP that renders HTML via Jinja2."""
        active_app = self._registry.active_apps.get(app_name)
        if active_app is None:
            return

        registry = self._registry
        template_engine = self._template_engine

        async def app_handler(ctx: Context, **kwargs: Any) -> str:
            current = registry.active_apps.get(app_name)
            if current is None:
                raise ToolExecutionError(app_name, "App is no longer active")

            # Enforce per-user authorization
            user = current_user_var.get()
            if user is not None and not user.is_admin:
                allowed = can_user_access_service(user, current.service_id)
                if not allowed:
                    svc = current.service_name
                    raise ToolExecutionError(
                        app_name,
                        f"User '{user.username}' does not have access to service '{svc}'",
                    )

            data = await current.provider.fetch_app_data(app_name, kwargs)
            return template_engine.render(
                f"apps/{current.definition.template_name}",
                **data,
            )

        tool_name = f"app_{app_name}"
        self._mcp.add_tool(
            app_handler,
            name=tool_name,
            description=f"[App] {active_app.definition.title}: {active_app.definition.description}",
        )

        # Override schema
        tool = self._mcp._tool_manager.get_tool(tool_name)
        if tool is not None:
            tool.parameters = active_app.definition.parameters_schema or {}
            tool.fn_metadata = _PERMISSIVE_METADATA

        self._registered_apps.add(app_name)

    async def sync_tools(self) -> None:
        """Reconcile FastMCP's tool list with the current registry state."""
        active = self._registry.active_tools
        desired = set(active.keys())
        synced: set[str] = set()

        for name in self._registered_tools - desired:
            try:
                self._mcp.remove_tool(name)
            except Exception:
                logger.exception("Failed to remove tool %s from FastMCP", name)

        # Re-register to pick up schema/description changes
        for name in self._registered_tools & desired:
            try:
                self._mcp.remove_tool(name)
                self._register_tool(name)
                synced.add(name)
            except Exception:
                logger.exception("Failed to re-register tool %s", name)

        for name in desired - self._registered_tools:
            try:
                self._register_tool(name)
                synced.add(name)
            except Exception:
                logger.exception("Failed to register new tool %s", name)

        self._registered_tools = synced

        active_app_names = set(self._registry.active_apps.keys())
        synced_apps: set[str] = set()

        for app_name in self._registered_apps - active_app_names:
            tool_name = f"app_{app_name}"
            try:
                self._mcp.remove_tool(tool_name)
            except Exception:
                logger.exception("Failed to remove app tool %s", tool_name)

        for app_name in self._registered_apps & active_app_names:
            tool_name = f"app_{app_name}"
            try:
                self._mcp.remove_tool(tool_name)
                self._register_app(app_name)
                synced_apps.add(app_name)
            except Exception:
                logger.exception("Failed to re-register app %s", app_name)

        for app_name in active_app_names - self._registered_apps:
            try:
                self._register_app(app_name)
                synced_apps.add(app_name)
            except Exception:
                logger.exception("Failed to register new app %s", app_name)

        self._registered_apps = synced_apps
        self._refresh_instructions()
        logger.info("MCP tools synced: %d tools, %d apps", len(synced), len(synced_apps))

    @staticmethod
    def set_current_user(user: User | None) -> None:
        """Set the authenticated user for the current request (contextvars-safe)."""
        current_user_var.set(user)

    def get_asgi_app(self) -> Any:
        """Return the Starlette ASGI app for Streamable HTTP transport."""
        return self._mcp.streamable_http_app()

    @property
    def session_manager(self) -> Any:
        return self._mcp.session_manager

    @property
    def mcp(self) -> FastMCP:
        return self._mcp
