"""Tests for the Nextcloud service client."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from domain.entities.service_connection import ServiceType
from domain.exceptions import ToolExecutionError
from infrastructure.clients.nextcloud_client import NextcloudClient


def _mock_json_response(json_data, status_code=200):
    """Build a mock JSON httpx response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = {"content-type": "application/json"}
    resp.json.return_value = json_data
    resp.text = ""
    resp.raise_for_status = MagicMock()
    return resp


def _mock_xml_response(text_data: str, status_code=207):
    """Build a mock XML httpx response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = {"content-type": "application/xml"}
    resp.text = text_data
    resp.raise_for_status = MagicMock()
    return resp


def _patch_client_transport(client: NextcloudClient):
    """Replace the httpx AsyncClient with an AsyncMock so no real HTTP calls are made."""
    mock = AsyncMock()
    mock.request = AsyncMock()
    mock.headers = {}
    client._client = mock
    return mock


def _ocs_response(data, *, status: str = "ok", statuscode: int = 100, message: str = "OK"):
    return {
        "ocs": {
            "meta": {"status": status, "statuscode": statuscode, "message": message},
            "data": data,
        }
    }


_PROPFIND_XML = """<?xml version="1.0" encoding="UTF-8"?>
<d:multistatus xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns">
  <d:response>
    <d:href>/remote.php/dav/files/maria/Documents/</d:href>
    <d:propstat>
      <d:prop>
        <d:displayname>Documents</d:displayname>
        <d:resourcetype><d:collection /></d:resourcetype>
        <oc:size>1234</oc:size>
        <oc:permissions>RGDNVCK</oc:permissions>
      </d:prop>
      <d:status>HTTP/1.1 200 OK</d:status>
    </d:propstat>
  </d:response>
  <d:response>
    <d:href>/remote.php/dav/files/maria/Documents/Projects/</d:href>
    <d:propstat>
      <d:prop>
        <d:displayname>Projects</d:displayname>
        <d:resourcetype><d:collection /></d:resourcetype>
        <oc:size>600</oc:size>
        <oc:fileid>42</oc:fileid>
        <oc:permissions>RGDNVCK</oc:permissions>
        <d:getetag>"dir-etag"</d:getetag>
        <d:getlastmodified>Wed, 20 Jul 2022 05:12:23 GMT</d:getlastmodified>
      </d:prop>
      <d:status>HTTP/1.1 200 OK</d:status>
    </d:propstat>
  </d:response>
  <d:response>
    <d:href>/remote.php/dav/files/maria/Documents/Quarterly%20Report.pdf</d:href>
    <d:propstat>
      <d:prop>
        <d:displayname>Quarterly Report.pdf</d:displayname>
        <d:getcontentlength>512</d:getcontentlength>
        <d:getcontenttype>application/pdf</d:getcontenttype>
        <d:getetag>"file-etag"</d:getetag>
        <d:getlastmodified>Thu, 21 Jul 2022 05:12:23 GMT</d:getlastmodified>
        <d:resourcetype />
        <oc:fileid>84</oc:fileid>
        <oc:permissions>RGDNVW</oc:permissions>
      </d:prop>
      <d:status>HTTP/1.1 200 OK</d:status>
    </d:propstat>
  </d:response>
</d:multistatus>
"""

_PROPFIND_XML_WITH_BASE_PATH = _PROPFIND_XML.replace(
    "/remote.php/dav/files/",
    "/nextcloud/remote.php/dav/files/",
)

_UNSAFE_PROPFIND_XML = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE multistatus [
  <!ELEMENT multistatus ANY>
]>
<d:multistatus xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns">
  <d:response>
    <d:href>/remote.php/dav/files/maria/Documents/</d:href>
    <d:propstat>
      <d:prop>
        <d:displayname>Documents</d:displayname>
        <d:resourcetype><d:collection /></d:resourcetype>
      </d:prop>
      <d:status>HTTP/1.1 200 OK</d:status>
    </d:propstat>
  </d:response>
</d:multistatus>
"""


