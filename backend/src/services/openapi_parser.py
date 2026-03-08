"""Parse OpenAPI 3.x specs into GenericToolSpec definitions."""

import json
import re
from dataclasses import dataclass
from typing import Any

import yaml

from domain.constants.http_methods import HTTP_METHODS
from domain.entities.generic_tool_spec import REQUEST_SHAPE_METADATA_KEY, GenericToolSpec

_OPENAPI_HTTP_METHODS = ("get", "post", "put", "patch", "delete", "head", "options", "trace")
_SUPPORTED_BODY_MEDIA_TYPES = {
    "application/json": "json",
    "application/x-www-form-urlencoded": "form-urlencoded",
}
_OPENAPI_VERSION_PATTERN = re.compile(r"^(?P<major>\d+)(?:\.\d+){0,2}(?:[-+][0-9A-Za-z.-]+)?$")


@dataclass(frozen=True)
class OpenAPIParseResult:
    tools: list[GenericToolSpec]
    warnings: list[str]


class OpenAPIParser:
    """Converts OpenAPI 3.x specs into MCP tool definitions."""

    @staticmethod
    def parse(spec_content: str) -> OpenAPIParseResult:
        """Parse an OpenAPI spec (JSON or YAML) and return tool definitions."""
        try:
            spec = json.loads(spec_content)
        except json.JSONDecodeError:
            spec = yaml.safe_load(spec_content)

        if not isinstance(spec, dict):
            raise ValueError("Invalid OpenAPI spec: expected a JSON/YAML object")

        version = spec.get("openapi")
        if not isinstance(version, str):
            raise ValueError(
                "Invalid OpenAPI spec: expected a root 'openapi' field with a 3.x version"
            )

        version_match = _OPENAPI_VERSION_PATTERN.fullmatch(version.strip())
        if version_match is None:
            raise ValueError(f"Invalid OpenAPI version '{version}'")
        if version_match.group("major") != "3":
            raise ValueError(f"Unsupported OpenAPI version '{version}': expected 3.x")

        paths = spec.get("paths", {})
        tools: list[GenericToolSpec] = []
        warnings: list[str] = []

        for path, path_item in paths.items():
            resolved_path_item = OpenAPIParser._resolve_ref(path_item, spec)
            if not isinstance(resolved_path_item, dict):
                continue

            for method in _OPENAPI_HTTP_METHODS:
                operation = resolved_path_item.get(method)
                if not isinstance(operation, dict):
                    continue

                if method.upper() not in HTTP_METHODS:
                    warnings.append(f"Skipped {method.upper()} {path}: unsupported HTTP method")
                    continue

                tool = OpenAPIParser._build_tool_spec(
                    method=method,
                    path=path,
                    path_item=resolved_path_item,
                    operation=operation,
                    spec=spec,
                    warnings=warnings,
                )
                if tool is not None:
                    tools.append(tool)

        return OpenAPIParseResult(tools=tools, warnings=warnings)

    @staticmethod
    def _build_tool_spec(
        *,
        method: str,
        path: str,
        path_item: dict[str, Any],
        operation: dict[str, Any],
        spec: dict[str, Any],
        warnings: list[str],
    ) -> GenericToolSpec | None:
        op_id = operation.get("operationId", "")
        tool_name = op_id or OpenAPIParser._path_to_name(method, path)
        description = (
            operation.get("summary", "")
            or operation.get("description", "")
            or f"{method.upper()} {path}"
        )

        params_schema, warning = OpenAPIParser._build_params_schema(
            path_template=path,
            path_item=path_item,
            operation=operation,
            spec=spec,
            tool_name=tool_name,
        )
        if params_schema is None:
            warnings.append(warning or f"Skipped {tool_name}: unsupported request shape")
            return None

        return GenericToolSpec(
            tool_name=tool_name,
            description=description[:500],
            http_method=method.upper(),
            path_template=path,
            params_schema=params_schema,
        )

    @staticmethod
    def _path_to_name(method: str, path: str) -> str:
        """Convert a method + path to a snake_case tool name."""
        clean = re.sub(r"[{}]", "", path)
        clean = re.sub(r"[^a-zA-Z0-9/]", "", clean)
        parts = [p for p in clean.split("/") if p]
        return f"{method}_{'_'.join(parts)}"

    @staticmethod
    def _build_params_schema(
        *,
        path_template: str,
        path_item: dict[str, Any],
        operation: dict[str, Any],
        spec: dict[str, Any],
        tool_name: str,
    ) -> tuple[dict[str, Any] | None, str | None]:
        """Build a JSON Schema for the tool's parameters."""
        properties: dict[str, Any] = {}
        required: list[str] = []
        request_shape: dict[str, Any] = {"version": 1}

        parameters, parameter_warnings = OpenAPIParser._merge_parameters(
            path_item.get("parameters", []),
            operation.get("parameters", []),
            spec,
            tool_name,
        )
        if parameter_warnings:
            return None, parameter_warnings[0]

        parameter_metadata: dict[str, Any] = {}
        source_by_name: dict[str, str] = {}

        for param in parameters:
            name = param.get("name", "")
            if not name:
                continue

            location = param.get("in")
            if location not in {"path", "query", "header", "cookie"}:
                return None, f"Skipped {tool_name}: unsupported parameter location '{location}'"

            if name in source_by_name:
                return None, (
                    f"Skipped {tool_name}: duplicate argument name '{name}' "
                    "across multiple request parts"
                )

            schema = OpenAPIParser._materialize_schema(
                param.get("schema", {"type": "string"}),
                spec,
            )
            if not schema:
                schema = {"type": "string"}
            if param.get("description") and not schema.get("description"):
                schema["description"] = param["description"]
            properties[name] = schema
            source_by_name[name] = location
            parameter_metadata[name] = {
                "in": location,
                "name": name,
                "required": param.get("required", location == "path"),
            }
            if "style" in param:
                parameter_metadata[name]["style"] = param["style"]
            if "explode" in param:
                parameter_metadata[name]["explode"] = param["explode"]
            if parameter_metadata[name]["required"] and name not in required:
                required.append(name)

        missing_path_params = [
            name
            for name in re.findall(r"\{([^}]+)\}", path_template)
            if parameter_metadata.get(name, {}).get("in") != "path"
        ]
        if missing_path_params:
            missing = ", ".join(missing_path_params)
            return None, (
                "Skipped "
                f"{tool_name}: path template parameters missing OpenAPI path definitions "
                f"({missing})"
            )

        if parameter_metadata:
            request_shape["parameters"] = parameter_metadata

        body_metadata, body_warning = OpenAPIParser._build_body_schema(
            operation.get("requestBody", {}),
            spec,
            properties,
            required,
            source_by_name,
            tool_name,
        )
        if body_warning is not None:
            return None, body_warning
        if body_metadata is not None:
            request_shape["body"] = body_metadata

        result: dict[str, Any] = {"type": "object", "properties": properties}
        if required:
            result["required"] = required
        if len(request_shape) > 1:
            result[REQUEST_SHAPE_METADATA_KEY] = request_shape
        return result, None

    @staticmethod
    def _build_body_schema(
        request_body: Any,
        spec: dict[str, Any],
        properties: dict[str, Any],
        required: list[str],
        source_by_name: dict[str, str],
        tool_name: str,
    ) -> tuple[dict[str, Any] | None, str | None]:
        body = OpenAPIParser._resolve_ref(request_body, spec)
        if not body:
            return None, None

        content = body.get("content", {})
        if not isinstance(content, dict) or not content:
            return None, f"Skipped {tool_name}: request body is missing content definitions"

        supported_media_type: str | None = None
        supported_content: dict[str, Any] | None = None
        for media_type in _SUPPORTED_BODY_MEDIA_TYPES:
            candidate = content.get(media_type)
            if isinstance(candidate, dict):
                supported_media_type = media_type
                supported_content = candidate
                break

        if supported_media_type is None or supported_content is None:
            unsupported = ", ".join(sorted(content.keys()))
            return None, (
                f"Skipped {tool_name}: unsupported request body media types ({unsupported})"
            )

        body_schema = OpenAPIParser._materialize_schema(supported_content.get("schema", {}), spec)
        if body_schema.get("type") != "object":
            return None, (
                f"Skipped {tool_name}: unsupported {supported_media_type} request body shape "
                f"'{body_schema.get('type', 'unknown')}'"
            )

        body_properties = body_schema.get("properties", {})
        if not isinstance(body_properties, dict):
            return None, (
                f"Skipped {tool_name}: unsupported {supported_media_type} "
                "request body properties"
            )

        body_property_names: list[str] = []
        for prop_name, prop_schema in body_properties.items():
            if prop_name in source_by_name:
                return None, (
                    f"Skipped {tool_name}: duplicate argument name '{prop_name}' across body and "
                    "other request parts"
                )
            schema = OpenAPIParser._materialize_schema(prop_schema, spec)
            if not schema:
                schema = {"type": "string"}
            properties[prop_name] = schema
            source_by_name[prop_name] = "body"
            body_property_names.append(prop_name)

        for body_required in body_schema.get("required", []):
            if body_required not in required:
                required.append(body_required)

        return (
            {
                "mediaType": supported_media_type,
                "encoding": _SUPPORTED_BODY_MEDIA_TYPES[supported_media_type],
                "propertyNames": body_property_names,
                "required": body.get("required", False),
            },
            None,
        )

    @staticmethod
    def _merge_parameters(
        path_parameters: Any,
        operation_parameters: Any,
        spec: dict[str, Any],
        tool_name: str,
    ) -> tuple[list[dict[str, Any]], list[str]]:
        merged: dict[tuple[str, str], dict[str, Any]] = {}
        warnings: list[str] = []

        for source in (path_parameters, operation_parameters):
            if not isinstance(source, list):
                continue
            for raw_param in source:
                param = OpenAPIParser._resolve_ref(raw_param, spec)
                if not param:
                    warnings.append(f"Skipped {tool_name}: unsupported parameter reference")
                    continue
                name = param.get("name")
                location = param.get("in")
                if not name or not location:
                    warnings.append(f"Skipped {tool_name}: parameter is missing name or location")
                    continue
                if "content" in param and "schema" not in param:
                    warnings.append(
                        f"Skipped {tool_name}: parameter '{name}' uses unsupported "
                        "content-based encoding"
                    )
                    continue
                merged[(location, name)] = param

        return list(merged.values()), warnings

    @staticmethod
    def _materialize_schema(obj: Any, spec: dict[str, Any], _depth: int = 0) -> dict[str, Any]:
        """Recursively resolve refs inside a JSON Schema fragment."""
        if _depth > 20:
            return {}

        resolved = OpenAPIParser._resolve_ref(obj, spec, _depth)
        if not isinstance(resolved, dict):
            return {}

        materialized: dict[str, Any] = {}
        for key, value in resolved.items():
            if key == "$ref":
                continue
            if key == "properties" and isinstance(value, dict):
                materialized[key] = {
                    prop_name: OpenAPIParser._materialize_schema(prop_schema, spec, _depth + 1)
                    for prop_name, prop_schema in value.items()
                }
                continue
            if key in {"items", "additionalProperties", "not"} and isinstance(value, dict):
                materialized[key] = OpenAPIParser._materialize_schema(value, spec, _depth + 1)
                continue
            if key in {"allOf", "anyOf", "oneOf", "prefixItems"} and isinstance(value, list):
                materialized[key] = [
                    OpenAPIParser._materialize_schema(item, spec, _depth + 1)
                    if isinstance(item, dict)
                    else item
                    for item in value
                ]
                continue
            materialized[key] = value
        return materialized

    @staticmethod
    def _resolve_ref(obj: Any, spec: dict[str, Any], _depth: int = 0) -> dict[str, Any]:
        """Recursively resolve $ref pointers. Max depth prevents circular refs."""
        if not isinstance(obj, dict):
            return {}
        ref = obj.get("$ref")
        if not ref or not isinstance(ref, str):
            return obj
        if _depth > 10:
            return {}
        if ref == "#":
            return spec
        if not ref.startswith("#/"):
            return {}
        parts = ref[2:].split("/")
        current: Any = spec
        for part in parts:
            decoded_part = OpenAPIParser._decode_json_pointer_token(part)
            if decoded_part is None:
                return {}
            if isinstance(current, dict):
                current = current.get(decoded_part, {})
            else:
                return {}
        resolved = current if isinstance(current, dict) else {}
        return OpenAPIParser._resolve_ref(resolved, spec, _depth + 1)

    @staticmethod
    def _decode_json_pointer_token(token: str) -> str | None:
        if re.search(r"~(?![01])", token):
            return None
        return token.replace("~1", "/").replace("~0", "~")
