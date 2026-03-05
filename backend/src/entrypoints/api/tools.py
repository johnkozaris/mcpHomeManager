from typing import Any
from uuid import UUID

import structlog
from litestar import Controller, Request, Response, get, patch, post
from litestar.enums import MediaType
from litestar.exceptions import ClientException
from sqlalchemy.ext.asyncio import AsyncSession

from entrypoints.api.schemas import (
    AppActionRequest,
    AppResponse,
    ToolResponse,
    UpdateToolPermission,
)
from entrypoints.mcp.template_engine import TemplateEngine
from security.auth_context import AuthContext
from services.tool_permission_service import ToolPermissionService
from services.tool_registry import ToolRegistry

logger = structlog.get_logger()
_template_engine = TemplateEngine()


class ToolController(Controller):
    path = "/api/tools"

    @get("/")
    async def list_tools(
        self,
        request: Request,
        tool_registry: ToolRegistry,
    ) -> list[ToolResponse]:
        ctx: AuthContext = request.user

        results = []
        for t in tool_registry.all_tools.values():
            if not ctx.can_access_service(t.service_id):
                continue
            results.append(
                ToolResponse(
                    name=t.definition.name,
                    service_type=t.definition.service_type.value,
                    service_id=t.service_id,
                    service_name=t.service_name,
                    description=t.definition.description,
                    parameters_schema=t.definition.parameters_schema,
                    is_enabled=t.definition.is_enabled,
                    description_override=t.description_override,
                    parameters_schema_override=t.parameters_schema_override,
                    http_method=t.original_http_method,
                    path_template=t.original_path_template,
                    http_method_override=t.http_method_override,
                    path_template_override=t.path_template_override,
                )
            )
        return results

    @patch("/{service_id:uuid}/{tool_name:str}")
    async def update_tool_permission(
        self,
        request: Request,
        db_session: AsyncSession,
        tool_registry: ToolRegistry,
        service_id: UUID,
        tool_name: str,
        data: UpdateToolPermission,
    ) -> ToolResponse:
        ctx: AuthContext = request.user
        ctx.require_service_access(service_id)

        from infrastructure.persistence.tool_repository import ToolPermissionRepository

        service = ToolPermissionService(ToolPermissionRepository(db_session))
        try:
            await service.set_permission(
                service_id,
                tool_name=tool_name,
                is_enabled=data.is_enabled,
                description_override=data.description_override or None,
                parameters_schema_override=data.parameters_schema_override or None,
                http_method_override=data.http_method_override or None,
                path_template_override=data.path_template_override or None,
            )
        except ValueError as exc:
            raise ClientException(str(exc)) from exc
        await db_session.commit()

        # Rebuild tools so the change takes effect (reads committed data)
        await tool_registry.refresh()

        tool = tool_registry.active_tools.get(tool_name)
        if not tool:
            tool = tool_registry.all_tools.get(tool_name)
        if tool:
            return ToolResponse(
                name=tool.definition.name,
                service_type=tool.definition.service_type.value,
                service_id=tool.service_id,
                service_name=tool.service_name,
                description=tool.definition.description,
                parameters_schema=tool.definition.parameters_schema,
                is_enabled=tool.definition.is_enabled,
                description_override=tool.description_override,
                parameters_schema_override=tool.parameters_schema_override,
                http_method=tool.original_http_method,
                path_template=tool.original_path_template,
                http_method_override=tool.http_method_override,
                path_template_override=tool.path_template_override,
            )
        return ToolResponse(
            name=tool_name,
            service_type="",
            service_id=service_id,
            service_name=None,
            description="",
            parameters_schema={},
            is_enabled=False,
        )

    @get("/apps")
    async def list_apps(self, request: Request, tool_registry: ToolRegistry) -> list[AppResponse]:
        ctx: AuthContext = request.user

        return [
            AppResponse(
                name=a.definition.name,
                service_type=a.definition.service_type,
                service_name=a.service_name,
                title=a.definition.title,
                description=a.definition.description,
                parameters_schema=a.definition.parameters_schema,
            )
            for a in tool_registry.active_apps.values()
            if ctx.can_access_service(a.service_id)
        ]

    @post("/apps/{app_name:str}/render")
    async def render_app(
        self,
        request: Request,
        tool_registry: ToolRegistry,
        app_name: str,
        data: dict[str, Any] | None = None,
    ) -> Response[str]:
        active = tool_registry.active_apps.get(app_name)
        if active is None:
            return Response(content="App not found", status_code=404, media_type=MediaType.TEXT)

        ctx: AuthContext = request.user
        if not ctx.can_access_service(active.service_id):
            return Response(content="Access denied", status_code=403, media_type=MediaType.TEXT)

        try:
            app_data = await active.provider.fetch_app_data(app_name, data or {})
            html = _template_engine.render(f"apps/{active.definition.template_name}", **app_data)
        except Exception:
            logger.exception("Failed to render app %s", app_name)
            return Response(
                content="Failed to render app",
                status_code=500,
                media_type=MediaType.TEXT,
            )
        return Response(content=html, media_type=MediaType.HTML)

    @post("/apps/{app_name:str}/action")
    async def app_action(
        self,
        request: Request,
        tool_registry: ToolRegistry,
        app_name: str,
        data: AppActionRequest,
    ) -> Response[str]:
        active = tool_registry.active_apps.get(app_name)
        if active is None:
            return Response(content="App not found", status_code=404, media_type=MediaType.TEXT)

        ctx: AuthContext = request.user
        if not ctx.can_access_service(active.service_id):
            return Response(content="Access denied", status_code=403, media_type=MediaType.TEXT)

        try:
            result_data = await active.provider.handle_app_action(
                app_name,
                data.action,
                data.payload,
            )
            html = _template_engine.render(f"apps/{active.definition.template_name}", **result_data)
        except Exception:
            logger.exception("Failed to execute app action %s/%s", app_name, data.action)
            return Response(
                content="Failed to execute action",
                status_code=500,
                media_type=MediaType.TEXT,
            )
        return Response(content=html, media_type=MediaType.HTML)
