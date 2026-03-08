import asyncio
from collections.abc import Awaitable, Callable
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from domain.entities.service_connection import ServiceType
from domain.exceptions import ServiceConnectionError, ToolExecutionError
from infrastructure.clients.uptimekuma_client import UptimeKumaClient


def _mock_response(json_data: Any, status_code: int = 200) -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.headers = {"content-type": "application/json"}
    response.json.return_value = json_data
    response.text = ""
    response.raise_for_status = MagicMock()
    return response


class FakeSocketClient:
    def __init__(self) -> None:
        self.connected = False
        self.handlers: dict[str, Callable[..., Any]] = {}
        self.calls: list[tuple[str, Any, int | None]] = []
        self.call_responses: dict[str, Any] = {}
        self.connect_calls: list[tuple[str, str, int | None]] = []
        self.disconnect_error: Exception | None = None

    def on(self, event: str, handler: Callable[..., Any] | None = None) -> None:
        if handler is not None:
            self.handlers[event] = handler

    async def connect(
        self,
        url: str,
        *,
        socketio_path: str = "socket.io",
        wait_timeout: int | None = None,
    ) -> None:
        self.connected = True
        self.connect_calls.append((url, socketio_path, wait_timeout))

    async def call(self, event: str, data: Any = None, **kwargs: Any) -> Any:
        self.calls.append((event, data, kwargs.get("timeout")))
        response = self.call_responses[event]
        if callable(response):
            result = response(data, self)
            if isinstance(result, Awaitable):
                return await result
            return result
        return response

    async def emit_server_event(self, event: str, data: Any = None) -> None:
        handler = self.handlers.get(event)
        if handler is None:
            return
        result = handler(data)
        if isinstance(result, Awaitable):
            await result

    async def disconnect(self) -> None:
        self.connected = False
        if self.disconnect_error is not None:
            raise self.disconnect_error
        handler = self.handlers.get("disconnect")
        if handler is None:
            return
        result = handler()
        if isinstance(result, Awaitable):
            await result


