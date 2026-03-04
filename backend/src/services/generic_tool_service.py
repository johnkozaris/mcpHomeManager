"""Application service for generic tool lifecycle and import workflows."""

import json
from typing import Any
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from domain.constants.http_methods import HTTP_METHODS
from domain.ports.generic_tool_repository import GenericToolRow, IGenericToolRepository
from domain.validation import validate_tool_name
from services.openapi_parser import OpenAPIParser


class GenericToolValidationError(ValueError):
    """Raised when generic tool input is invalid."""


class GenericToolConflictError(ValueError):
    """Raised when creating a tool that already exists."""


class GenericToolNotFoundError(LookupError):
    """Raised when a tool does not exist on the target service."""


class GenericToolService:
    """Encapsulates generic tool CRUD + OpenAPI import with consistent validation."""

    def __init__(self, repository: IGenericToolRepository) -> None:
        self._repo = repository

    @staticmethod
    def parse_params_schema_json(raw: str) -> dict[str, Any]:
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise GenericToolValidationError(f"Invalid params_schema JSON: {exc}") from exc
        if not isinstance(parsed, dict):
            raise GenericToolValidationError("params_schema must decode to a JSON object")
        return parsed

    @staticmethod
    def _normalize_http_method(method: str) -> str:
        normalized = method.upper()
        if normalized not in HTTP_METHODS:
            allowed = ", ".join(sorted(HTTP_METHODS))
            raise GenericToolValidationError(
                f"Invalid HTTP method '{method}'. Use: {allowed}"
            )
        return normalized

    async def create_tool(
        self,
        service_id: UUID,
        *,
        tool_name: str,
        description: str,
        http_method: str,
        path_template: str,
        params_schema: dict[str, Any],
    ) -> GenericToolRow:
        try:
            validate_tool_name(tool_name)
        except ValueError as exc:
            raise GenericToolValidationError(str(exc)) from exc

        method = self._normalize_http_method(http_method)
        try:
            return await self._repo.create(
                service_id=service_id,
                tool_name=tool_name,
                description=description,
                http_method=method,
                path_template=path_template,
                params_schema=params_schema,
            )
        except IntegrityError as exc:
            raise GenericToolConflictError(
                f"Tool '{tool_name}' already exists on this service"
            ) from exc

    async def update_tool(
        self,
        service_id: UUID,
        tool_name: str,
        *,
        description: str | None = None,
        http_method: str | None = None,
        path_template: str | None = None,
        params_schema: dict[str, Any] | None = None,
    ) -> GenericToolRow:
        normalized_method = (
            self._normalize_http_method(http_method) if http_method is not None else None
        )

        row = await self._repo.update(
            service_id,
            tool_name,
            description=description,
            http_method=normalized_method,
            path_template=path_template,
            params_schema=params_schema,
        )
        if row is None:
            raise GenericToolNotFoundError(f"Tool '{tool_name}' not found")
        return row

    async def delete_tool(self, service_id: UUID, tool_name: str) -> None:
        deleted = await self._repo.delete(service_id, tool_name)
        if not deleted:
            raise GenericToolNotFoundError(f"Tool '{tool_name}' not found")

    async def get_tool(self, service_id: UUID, tool_name: str) -> GenericToolRow:
        row = await self._repo.get_by_name(service_id, tool_name)
        if row is None:
            raise GenericToolNotFoundError(f"Tool '{tool_name}' not found")
        return row

    async def import_openapi(
        self,
        service_id: UUID,
        spec: str,
    ) -> tuple[list[str], list[str]]:
        parser = OpenAPIParser()
        specs = parser.parse(spec)

        existing_tools = await self._repo.get_by_service_id(service_id)
        existing_names = {tool.tool_name for tool in existing_tools}

        imported: list[str] = []
        skipped: list[str] = []
        for candidate in specs:
            if candidate.tool_name in existing_names:
                skipped.append(candidate.tool_name)
                continue

            try:
                validate_tool_name(candidate.tool_name)
            except ValueError:
                skipped.append(candidate.tool_name)
                continue

            await self._repo.create(
                service_id=service_id,
                tool_name=candidate.tool_name,
                description=candidate.description,
                http_method=self._normalize_http_method(candidate.http_method),
                path_template=candidate.path_template,
                params_schema=candidate.params_schema,
            )
            imported.append(candidate.tool_name)

        return imported, skipped

