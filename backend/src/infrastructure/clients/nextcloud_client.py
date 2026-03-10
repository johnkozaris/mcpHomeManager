import base64
import posixpath
from typing import Any
from urllib.parse import quote, unquote, urlsplit

from defusedxml import ElementTree
from defusedxml.common import DefusedXmlException

from domain.entities.service_connection import ServiceType
from domain.entities.tool_definition import ToolDefinition
from domain.exceptions import ServiceConnectionError, ToolExecutionError
from infrastructure.clients.base_client import BaseServiceClient

_TOOLS = [
    ToolDefinition(
        name="nextcloud_list_files",
        http_method="PROPFIND",
        path_template="/remote.php/dav/files/{resolved_user}{path}",
        service_type=ServiceType.NEXTCLOUD,
        description="List files and folders in a Nextcloud directory via documented WebDAV",
        parameters_schema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path (e.g. / or /Documents)",
                    "default": "/",
                },
            },
        },
    ),
    ToolDefinition(
        name="nextcloud_search_files",
        http_method="GET",
        path_template="/ocs/v2.php/search/providers/files/search",
        service_type=ServiceType.NEXTCLOUD,
        description="Search for files by name across Nextcloud",
        parameters_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search term"},
            },
            "required": ["query"],
        },
    ),
    ToolDefinition(
        name="nextcloud_list_notes",
        http_method="GET",
        path_template="/index.php/apps/notes/api/v1/notes",
        service_type=ServiceType.NEXTCLOUD,
        description="List all notes from Nextcloud Notes app",
        parameters_schema={"type": "object", "properties": {}},
    ),
    ToolDefinition(
        name="nextcloud_get_note",
        http_method="GET",
        path_template="/index.php/apps/notes/api/v1/notes/{note_id}",
        service_type=ServiceType.NEXTCLOUD,
        description="Get a specific note by ID",
        parameters_schema={
            "type": "object",
            "properties": {
                "note_id": {"type": "integer", "description": "Note ID"},
            },
            "required": ["note_id"],
        },
    ),
    ToolDefinition(
        name="nextcloud_user_status",
        http_method="GET",
        path_template="/ocs/v1.php/cloud/user",
        service_type=ServiceType.NEXTCLOUD,
        description="Get Nextcloud user metadata via documented OCS endpoint",
        parameters_schema={"type": "object", "properties": {}},
    ),
]

_DAV_NAMESPACES = {
    "d": "DAV:",
    "oc": "http://owncloud.org/ns",
    "nc": "http://nextcloud.org/ns",
}

_DAV_PROPFIND_BODY = """<?xml version="1.0" encoding="UTF-8"?>
<d:propfind xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns" xmlns:nc="http://nextcloud.org/ns">
  <d:prop>
    <d:displayname />
    <d:getlastmodified />
    <d:getcontentlength />
    <d:getcontenttype />
    <d:getetag />
    <d:resourcetype />
    <oc:fileid />
    <oc:permissions />
    <oc:size />
  </d:prop>
</d:propfind>
"""


