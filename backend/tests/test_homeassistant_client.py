"""Tests for the Home Assistant service client."""

from unittest.mock import AsyncMock

import httpx
import pytest

from domain.entities.service_connection import ServiceType
from domain.exceptions import ToolExecutionError
from infrastructure.clients.homeassistant_client import HomeAssistantClient


def _response(
    method: str,
    path: str,
    *,
    status_code: int = 200,
    json_data: object | None = None,
    text_data: str = "",
) -> httpx.Response:
    request = httpx.Request(method, f"http://ha.local{path}")
    if json_data is not None:
        return httpx.Response(status_code, request=request, json=json_data)
    return httpx.Response(status_code, request=request, text=text_data)


def _patch_client_transport(client: HomeAssistantClient) -> AsyncMock:
    mock = AsyncMock()
    mock.request = AsyncMock()
    mock.headers = {}
    client._client = mock
    return mock


class TestHomeAssistantClient:
    def test_get_tool_definitions(self) -> None:
        client = HomeAssistantClient("http://ha.local", "test-token")
        defs = client.get_tool_definitions()

        assert len(defs) == 4
        assert all(defn.service_type == ServiceType.HOME_ASSISTANT for defn in defs)
        call_service = next(defn for defn in defs if defn.name == "ha_call_service")
        get_services = next(defn for defn in defs if defn.name == "ha_get_services")
        assert call_service.parameters_schema["properties"]["return_response"]["type"] == "boolean"
        assert get_services.description == (
            "List Home Assistant service domains and the services they expose"
        )

    def test_build_headers_uses_bearer_auth(self) -> None:
        client = HomeAssistantClient("http://ha.local", "test-token")

        headers = client._build_headers("another-token")

        assert headers["Authorization"] == "Bearer another-token"
        assert headers["Content-Type"] == "application/json"

    async def test_health_check_uses_api_root(self) -> None:
        client = HomeAssistantClient("http://ha.local", "test-token")
        mock = _patch_client_transport(client)
        mock.request.return_value = _response("GET", "/api/", json_data={"message": "API running."})

        result = await client.health_check()

        assert result is True
        mock.request.assert_called_once_with("GET", "/api/")

    async def test_call_service_default_mode_returns_changed_states(self) -> None:
        client = HomeAssistantClient("http://ha.local", "test-token")
        mock = _patch_client_transport(client)
        changed_states = [{"entity_id": "light.kitchen", "state": "on"}]
        mock.request.return_value = _response(
            "POST",
            "/api/services/light/turn_on",
            json_data=changed_states,
        )

        result = await client.execute_tool(
            "ha_call_service",
            {
                "domain": "light",
                "service": "turn_on",
                "entity_id": "light.kitchen",
                "data": {"brightness": 120},
            },
        )

        assert result == changed_states
        mock.request.assert_called_once_with(
            "POST",
            "/api/services/light/turn_on",
            json={"entity_id": "light.kitchen", "brightness": 120},
        )

    async def test_call_service_return_response_mode_returns_service_response(self) -> None:
        client = HomeAssistantClient("http://ha.local", "test-token")
        mock = _patch_client_transport(client)
        result_payload = {
            "changed_states": [{"entity_id": "weather.home", "state": "sunny"}],
            "service_response": {"weather.home": {"forecast": []}},
        }
        mock.request.return_value = _response(
            "POST",
            "/api/services/weather/get_forecasts?return_response",
            json_data=result_payload,
        )

        result = await client.execute_tool(
            "ha_call_service",
            {
                "domain": "weather",
                "service": "get_forecasts",
                "entity_id": "weather.home",
                "return_response": True,
                "data": {"type": "daily"},
            },
        )

        assert result == result_payload
        mock.request.assert_called_once_with(
            "POST",
            "/api/services/weather/get_forecasts?return_response",
            json={"entity_id": "weather.home", "type": "daily"},
        )

    async def test_call_service_surfaces_missing_return_response_error(self) -> None:
        client = HomeAssistantClient("http://ha.local", "test-token")
        mock = _patch_client_transport(client)
        mock.request.return_value = _response(
            "POST",
            "/api/services/weather/get_forecasts",
            status_code=400,
            json_data={"message": "Service call requires responses"},
        )

        with pytest.raises(ToolExecutionError, match="HTTP 400"):
            await client.execute_tool(
                "ha_call_service",
                {"domain": "weather", "service": "get_forecasts"},
            )

    async def test_call_service_surfaces_unsupported_return_response_error(self) -> None:
        client = HomeAssistantClient("http://ha.local", "test-token")
        mock = _patch_client_transport(client)
        mock.request.return_value = _response(
            "POST",
            "/api/services/light/turn_on?return_response",
            status_code=400,
            json_data={"message": "Service does not support responses"},
        )

        with pytest.raises(ToolExecutionError, match="HTTP 400"):
            await client.execute_tool(
                "ha_call_service",
                {"domain": "light", "service": "turn_on", "return_response": True},
            )

    @pytest.mark.parametrize(
        ("return_response", "expected_path"),
        [
            (False, "/api/services/light/turn_on"),
            (True, "/api/services/light/turn_on?return_response"),
        ],
    )
    async def test_handle_app_action_uses_same_service_call_path(
        self,
        return_response: bool,
        expected_path: str,
    ) -> None:
        client = HomeAssistantClient("http://ha.local", "test-token")
        mock = _patch_client_transport(client)
        mock.request.side_effect = [
            _response(
                "POST", expected_path, json_data=[{"entity_id": "light.kitchen", "state": "on"}]
            ),
            _response(
                "GET",
                "/api/states",
                json_data=[
                    {
                        "entity_id": "light.kitchen",
                        "state": "on",
                        "attributes": {"friendly_name": "Kitchen"},
                    }
                ],
            ),
        ]

        result = await client.handle_app_action(
            "ha_entity_dashboard",
            "call_service",
            {
                "domain": "light",
                "service": "turn_on",
                "entity_id": "light.kitchen",
                "data": {"brightness": 120},
                "return_response": return_response,
                "refresh_args": {"domain": "light"},
            },
        )

        assert result["entity_count"] == 1
        assert result["domain_filter"] == "light"
        assert mock.request.await_args_list[0].args == ("POST", expected_path)
        assert mock.request.await_args_list[0].kwargs == {
            "json": {"entity_id": "light.kitchen", "brightness": 120}
        }
        assert mock.request.await_args_list[1].args == ("GET", "/api/states")
