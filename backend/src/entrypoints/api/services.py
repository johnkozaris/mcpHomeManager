import re
import time
from uuid import UUID

import httpx
import structlog
from litestar import Controller, MediaType, Request, Response, delete, get, patch, post
from litestar.exceptions import ClientException, NotFoundException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.service_connection import ServiceConnection, ServiceType
from domain.ports.encryption import IEncryptionPort
from entrypoints.api.schemas import (
    ApplyProfileRequest,
    ApplyProfileResponse,
    CreateGenericToolRequest,
    CreateServiceRequest,
    GenericToolResult,
    ImportOpenAPIRequest,
    ImportOpenAPIResult,
    ImportRequest,
    ImportResult,
    ProfileResponse,
    ServiceDetailResponse,
    ServiceResponse,
    TestResult,
    ToolResponse,
    UpdateGenericToolRequest,
    UpdateServiceRequest,
)
from infrastructure.persistence.audit_repository import AuditRepository
from infrastructure.persistence.generic_tool_repository import GenericToolDefinitionRepository
from infrastructure.persistence.tool_repository import ToolPermissionRepository
from security.auth_context import AuthContext
from services.audit_service import AuditService
from services.config_export import ConfigExporter
from services.openapi_parser import OpenAPIParser
from services.permission_profiles import PROFILES
from services.service_manager import ServiceManager
from services.tool_registry import ToolRegistry


def _to_response(svc: ServiceConnection, tool_count: int = 0) -> ServiceResponse:
    if svc.id is None:
        raise ValueError("Service ID is required for API responses")
    return ServiceResponse(
        id=svc.id,
        name=svc.name,
        display_name=svc.display_name,
        service_type=svc.service_type.value,
        base_url=svc.base_url,
        is_enabled=svc.is_enabled,
        health_status=svc.health_status.value,
        last_health_check=svc.last_health_check,
        tool_count=tool_count,
        created_at=svc.created_at,
        updated_at=svc.updated_at,
    )