class TestUptimeKumaClient:
    def _build_client(
        self,
        auth_value: str,
        *,
        socket_client: FakeSocketClient | None = None,
        timeout: float | None = None,
        connect_timeout: float | None = None,
    ) -> tuple[UptimeKumaClient, AsyncMock, FakeSocketClient]:
        fake_socket = socket_client or FakeSocketClient()
        http_client = AsyncMock()
        http_client.get = AsyncMock(return_value=_mock_response({"type": "entryPage"}))
        http_client.aclose = AsyncMock()
        client = UptimeKumaClient(
            "http://test:3001",
            auth_value,
            timeout=timeout,
            connect_timeout=connect_timeout,
            http_client=http_client,
            socket_factory=lambda: fake_socket,
        )
        return client, http_client, fake_socket

    def test_get_tool_definitions(self) -> None:
        client, _, _ = self._build_client("admin:password")
        defs = client.get_tool_definitions()
        assert len(defs) == 4
        assert all(defn.service_type == ServiceType.UPTIME_KUMA for defn in defs)
        assert {defn.name: defn.description for defn in defs} == {
            "uptimekuma_list_monitors": (
                "List all monitors and whether each one is active or paused"
            ),
            "uptimekuma_get_monitor": "Get the full configuration for a specific monitor",
            "uptimekuma_pause_monitor": "Pause a monitor (stop checking)",
            "uptimekuma_resume_monitor": "Resume a paused monitor",
        }

    async def test_health_check_authenticates_with_login_event(self) -> None:
        client, http_client, socket_client = self._build_client("admin:secret")
        socket_client.call_responses["login"] = {"ok": True, "token": "jwt-token"}

        result = await client.health_check()

        assert result is True
        http_client.get.assert_awaited_once_with("/api/entry-page")
        assert socket_client.connect_calls == [("http://test:3001", "socket.io", 10)]
        assert socket_client.calls[0] == (
            "login",
            {"username": "admin", "password": "secret"},
            30,
        )
        await client.close()

    async def test_health_check_authenticates_with_login_by_token(self) -> None:
        client, _, socket_client = self._build_client("jwt-token")
        socket_client.call_responses["loginByToken"] = {"ok": True}

        result = await client.health_check()

        assert result is True
        assert socket_client.calls[0] == ("loginByToken", "jwt-token", 30)
        await client.close()

    async def test_health_check_surfaces_2fa_requirement(self) -> None:
        client, _, socket_client = self._build_client("admin:secret")
        socket_client.call_responses["login"] = {"tokenRequired": True}

        with pytest.raises(ServiceConnectionError, match="requires a 2FA code"):
            await client.health_check()

        await client.close()

    async def test_health_check_authenticates_with_inline_2fa_token(self) -> None:
        client, _, socket_client = self._build_client("admin:secret:123456")

        async def login_response(data: Any, _: FakeSocketClient) -> dict[str, Any]:
            if data == {"username": "admin", "password": "secret:123456"}:
                return {"tokenRequired": True}
            if data == {"username": "admin", "password": "secret", "token": "123456"}:
                return {"ok": True, "token": "jwt-token"}
            raise AssertionError(f"unexpected login payload: {data!r}")

        socket_client.call_responses["login"] = login_response

        result = await client.health_check()

        assert result is True
        assert socket_client.calls == [
            ("login", {"username": "admin", "password": "secret:123456"}, 30),
            ("login", {"username": "admin", "password": "secret", "token": "123456"}, 30),
        ]
        await client.close()

    async def test_health_check_surfaces_invalid_inline_2fa_token(self) -> None:
        client, _, socket_client = self._build_client("admin:secret:123456")

        async def login_response(data: Any, _: FakeSocketClient) -> dict[str, Any]:
            if data == {"username": "admin", "password": "secret:123456"}:
                return {"tokenRequired": True}
            if data == {"username": "admin", "password": "secret", "token": "123456"}:
                return {"ok": False, "msg": "authInvalidToken"}
            raise AssertionError(f"unexpected login payload: {data!r}")

        socket_client.call_responses["login"] = login_response

        with pytest.raises(ServiceConnectionError, match="Invalid Uptime Kuma 2FA code"):
            await client.health_check()

        await client.close()

    async def test_list_monitors_uses_monitor_list_event_payload(self) -> None:
        client, _, socket_client = self._build_client("admin:secret")
        socket_client.call_responses["login"] = {"ok": True, "token": "jwt-token"}

        async def get_monitor_list_response(
            _: Any, fake_socket: FakeSocketClient
        ) -> dict[str, Any]:
            await fake_socket.emit_server_event(
                "monitorList",
                {
                    "2": {"id": 2, "name": "Database", "active": True},
                    "1": {"id": 1, "name": "Website", "active": False},
                },
            )
            return {"ok": True}

        socket_client.call_responses["getMonitorList"] = get_monitor_list_response

        result = await client.execute_tool("uptimekuma_list_monitors", {})

        assert result == [
            {"id": 1, "name": "Website", "active": False},
            {"id": 2, "name": "Database", "active": True},
        ]
        assert [call[0] for call in socket_client.calls] == ["login", "getMonitorList"]
        await client.close()

    async def test_disconnect_socket_clears_state_when_disconnect_raises(self) -> None:
        socket_client = FakeSocketClient()
        socket_client.connected = True
        socket_client.disconnect_error = RuntimeError("disconnect failed")
        client, _, _ = self._build_client("admin:secret", socket_client=socket_client)
        client._socket = socket_client
        client._socket_authenticated = True

        with pytest.raises(RuntimeError, match="disconnect failed"):
            await client._disconnect_socket()

        assert client._socket is None
        assert client._socket_authenticated is False
        await client.close()

    async def test_list_monitors_concurrent_calls_do_not_overwrite_waiter(self) -> None:
        client, _, socket_client = self._build_client(
            "admin:secret",
            timeout=0.2,
            connect_timeout=0.2,
        )
        socket_client.call_responses["login"] = {"ok": True, "token": "jwt-token"}
        first_request_started = asyncio.Event()
        second_request_started = asyncio.Event()
        get_monitor_list_calls = 0

        async def get_monitor_list_response(
            _: Any, fake_socket: FakeSocketClient
        ) -> dict[str, Any]:
            nonlocal get_monitor_list_calls
            get_monitor_list_calls += 1
            call_number = get_monitor_list_calls

            if call_number == 1:
                first_request_started.set()
                await second_request_started.wait()
                await asyncio.sleep(0)
                await asyncio.sleep(0)

            await fake_socket.emit_server_event(
                "monitorList",
                {
                    "1": {
                        "id": 1,
                        "name": f"Website {call_number}",
                        "active": True,
                    }
                },
            )
            return {"ok": True}

        socket_client.call_responses["getMonitorList"] = get_monitor_list_response

        try:
            first_task = asyncio.create_task(client.execute_tool("uptimekuma_list_monitors", {}))
            await asyncio.wait_for(first_request_started.wait(), timeout=1)

            async def run_second_refresh() -> Any:
                second_request_started.set()
                return await client.execute_tool("uptimekuma_list_monitors", {})

            second_task = asyncio.create_task(run_second_refresh())
            first_result, second_result = await asyncio.wait_for(
                asyncio.gather(first_task, second_task),
                timeout=1,
            )
        finally:
            await client.close()

        assert first_result == [{"id": 1, "name": "Website 1", "active": True}]
        assert second_result == [{"id": 1, "name": "Website 2", "active": True}]
        assert [call[0] for call in socket_client.calls] == [
            "login",
            "getMonitorList",
            "getMonitorList",
        ]

    async def test_get_monitor_uses_get_monitor_event(self) -> None:
        client, _, socket_client = self._build_client("admin:secret")
        socket_client.call_responses["login"] = {"ok": True, "token": "jwt-token"}
        socket_client.call_responses["getMonitor"] = {
            "ok": True,
            "monitor": {"id": 9, "name": "API", "active": True},
        }

        result = await client.execute_tool("uptimekuma_get_monitor", {"monitor_id": 9})

        assert result == {"id": 9, "name": "API", "active": True}
        assert socket_client.calls[-1] == ("getMonitor", 9, 30)
        await client.close()

    async def test_pause_monitor_returns_updated_monitor(self) -> None:
        client, _, socket_client = self._build_client("admin:secret")
        socket_client.call_responses["login"] = {"ok": True, "token": "jwt-token"}
        socket_client.call_responses["pauseMonitor"] = {"ok": True, "msg": "successPaused"}
        socket_client.call_responses["getMonitor"] = {
            "ok": True,
            "monitor": {"id": 3, "name": "Redis", "active": False},
        }

        result = await client.execute_tool("uptimekuma_pause_monitor", {"monitor_id": 3})

        assert result == {
            "ok": True,
            "msg": "successPaused",
            "monitor": {"id": 3, "name": "Redis", "active": False},
        }
        assert [call[0] for call in socket_client.calls] == ["login", "pauseMonitor", "getMonitor"]
        await client.close()

    async def test_resume_monitor_returns_updated_monitor(self) -> None:
        client, _, socket_client = self._build_client("admin:secret")
        socket_client.call_responses["login"] = {"ok": True, "token": "jwt-token"}
        socket_client.call_responses["resumeMonitor"] = {"ok": True, "msg": "successResumed"}
        socket_client.call_responses["getMonitor"] = {
            "ok": True,
            "monitor": {"id": 3, "name": "Redis", "active": True},
        }

        result = await client.execute_tool("uptimekuma_resume_monitor", {"monitor_id": 3})

        assert result == {
            "ok": True,
            "msg": "successResumed",
            "monitor": {"id": 3, "name": "Redis", "active": True},
        }
        assert [call[0] for call in socket_client.calls] == ["login", "resumeMonitor", "getMonitor"]
        await client.close()

    async def test_unknown_tool_raises(self) -> None:
        client, _, _ = self._build_client("admin:secret")

        with pytest.raises(ToolExecutionError, match="Unknown tool"):
            await client.execute_tool("uptimekuma_delete_monitor", {})

        await client.close()