class TestNextcloudClient:
    def test_get_tool_definitions(self):
        client = NextcloudClient("https://cloud.example.com", "maria:app-password")
        defs = client.get_tool_definitions()
        assert len(defs) == 5
        assert all(d.service_type == ServiceType.NEXTCLOUD for d in defs)
        assert defs[0].http_method == "PROPFIND"
        assert defs[-1].path_template == "/ocs/v1.php/cloud/user"

    async def test_health_check_uses_documented_ocs_capabilities(self):
        client = NextcloudClient("https://cloud.example.com", "maria:app-password")
        mock = _patch_client_transport(client)
        mock.request.return_value = _mock_json_response(
            _ocs_response({"capabilities": {"core": {"webdav-root": "remote.php/dav"}}})
        )

        result = await client.health_check()

        assert result is True
        mock.request.assert_awaited_once_with(
            "GET", "/ocs/v1.php/cloud/capabilities", params={"format": "json"}
        )

    async def test_health_check_returns_false_when_ocs_meta_is_not_ok(self):
        client = NextcloudClient("https://cloud.example.com", "maria:app-password")
        mock = _patch_client_transport(client)
        mock.request.return_value = _mock_json_response(
            _ocs_response({}, status="failure", statuscode=996, message="Auth failed")
        )

        result = await client.health_check()

        assert result is False

    async def test_user_status_uses_documented_ocs_user_endpoint(self):
        client = NextcloudClient("https://cloud.example.com", "maria:app-password")
        mock = _patch_client_transport(client)
        mock.request.return_value = _mock_json_response(
            _ocs_response({"id": "maria", "display-name": "Maria Example"})
        )

        result = await client.execute_tool("nextcloud_user_status", {})

        assert result == {"id": "maria", "display-name": "Maria Example"}
        mock.request.assert_awaited_once_with(
            "GET", "/ocs/v1.php/cloud/user", params={"format": "json"}
        )

    async def test_list_notes_checks_capabilities_before_calling_notes_api(self):
        client = NextcloudClient("https://cloud.example.com", "maria:app-password")
        mock = _patch_client_transport(client)
        mock.request.side_effect = [
            _mock_json_response(
                _ocs_response(
                    {"capabilities": {"notes": {"api_version": ["1.4"], "version": "4.9.0"}}}
                )
            ),
            _mock_json_response([{"id": 7, "title": "Grocery list"}]),
        ]

        result = await client.execute_tool("nextcloud_list_notes", {})

        assert result == [{"id": 7, "title": "Grocery list"}]
        assert mock.request.await_args_list[0].args == ("GET", "/ocs/v2.php/cloud/capabilities")
        assert mock.request.await_args_list[0].kwargs == {"params": {"format": "json"}}
        assert mock.request.await_args_list[1].args == ("GET", "/index.php/apps/notes/api/v1/notes")

    async def test_notes_tools_fail_fast_when_notes_api_v1_is_not_advertised(self):
        client = NextcloudClient("https://cloud.example.com", "maria:app-password")
        mock = _patch_client_transport(client)
        mock.request.return_value = _mock_json_response(
            _ocs_response({"capabilities": {"files": {"version": "1.0"}}})
        )

        with pytest.raises(ToolExecutionError, match="Notes API v1 is unavailable"):
            await client.execute_tool("nextcloud_list_notes", {})

        mock.request.assert_awaited_once_with(
            "GET", "/ocs/v2.php/cloud/capabilities", params={"format": "json"}
        )

    async def test_notes_capabilities_check_is_cached_across_notes_tools(self):
        client = NextcloudClient("https://cloud.example.com", "maria:app-password")
        mock = _patch_client_transport(client)
        mock.request.side_effect = [
            _mock_json_response(
                _ocs_response(
                    {"capabilities": {"notes": {"api_version": ["1.2"], "version": "4.1.0"}}}
                )
            ),
            _mock_json_response([{"id": 7, "title": "Grocery list"}]),
            _mock_json_response({"id": 7, "title": "Grocery list", "content": "- milk"}),
        ]

        await client.execute_tool("nextcloud_list_notes", {})
        result = await client.execute_tool("nextcloud_get_note", {"note_id": 7})

        assert result == {"id": 7, "title": "Grocery list", "content": "- milk"}
        assert [call.args for call in mock.request.await_args_list] == [
            ("GET", "/ocs/v2.php/cloud/capabilities"),
            ("GET", "/index.php/apps/notes/api/v1/notes"),
            ("GET", "/index.php/apps/notes/api/v1/notes/7"),
        ]

    async def test_list_files_uses_webdav_propfind_and_normalizes_entries(self):
        client = NextcloudClient("https://cloud.example.com", "maria:app-password")
        mock = _patch_client_transport(client)
        mock.request.side_effect = [
            _mock_json_response(_ocs_response({"id": "maria"})),
            _mock_xml_response(_PROPFIND_XML),
        ]

        result = await client.execute_tool("nextcloud_list_files", {"path": "Documents"})

        assert result == {
            "path": "/Documents",
            "directory": {
                "name": "Documents",
                "path": "/Documents",
                "type": "directory",
                "size": 1234,
                "content_type": None,
                "etag": None,
                "last_modified": None,
                "permissions": "RGDNVCK",
                "file_id": None,
            },
            "entries": [
                {
                    "name": "Projects",
                    "path": "/Documents/Projects",
                    "type": "directory",
                    "size": 600,
                    "content_type": None,
                    "etag": "dir-etag",
                    "last_modified": "Wed, 20 Jul 2022 05:12:23 GMT",
                    "permissions": "RGDNVCK",
                    "file_id": "42",
                },
                {
                    "name": "Quarterly Report.pdf",
                    "path": "/Documents/Quarterly Report.pdf",
                    "type": "file",
                    "size": 512,
                    "content_type": "application/pdf",
                    "etag": "file-etag",
                    "last_modified": "Thu, 21 Jul 2022 05:12:23 GMT",
                    "permissions": "RGDNVW",
                    "file_id": "84",
                },
            ],
            "total": 2,
        }

        assert mock.request.await_count == 2
        first_call = mock.request.await_args_list[0]
        assert first_call.args == ("GET", "/ocs/v1.php/cloud/user")
        assert first_call.kwargs == {"params": {"format": "json"}}

        second_call = mock.request.await_args_list[1]
        assert second_call.args == ("PROPFIND", "/remote.php/dav/files/maria/Documents")
        assert second_call.kwargs["headers"]["Depth"] == "1"
        assert second_call.kwargs["content"].startswith('<?xml version="1.0" encoding="UTF-8"?>')

    async def test_list_files_rejects_parent_traversal(self):
        client = NextcloudClient("https://cloud.example.com", "maria:app-password")

        with pytest.raises(ToolExecutionError, match="Parent directory traversal"):
            await client.execute_tool("nextcloud_list_files", {"path": "/../Secrets"})

    async def test_list_files_accepts_webdav_hrefs_when_nextcloud_is_under_subpath(self):
        client = NextcloudClient("https://cloud.example.com/nextcloud", "maria:app-password")
        mock = _patch_client_transport(client)
        mock.request.side_effect = [
            _mock_json_response(_ocs_response({"id": "maria"})),
            _mock_xml_response(_PROPFIND_XML_WITH_BASE_PATH),
        ]

        result = await client.execute_tool("nextcloud_list_files", {"path": "Documents"})

        assert result["directory"]["path"] == "/Documents"
        assert [entry["path"] for entry in result["entries"]] == [
            "/Documents/Projects",
            "/Documents/Quarterly Report.pdf",
        ]

    async def test_list_files_rejects_unsafe_xml_constructs(self):
        client = NextcloudClient("https://cloud.example.com", "maria:app-password")
        mock = _patch_client_transport(client)
        mock.request.side_effect = [
            _mock_json_response(_ocs_response({"id": "maria"})),
            _mock_xml_response(_UNSAFE_PROPFIND_XML),
        ]

        with pytest.raises(ToolExecutionError, match="Invalid or unsafe XML"):
            await client.execute_tool("nextcloud_list_files", {"path": "/Documents"})