class NextcloudClient(BaseServiceClient):
    service_name = "nextcloud"

    def __init__(self, base_url: str, api_token: str, **kwargs: Any) -> None:
        super().__init__(base_url, api_token, **kwargs)
        base_path = unquote(urlsplit(self._base_url).path.rstrip("/"))
        self._dav_href_base = (
            f"{base_path}/remote.php/dav/files" if base_path else "/remote.php/dav/files"
        )
        self._notes_api_v1_available: bool | None = None

    def _build_headers(self, token: str) -> dict[str, str]:
        # Token format: "user:app-password"
        encoded = base64.b64encode(token.encode()).decode()
        return {
            "Authorization": f"Basic {encoded}",
            "OCS-APIRequest": "true",
            "Accept": "application/json",
        }

    async def health_check(self) -> bool:
        try:
            data = await self._request_ocs_json(
                "/ocs/v1.php/cloud/capabilities", tool_name="nextcloud_health_check"
            )
        except ServiceConnectionError, ToolExecutionError:
            return False
        return isinstance(data, dict) and isinstance(data.get("capabilities"), dict)

    def get_tool_definitions(self) -> list[ToolDefinition]:
        return list(_TOOLS)

    async def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        match tool_name:
            case "nextcloud_list_files":
                return await self._list_files(arguments.get("path", "/"))
            case "nextcloud_search_files":
                return await self._request(
                    "GET",
                    "/ocs/v2.php/search/providers/files/search",
                    params={"term": arguments["query"], "format": "json"},
                )
            case "nextcloud_list_notes":
                await self._ensure_notes_api_available("nextcloud_list_notes")
                return await self._request("GET", "/index.php/apps/notes/api/v1/notes")
            case "nextcloud_get_note":
                note_id = int(arguments["note_id"])
                await self._ensure_notes_api_available("nextcloud_get_note")
                return await self._request("GET", f"/index.php/apps/notes/api/v1/notes/{note_id}")
            case "nextcloud_user_status":
                return await self._request_ocs_json(
                    "/ocs/v1.php/cloud/user", tool_name="nextcloud_user_status"
                )
            case _:
                raise ToolExecutionError(tool_name, f"Unknown tool: {tool_name}")

    async def _list_files(self, path: Any) -> dict[str, Any]:
        requested_path = self._normalize_nextcloud_path(path)
        user_id = await self._resolve_dav_user_id()
        encoded_path = self._encode_dav_path(requested_path)
        response = await self._client.request(
            "PROPFIND",
            f"/remote.php/dav/files/{quote(user_id, safe='')}{encoded_path}",
            headers={
                "Accept": "application/xml, text/xml;q=0.9",
                "Content-Type": "application/xml; charset=utf-8",
                "Depth": "1",
            },
            content=_DAV_PROPFIND_BODY,
        )
        response.raise_for_status()
        return self._parse_propfind_response(requested_path, user_id, response.text)

    async def _resolve_dav_user_id(self) -> str:
        data = await self._request_ocs_json(
            "/ocs/v1.php/cloud/user", tool_name="nextcloud_list_files"
        )
        user_id = data.get("id") or data.get("uid")
        if not isinstance(user_id, str) or not user_id:
            raise ToolExecutionError(
                "nextcloud_list_files",
                "Nextcloud user metadata did not include a WebDAV user id",
            )
        return user_id

    async def _ensure_notes_api_available(self, tool_name: str) -> None:
        if self._notes_api_v1_available is True:
            return
        if self._notes_api_v1_available is False:
            raise ToolExecutionError(
                tool_name,
                "Nextcloud Notes API v1 is unavailable on this server. Enable the Notes app first.",
            )

        data = await self._request_ocs_json("/ocs/v2.php/cloud/capabilities", tool_name=tool_name)
        capabilities = data.get("capabilities")
        notes_capabilities = capabilities.get("notes") if isinstance(capabilities, dict) else None
        api_versions = (
            notes_capabilities.get("api_version") if isinstance(notes_capabilities, dict) else None
        )
        if isinstance(api_versions, list) and any(
            self._supports_notes_api_v1(version) for version in api_versions
        ):
            self._notes_api_v1_available = True
            return

        self._notes_api_v1_available = False
        raise ToolExecutionError(
            tool_name,
            "Nextcloud Notes API v1 is unavailable on this server. Enable the Notes app first.",
        )

    async def _request_ocs_json(
        self,
        path: str,
        *,
        tool_name: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        ocs_params = {"format": "json"}
        if params:
            ocs_params.update(params)
        payload = await self._request("GET", path, params=ocs_params)
        if not isinstance(payload, dict):
            raise ToolExecutionError(
                tool_name, "Expected JSON response from Nextcloud OCS endpoint"
            )
        ocs = payload.get("ocs")
        if not isinstance(ocs, dict):
            raise ToolExecutionError(tool_name, "Missing OCS wrapper in Nextcloud response")
        meta = ocs.get("meta")
        if not isinstance(meta, dict):
            raise ToolExecutionError(tool_name, "Missing OCS meta block in Nextcloud response")
        status = str(meta.get("status", "")).lower()
        status_code = meta.get("statuscode")
        if isinstance(status_code, int):
            status_code_int = status_code
        elif isinstance(status_code, str):
            try:
                status_code_int = int(status_code)
            except ValueError as exc:
                raise ToolExecutionError(
                    tool_name, "Invalid OCS status code in Nextcloud response"
                ) from exc
        else:
            raise ToolExecutionError(tool_name, "Invalid OCS status code in Nextcloud response")
        if status != "ok" or status_code_int >= 400:
            message = meta.get("message") or "OCS request failed"
            raise ToolExecutionError(tool_name, f"OCS request failed: {message}")
        data = ocs.get("data")
        if not isinstance(data, dict):
            raise ToolExecutionError(tool_name, "Expected OCS data object in Nextcloud response")
        return data

    def _parse_propfind_response(
        self, requested_path: str, user_id: str, response_text: str
    ) -> dict[str, Any]:
        try:
            root = ElementTree.fromstring(
                response_text,
                forbid_dtd=True,
                forbid_entities=True,
                forbid_external=True,
            )
        except (DefusedXmlException, ElementTree.ParseError) as exc:
            raise ToolExecutionError(
                "nextcloud_list_files",
                "Invalid or unsafe XML returned from Nextcloud WebDAV listing",
            ) from exc

        entries: list[dict[str, Any]] = []
        current_directory: dict[str, Any] | None = None
        for response in root.findall("d:response", _DAV_NAMESPACES):
            item = self._parse_propfind_item(response, user_id)
            if item is None:
                continue
            if item["path"] == requested_path:
                current_directory = item
                continue
            entries.append(item)

        entries.sort(key=lambda item: (item["type"] != "directory", item["name"].lower()))
        return {
            "path": requested_path,
            "directory": current_directory
            or {
                "name": requested_path.rsplit("/", 1)[-1] or user_id,
                "path": requested_path,
                "type": "directory",
            },
            "entries": entries,
            "total": len(entries),
        }

    def _parse_propfind_item(self, response: Any, user_id: str) -> dict[str, Any] | None:
        href_text = response.findtext("d:href", default="", namespaces=_DAV_NAMESPACES)
        item_path = self._href_to_nextcloud_path(href_text, user_id)
        if item_path is None:
            return None

        prop = self._successful_propfind_props(response)
        if prop is None:
            return None

        is_directory = prop.find("d:resourcetype/d:collection", _DAV_NAMESPACES) is not None
        display_name = prop.findtext(
            "d:displayname", default="", namespaces=_DAV_NAMESPACES
        ).strip()
        if not display_name:
            display_name = item_path.rsplit("/", 1)[-1] or user_id

        content_length = self._optional_int(
            prop.findtext("d:getcontentlength", default=None, namespaces=_DAV_NAMESPACES)
        )
        aggregate_size = self._optional_int(
            prop.findtext("oc:size", default=None, namespaces=_DAV_NAMESPACES)
        )

        return {
            "name": display_name,
            "path": item_path,
            "type": "directory" if is_directory else "file",
            "size": aggregate_size if is_directory else content_length,
            "content_type": prop.findtext(
                "d:getcontenttype", default=None, namespaces=_DAV_NAMESPACES
            ),
            "etag": self._strip_quotes(
                prop.findtext("d:getetag", default=None, namespaces=_DAV_NAMESPACES)
            ),
            "last_modified": prop.findtext(
                "d:getlastmodified", default=None, namespaces=_DAV_NAMESPACES
            ),
            "permissions": prop.findtext(
                "oc:permissions", default=None, namespaces=_DAV_NAMESPACES
            ),
            "file_id": prop.findtext("oc:fileid", default=None, namespaces=_DAV_NAMESPACES),
        }

    def _successful_propfind_props(self, response: Any) -> Any | None:
        for propstat in response.findall("d:propstat", _DAV_NAMESPACES):
            status = propstat.findtext("d:status", default="", namespaces=_DAV_NAMESPACES)
            if " 2" not in status:
                continue
            prop = propstat.find("d:prop", _DAV_NAMESPACES)
            if prop is not None:
                return prop
        return None

    @staticmethod
    def _normalize_nextcloud_path(path: Any) -> str:
        value = "/" if path in (None, "") else str(path)
        if not value.startswith("/"):
            value = f"/{value}"
        if any(segment == ".." for segment in value.split("/")):
            raise ToolExecutionError(
                "nextcloud_list_files", "Parent directory traversal is not allowed"
            )
        normalized = posixpath.normpath(value)
        if normalized == ".":
            normalized = "/"
        if not normalized.startswith("/"):
            normalized = f"/{normalized}"
        return normalized

    @staticmethod
    def _encode_dav_path(path: str) -> str:
        if path == "/":
            return ""
        segments = [quote(segment, safe="") for segment in path.strip("/").split("/")]
        return "/" + "/".join(segments)

    def _href_to_nextcloud_path(self, href_text: str, user_id: str) -> str | None:
        href_path = unquote(urlsplit(href_text).path or href_text)
        prefixes = (
            f"{self._dav_href_base}/{user_id}",
            f"/remote.php/dav/files/{user_id}",
        )
        for prefix in dict.fromkeys(prefixes):
            if href_path.startswith(prefix):
                relative_path = href_path[len(prefix) :] or "/"
                return self._normalize_nextcloud_path(relative_path)
        return None

    @staticmethod
    def _optional_int(value: str | None) -> int | None:
        if value is None or value == "":
            return None
        try:
            return int(value)
        except ValueError:
            return None

    @staticmethod
    def _strip_quotes(value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip('"')

    @staticmethod
    def _supports_notes_api_v1(version: Any) -> bool:
        return isinstance(version, str) and version.split(".", 1)[0] == "1"
