"""Parse OpenAPI 3.x specs into GenericToolSpec definitions."""

import json
import re
from typing import Any

import yaml

from domain.entities.generic_tool_spec import GenericToolSpec


class OpenAPIParser:
    """Converts OpenAPI 3.x specs into MCP tool definitions."""

    @staticmethod
    def parse(spec_content: str) -> list[GenericToolSpec]:
        """Parse an OpenAPI spec (JSON or YAML) and return tool definitions."""
        try:
            spec = json.loads(spec_content)
        except json.JSONDecodeError:
            spec = yaml.safe_load(spec_content)

        if not isinstance(spec, dict):
            raise ValueError("Invalid OpenAPI spec: expected a JSON/YAML object")

        paths = spec.get("paths", {})
        tools: list[GenericToolSpec] = []

        for path, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue
            for method in ("get", "post", "put", "patch", "delete"):
                operation = path_item.get(method)
                if not isinstance(operation, dict):
                    continue

                op_id = operation.get("operationId", "")
                tool_name = op_id or OpenAPIParser._path_to_name(method, path)
                description = (
                    operation.get("summary", "")
                    or operation.get("description", "")
                    or f"{method.upper()} {path}"
                )

                params_schema = OpenAPIParser._build_params_schema(
                    operation,
                    path,
                    spec,
                )
                tools.append(
                    GenericToolSpec(
                        tool_name=tool_name,
                        description=description[:500],
                        http_method=method.upper(),
                        path_template=path,
                        params_schema=params_schema,
                    )
                )

        return tools

    @staticmethod
    def _path_to_name(method: str, path: str) -> str:
        """Convert a method + path to a snake_case tool name."""
        # /api/users/{id}/posts -> api_users_id_posts
        clean = re.sub(r"[{}]", "", path)
        clean = re.sub(r"[^a-zA-Z0-9/]", "", clean)
        parts = [p for p in clean.split("/") if p]
        return f"{method}_{'_'.join(parts)}"

    @staticmethod
    def _build_params_schema(
        operation: dict[str, Any],
        path: str,
        spec: dict[str, Any],
        _depth: int = 0,
    ) -> dict[str, Any]:
        """Build a JSON Schema for the tool's parameters."""
        properties: dict[str, Any] = {}
        required: list[str] = []

        # Path parameters
        for param in operation.get("parameters", []):
            param = OpenAPIParser._resolve_ref(param, spec, _depth)
            name = param.get("name", "")
            if not name:
                continue
            schema = param.get("schema", {"type": "string"})
            properties[name] = {
                "type": schema.get("type", "string"),
                "description": param.get("description", ""),
            }
            if param.get("required", param.get("in") == "path"):
                required.append(name)

        # Request body
        body = operation.get("requestBody", {})
        body = OpenAPIParser._resolve_ref(body, spec, _depth)
        if body:
            content = body.get("content", {})
            json_content = content.get("application/json", {})
            body_schema = json_content.get("schema", {})
            body_schema = OpenAPIParser._resolve_ref(body_schema, spec, _depth)
            if body_schema.get("type") == "object":
                for prop_name, prop_schema in body_schema.get("properties", {}).items():
                    prop_schema = OpenAPIParser._resolve_ref(prop_schema, spec, _depth)
                    properties[prop_name] = {
                        "type": prop_schema.get("type", "string"),
                        "description": prop_schema.get("description", ""),
                    }
                for req in body_schema.get("required", []):
                    if req not in required:
                        required.append(req)

        result: dict[str, Any] = {"type": "object", "properties": properties}
        if required:
            result["required"] = required
        return result

    @staticmethod
    def _resolve_ref(obj: Any, spec: dict[str, Any], _depth: int = 0) -> dict:
        """Recursively resolve $ref pointers. Max depth prevents circular refs."""
        if not isinstance(obj, dict):
            return {}
        ref = obj.get("$ref")
        if not ref or not isinstance(ref, str):
            return obj
        if _depth > 10:
            return {}
        # e.g. #/components/schemas/User
        parts = ref.lstrip("#/").split("/")
        current: Any = spec
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part, {})
            else:
                return {}
        resolved = current if isinstance(current, dict) else {}
        # Recurse in case the resolved object itself contains a $ref
        return OpenAPIParser._resolve_ref(resolved, spec, _depth + 1)
