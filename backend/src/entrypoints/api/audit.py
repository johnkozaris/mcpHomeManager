from datetime import datetime

from litestar import Controller, Request, get
from litestar.params import Parameter

from entrypoints.api.schemas import AuditEntryResponse, AuditListResponse
from security.auth_context import AuthContext
from services.audit_service import AuditService
from services.service_manager import ServiceManager


class AuditController(Controller):
    path = "/api/audit"

    @get("/")
    async def list_audit_entries(
        self,
        request: Request,
        audit_service: AuditService,
        service_manager: ServiceManager,
        limit: int = Parameter(default=50, ge=1, le=200),
        offset: int = Parameter(default=0, ge=0),
        service_name: str | None = None,
        tool_name: str | None = None,
        status: str | None = None,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
    ) -> AuditListResponse:
        ctx: AuthContext = request.user

        # Non-admin: resolve which service names are allowed
        allowed_names: set[str] | None = None
        if not ctx.is_admin:
            all_services = await service_manager.list_all()
            allowed_names = {s.name for s in all_services if str(s.id) in ctx.allowed_service_ids}
            # If requesting a specific service, block if not allowed
            if service_name and service_name not in allowed_names:
                return AuditListResponse(items=[], total=0)

        entries = await audit_service.get_recent(
            limit=limit,
            offset=offset,
            service_name=service_name,
            tool_name=tool_name,
            status=status,
            created_after=created_after,
            created_before=created_before,
            allowed_service_names=allowed_names,
        )
        total = await audit_service.count(
            service_name=service_name,
            tool_name=tool_name,
            status=status,
            created_after=created_after,
            created_before=created_before,
            allowed_service_names=allowed_names,
        )

        results: list[AuditEntryResponse] = []
        for e in entries:
            if e.id is None:
                continue
            results.append(
                AuditEntryResponse(
                    id=e.id,
                    service_name=e.service_name,
                    tool_name=e.tool_name,
                    input_summary=e.input_summary,
                    status=e.status.value,
                    duration_ms=e.duration_ms,
                    error_message=e.error_message,
                    client_name=e.client_name,
                    created_at=e.created_at,
                )
            )
        return AuditListResponse(items=results, total=total)