class ServiceController(Controller):
    path = "/api/services"

    @get("/")
    async def list_services(
        self,
        request: Request,
        service_manager: ServiceManager,
        tool_registry: ToolRegistry,
    ) -> list[ServiceResponse]:
        ctx: AuthContext = request.user
        services = await service_manager.list_all()

        # Non-admin users only see their allowed services
        if not ctx.is_admin:
            services = [s for s in services if ctx.can_access_service(s.id)]

        tools = tool_registry.all_tools
        return [
            _to_response(
                svc,
                tool_count=sum(1 for t in tools.values() if t.service_name == svc.name),
            )
            for svc in services
        ]

    @post("/")
    async def create_service(
        self,
        request: Request,
        db_session: AsyncSession,
        service_manager: ServiceManager,
        tool_registry: ToolRegistry,
        data: CreateServiceRequest,
    ) -> ServiceResponse:
        ctx: AuthContext = request.user
        if not ctx.is_admin:
            raise ClientException("Admin access required to create services", status_code=403)
        try:
            svc = await service_manager.create_connection(
                name=data.name,
                display_name=data.display_name,
                service_type=ServiceType(data.service_type),
                base_url=data.base_url,
                api_token=data.api_token,
                config=data.config,
            )
        except ValueError as e:
            raise ClientException(str(e)) from e
        await db_session.commit()
        await tool_registry.refresh()
        return _to_response(svc)

    @get("/{service_id:uuid}")
    async def get_service(
        self,
        request: Request,
        db_session: AsyncSession,
        service_manager: ServiceManager,
        tool_registry: ToolRegistry,
        service_id: UUID,
    ) -> ServiceDetailResponse:
        ctx: AuthContext = request.user
        ctx.require_service_access(service_id)

        svc = await service_manager.get_by_id(service_id)

        # Load custom tool definitions so we can include http_method / path_template
        generic_tool_defs: dict[str, tuple[str, str]] = {}
        gt_repo = GenericToolDefinitionRepository(db_session)
        for td in await gt_repo.get_by_service_id(service_id):
            generic_tool_defs[td.tool_name] = (td.http_method, td.path_template)

        svc_tools = [
            ToolResponse(
                name=t.definition.name,
                service_type=t.definition.service_type.value,
                description=t.definition.description,
                parameters_schema=t.definition.parameters_schema,
                is_enabled=t.definition.is_enabled,
                description_override=t.description_override,
                parameters_schema_override=t.parameters_schema_override,
                http_method=generic_tool_defs.get(t.definition.name, (None, None))[0],
                path_template=generic_tool_defs.get(t.definition.name, (None, None))[1],
            )
            for t in tool_registry.all_tools.values()
            if t.service_name == svc.name
        ]

        return ServiceDetailResponse(
            id=service_id,
            name=svc.name,
            display_name=svc.display_name,
            service_type=svc.service_type.value,
            base_url=svc.base_url,
            is_enabled=svc.is_enabled,
            health_status=svc.health_status.value,
            last_health_check=svc.last_health_check,
            tool_count=len(svc_tools),
            config=svc.config,
            tools=svc_tools,
            created_at=svc.created_at,
            updated_at=svc.updated_at,
        )

    @patch("/{service_id:uuid}")
    async def update_service(
        self,
        request: Request,
        db_session: AsyncSession,
        service_manager: ServiceManager,
        tool_registry: ToolRegistry,
        service_id: UUID,
        data: UpdateServiceRequest,
    ) -> ServiceResponse:
        ctx: AuthContext = request.user
        ctx.require_service_access(service_id)

        try:
            svc = await service_manager.update_connection(
                service_id,
                display_name=data.display_name,
                base_url=data.base_url,
                api_token=data.api_token,
                is_enabled=data.is_enabled,
                config=data.config,
            )
        except ValueError as e:
            raise ClientException(str(e)) from e
        await db_session.commit()
        await tool_registry.refresh()
        return _to_response(svc)

    @delete("/{service_id:uuid}")
    async def delete_service(
        self,
        request: Request,
        db_session: AsyncSession,
        service_manager: ServiceManager,
        tool_registry: ToolRegistry,
        service_id: UUID,
    ) -> None:
        ctx: AuthContext = request.user
        ctx.require_service_access(service_id)

        await service_manager.delete_connection(service_id)
        await db_session.commit()
        await tool_registry.refresh()

    @get("/export", media_type=MediaType.TEXT)
    async def export_services(
        self,
        request: Request,
        service_manager: ServiceManager,
    ) -> Response[str]:
        ctx: AuthContext = request.user
        services = await service_manager.list_all()

        # Non-admin: only export allowed services
        if not ctx.is_admin:
            services = [s for s in services if ctx.can_access_service(s.id)]

        exporter = ConfigExporter()
        yaml_content = exporter.export_yaml(services)
        return Response(
            content=yaml_content,
            media_type="application/x-yaml",
            headers={"Content-Disposition": "attachment; filename=mcp-services.yaml"},
        )

    @post("/import")
    async def import_services(
        self,
        request: Request,
        db_session: AsyncSession,
        service_manager: ServiceManager,
        tool_registry: ToolRegistry,
        data: ImportRequest,
    ) -> ImportResult:
        ctx: AuthContext = request.user
        if not ctx.is_admin:
            raise ClientException("Admin access required to import services", status_code=403)
        exporter = ConfigExporter()
        try:
            specs = exporter.parse_import(data.yaml_content)
        except ValueError as e:
            return ImportResult(errors=[str(e)])

        result = ImportResult()
        existing = await service_manager.list_all()
        existing_names = {s.name for s in existing}

        for spec in specs:
            if spec.name in existing_names:
                result.skipped.append(spec.name)
                continue

            token = data.token_map.get(spec.name, "")
            if not token:
                result.errors.append(f"{spec.name}: no API token provided in token_map")
                continue

            try:
                await service_manager.create_connection(
                    name=spec.name,
                    display_name=spec.display_name,
                    service_type=ServiceType(spec.service_type),
                    base_url=spec.base_url,
                    api_token=token,
                    config=spec.config,
                )
                result.created.append(spec.name)
            except Exception as e:
                result.errors.append(f"{spec.name}: {e}")

        if result.created:
            await db_session.commit()
            await tool_registry.refresh()

        return result

    @get("/{service_id:uuid}/profiles")
    async def get_profiles(
        self,
        request: Request,
        service_manager: ServiceManager,
        service_id: UUID,
    ) -> list[ProfileResponse]:
        ctx: AuthContext = request.user
        ctx.require_service_access(service_id)

        svc = await service_manager.get_by_id(service_id)

        profiles = PROFILES.get(svc.service_type, [])
        return [
            ProfileResponse(
                name=p.name,
                label=p.label,
                description=p.description,
                tool_states=p.tool_states,
            )
            for p in profiles
        ]

    @post("/{service_id:uuid}/apply-profile")
    async def apply_profile(
        self,
        request: Request,
        db_session: AsyncSession,
        service_manager: ServiceManager,
        tool_registry: ToolRegistry,
        service_id: UUID,
        data: ApplyProfileRequest,
    ) -> ApplyProfileResponse:
        ctx: AuthContext = request.user
        ctx.require_service_access(service_id)

        svc = await service_manager.get_by_id(service_id)

        profiles = PROFILES.get(svc.service_type, [])
        profile = next((p for p in profiles if p.name == data.profile_name), None)
        if profile is None:
            raise NotFoundException(f"Profile '{data.profile_name}' not found")

        if svc.id is None:
            raise NotFoundException("Service has no ID")
        tool_repo = ToolPermissionRepository(db_session)
        for tool_name, enabled in profile.tool_states.items():
            await tool_repo.set_permission(svc.id, tool_name, enabled)
        await db_session.commit()
        await tool_registry.refresh()

        return ApplyProfileResponse(status="applied", profile=profile.name)

    @post("/{service_id:uuid}/test")
    async def test_connection(
        self,
        request: Request,
        db_session: AsyncSession,
        service_manager: ServiceManager,
        tool_registry: ToolRegistry,
        service_id: UUID,
    ) -> TestResult:
        ctx: AuthContext = request.user
        ctx.require_service_access(service_id)

        success, message = await service_manager.test_connection(service_id)
        await db_session.commit()
        if success:
            await tool_registry.refresh()
        return TestResult(success=success, message=message)

    @post("/{service_id:uuid}/tools")
    async def create_generic_tool(
        self,
        request: Request,
        db_session: AsyncSession,
        service_manager: ServiceManager,
        tool_registry: ToolRegistry,
        service_id: UUID,
        data: CreateGenericToolRequest,
    ) -> GenericToolResult:
        ctx: AuthContext = request.user
        ctx.require_service_access(service_id)

        await service_manager.get_by_id(service_id)

        repo = GenericToolDefinitionRepository(db_session)
        try:
            row = await repo.create(
                service_id=service_id,
                tool_name=data.tool_name,
                description=data.description,
                http_method=data.http_method,
                path_template=data.path_template,
                params_schema=data.params_schema,
            )
        except IntegrityError:
            raise ClientException(
                detail=f"Tool '{data.tool_name}' already exists on this service",
                status_code=409,
            ) from None
        await db_session.commit()
        await tool_registry.refresh()
        return GenericToolResult(status="created", tool_name=row.tool_name, tools_count=1)

    @patch("/{service_id:uuid}/tools/{tool_name:str}")
    async def update_generic_tool(
        self,
        request: Request,
        db_session: AsyncSession,
        service_manager: ServiceManager,
        tool_registry: ToolRegistry,
        service_id: UUID,
        tool_name: str,
        data: UpdateGenericToolRequest,
    ) -> GenericToolResult:
        ctx: AuthContext = request.user
        ctx.require_service_access(service_id)
        await service_manager.get_by_id(service_id)

        repo = GenericToolDefinitionRepository(db_session)
        row = await repo.update(
            service_id,
            tool_name,
            description=data.description,
            http_method=data.http_method,
            path_template=data.path_template,
            params_schema=data.params_schema,
        )
        if row is None:
            raise NotFoundException(f"Tool '{tool_name}' not found")
        await db_session.commit()
        await tool_registry.refresh()
        return GenericToolResult(status="updated", tool_name=row.tool_name, tools_count=1)

    @delete("/{service_id:uuid}/tools/{tool_name:str}")
    async def delete_generic_tool(
        self,
        request: Request,
        db_session: AsyncSession,
        service_manager: ServiceManager,
        tool_registry: ToolRegistry,
        service_id: UUID,
        tool_name: str,
    ) -> None:
        ctx: AuthContext = request.user
        ctx.require_service_access(service_id)
        await service_manager.get_by_id(service_id)

        repo = GenericToolDefinitionRepository(db_session)
        deleted = await repo.delete(service_id, tool_name)
        if not deleted:
            raise NotFoundException(f"Tool '{tool_name}' not found")
        await db_session.commit()
        await tool_registry.refresh()

    @post("/{service_id:uuid}/tools/{tool_name:str}/test")
    async def test_generic_tool(
        self,
        request: Request,
        db_session: AsyncSession,
        service_manager: ServiceManager,
        service_id: UUID,
        tool_name: str,
    ) -> TestResult:
        ctx: AuthContext = request.user
        ctx.require_service_access(service_id)
        svc = await service_manager.get_by_id(service_id)
        start = time.monotonic()

        repo = GenericToolDefinitionRepository(db_session)
        tools = await repo.get_by_service_id(service_id)
        tool = next((t for t in tools if t.tool_name == tool_name), None)
        if tool is None:
            raise NotFoundException(f"Tool '{tool_name}' not found")

        # Probe: substitute path params with "test" placeholder
        path = re.sub(r"\{[^}]+\}", "test", tool.path_template)

        encryption: IEncryptionPort = request.app.state.encryption

        # Re-validate URL (defense-in-depth — URL may have been updated since creation)
        from infrastructure.clients.generic_rest_client import validate_base_url

        try:
            await validate_base_url(svc.base_url)
        except ValueError as e:
            return TestResult(success=False, message=f"URL validation failed: {e}")

        try:
            token = encryption.decrypt(svc.api_token_encrypted)
            # Apply custom headers from service config (matches GenericRestClient behavior)
            # Filter dangerous headers that could enable request smuggling
            raw_headers = (svc.config or {}).get("headers", {}) or {}
            custom_headers = {
                k: v
                for k, v in raw_headers.items()
                if k.lower() not in ("host", "content-length", "transfer-encoding")
            }
            async with httpx.AsyncClient(
                base_url=svc.base_url.rstrip("/"),
                headers={
                    **custom_headers,
                    "Authorization": f"Bearer {token}",
                },
                timeout=10.0,
                follow_redirects=False,
            ) as client:
                resp = await client.request("HEAD", path)
                if resp.status_code < 500:
                    result = TestResult(
                        success=True,
                        message=f"Endpoint reachable (HTTP {resp.status_code})",
                    )
                else:
                    result = TestResult(
                        success=False,
                        message=f"Server error: HTTP {resp.status_code}",
                    )
        except httpx.ConnectError as e:
            result = TestResult(success=False, message=f"Connection failed: {str(e)[:200]}")
        except Exception as e:
            structlog.get_logger().warning(
                "tool_test_probe_failed",
                service_id=str(service_id),
                tool_name=tool_name,
                error=str(e),
            )
            result = TestResult(success=False, message=f"Error: {type(e).__name__}: {str(e)[:200]}")

        # Record audit for the test probe
        audit = AuditService(repository=AuditRepository(db_session))
        try:
            if result.success:
                await audit.record_success(
                    svc.name,
                    tool_name,
                    {"action": "test_probe"},
                    start,
                    client_name=f"web:{ctx.username}",
                )
            else:
                await audit.record_error(
                    svc.name,
                    tool_name,
                    {"action": "test_probe"},
                    start,
                    Exception(result.message),
                    client_name=f"web:{ctx.username}",
                )
        except Exception:
            structlog.get_logger().exception("Failed to record audit for tool test")

        return result

    @post("/{service_id:uuid}/import-openapi")
    async def import_openapi(
        self,
        request: Request,
        db_session: AsyncSession,
        service_manager: ServiceManager,
        tool_registry: ToolRegistry,
        service_id: UUID,
        data: ImportOpenAPIRequest,
    ) -> ImportOpenAPIResult:
        ctx: AuthContext = request.user
        ctx.require_service_access(service_id)

        await service_manager.get_by_id(service_id)

        parser = OpenAPIParser()
        specs = parser.parse(data.spec)

        from domain.validation import validate_tool_name

        repo = GenericToolDefinitionRepository(db_session)
        existing_tools = await repo.get_by_service_id(service_id)
        existing_names = {t.tool_name for t in existing_tools}
        created = []
        skipped = []
        for spec in specs:
            if spec.tool_name in existing_names:
                skipped.append(spec.tool_name)
                continue
            try:
                validate_tool_name(spec.tool_name)
            except ValueError:
                skipped.append(spec.tool_name)
                continue
            await repo.create(
                service_id=service_id,
                tool_name=spec.tool_name,
                description=spec.description,
                http_method=spec.http_method,
                path_template=spec.path_template,
                params_schema=spec.params_schema,
            )
            created.append(spec.tool_name)

        await db_session.commit()
        await tool_registry.refresh()
        return ImportOpenAPIResult(
            status="imported",
            imported=created,
            skipped=skipped,
            tools_count=len(created),
        )
