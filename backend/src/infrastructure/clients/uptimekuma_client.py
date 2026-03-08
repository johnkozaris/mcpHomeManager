import asyncio
import math
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Protocol

import httpx
import socketio  # type: ignore[import-untyped]
from socketio.exceptions import (  # type: ignore[import-untyped]
    BadNamespaceError,
)
from socketio.exceptions import (
    ConnectionError as SocketConnectionError,
)
from socketio.exceptions import (
    TimeoutError as SocketTimeoutError,
)

from domain.entities.service_connection import ServiceType
from domain.entities.tool_definition import ToolDefinition
from domain.exceptions import ServiceConnectionError, ToolExecutionError
from domain.ports.service_client import IServiceClient

_TOOLS = [
    ToolDefinition(
        name="uptimekuma_list_monitors",
        service_type=ServiceType.UPTIME_KUMA,
        description="List all monitors and whether each one is active or paused",
        parameters_schema={"type": "object", "properties": {}},
    ),
    ToolDefinition(
        name="uptimekuma_get_monitor",
        service_type=ServiceType.UPTIME_KUMA,
        description="Get the full configuration for a specific monitor",
        parameters_schema={
            "type": "object",
            "properties": {
                "monitor_id": {"type": "integer", "description": "Monitor ID"},
            },
            "required": ["monitor_id"],
        },
    ),
    ToolDefinition(
        name="uptimekuma_pause_monitor",
        service_type=ServiceType.UPTIME_KUMA,
        description="Pause a monitor (stop checking)",
        parameters_schema={
            "type": "object",
            "properties": {
                "monitor_id": {"type": "integer", "description": "Monitor ID"},
            },
            "required": ["monitor_id"],
        },
    ),
    ToolDefinition(
        name="uptimekuma_resume_monitor",
        service_type=ServiceType.UPTIME_KUMA,
        description="Resume a paused monitor",
        parameters_schema={
            "type": "object",
            "properties": {
                "monitor_id": {"type": "integer", "description": "Monitor ID"},
            },
            "required": ["monitor_id"],
        },
    ),
]

_AUTH_INVALID_TOKEN = (
    "Uptime Kuma rejected the session token. Paste a valid remembered-session JWT "  # noqa: S105
    "or use username-based login credentials."
)
_AUTH_2FA_REQUIRED = (
    "This Uptime Kuma account requires a 2FA code. Append the current 6-digit TOTP "
    "as username:password:123456, or use a remembered-session JWT (optionally prefixed "
    "with jwt:)."
)


class _SocketClient(Protocol):
    connected: bool

    def on(self, *args: Any, **kwargs: Any) -> Any: ...

    def connect(self, *args: Any, **kwargs: Any) -> Awaitable[None]: ...

    def call(self, *args: Any, **kwargs: Any) -> Awaitable[Any]: ...

    def disconnect(self) -> Awaitable[None]: ...


@dataclass(frozen=True)
class _LoginCredentials:
    username: str
    password: str


class UptimeKumaClient(IServiceClient):
    """Official Uptime Kuma client using Socket.IO auth and monitor events."""

    service_name = "uptimekuma"

    def __init__(
        self,
        base_url: str,
        api_token: str,
        *,
        timeout: float | None = None,
        connect_timeout: float | None = None,
        socket_factory: Callable[[], _SocketClient] | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        from config import settings

        self._base_url = base_url.rstrip("/")
        self._api_token = api_token
        self._timeout = timeout or settings.http_timeout_seconds
        self._connect_timeout = connect_timeout or settings.http_connect_timeout_seconds
        self._socket_timeout = self._socketio_timeout(self._timeout)
        self._socket_connect_timeout = self._socketio_timeout(self._connect_timeout)
        self._http_client = http_client or httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(self._timeout, connect=self._connect_timeout),
            headers={"Accept": "application/json"},
        )
        self._socket_factory = socket_factory or self._default_socket_factory
        self._socket: _SocketClient | None = None
        self._socket_authenticated = False
        self._socket_lock = asyncio.Lock()
        self._monitor_list_snapshot: dict[str, dict[str, Any]] = {}
        self._monitor_list_refresh_lock = asyncio.Lock()
        self._monitor_list_waiter: asyncio.Event | None = None
        self._session_jwt: str | None = None

    @staticmethod
    def _socketio_timeout(value: float) -> int:
        return max(1, math.ceil(value))

    def _default_socket_factory(self) -> _SocketClient:
        return socketio.AsyncClient(reconnection=False, logger=False, engineio_logger=False)

    @staticmethod
    def _parse_auth_value(auth_value: str) -> _LoginCredentials | str:
        value = auth_value.strip()
        if not value:
            raise ServiceConnectionError(
                UptimeKumaClient.service_name,
                "Missing credentials. Use username:password, username:password:123456, "
                "or a remembered-session JWT.",
            )

        if value.startswith("jwt:"):
            token = value.removeprefix("jwt:").strip()
            if not token:
                raise ServiceConnectionError(
                    UptimeKumaClient.service_name,
                    "JWT credentials cannot be empty.",
                )
            return token

        if ":" not in value:
            return value

        username, password = value.split(":", 1)
        if not username or not password:
            raise ServiceConnectionError(
                UptimeKumaClient.service_name,
                "Use username:password, username:password:123456, or a remembered-session JWT.",
            )
        return _LoginCredentials(username=username, password=password)

    @staticmethod
    def _split_inline_totp(password: str) -> tuple[str, str] | None:
        raw_password, separator, token = password.rpartition(":")
        if not separator or not raw_password:
            return None
        if len(token) == 6 and token.isdigit():
            return raw_password, token
        return None

    @staticmethod
    def _normalize_monitor_list(payload: Any) -> dict[str, dict[str, Any]]:
        if not isinstance(payload, dict):
            return {}
        return {str(key): value for key, value in payload.items() if isinstance(value, dict)}

    @staticmethod
    def _auth_error_message(response: dict[str, Any]) -> str:
        if response.get("tokenRequired"):
            return _AUTH_2FA_REQUIRED

        msg = response.get("msg")
        if msg == "authInvalidToken":
            return _AUTH_INVALID_TOKEN
        if msg == "authIncorrectCreds":
            return "Invalid Uptime Kuma username or password."
        if msg == "authUserInactiveOrDeleted":
            return "The Uptime Kuma user is inactive or deleted."
        if isinstance(msg, str) and msg:
            return msg
        return "Uptime Kuma authentication failed."

    @staticmethod
    def _totp_error_message(response: dict[str, Any]) -> str:
        if response.get("msg") == "authInvalidToken":
            return "Invalid Uptime Kuma 2FA code."
        return UptimeKumaClient._auth_error_message(response)

    def _register_socket_handlers(self, socket: _SocketClient) -> None:
        async def _on_disconnect() -> None:
            self._socket_authenticated = False

        async def _on_monitor_list(data: Any) -> None:
            self._monitor_list_snapshot = self._normalize_monitor_list(data)
            waiter = self._monitor_list_waiter
            if waiter is not None:
                waiter.set()

        async def _on_update_monitor_into_list(data: Any) -> None:
            for key, value in self._normalize_monitor_list(data).items():
                self._monitor_list_snapshot[key] = value

        async def _on_delete_monitor_from_list(monitor_id: Any) -> None:
            self._monitor_list_snapshot.pop(str(monitor_id), None)

        socket.on("disconnect", handler=_on_disconnect)
        socket.on("monitorList", handler=_on_monitor_list)
        socket.on("updateMonitorIntoList", handler=_on_update_monitor_into_list)
        socket.on("deleteMonitorFromList", handler=_on_delete_monitor_from_list)

    async def _disconnect_socket(self) -> None:
        socket = self._socket
        self._socket = None
        self._socket_authenticated = False

        if socket is None or not socket.connected:
            return

        await socket.disconnect()

    async def _authenticate_socket(self, socket: _SocketClient) -> None:
        if self._session_jwt:
            response = await socket.call(
                "loginByToken", self._session_jwt, timeout=self._socket_timeout
            )
            if not isinstance(response, dict) or not response.get("ok"):
                raise ServiceConnectionError(
                    self.service_name, self._auth_error_message(response or {})
                )
            return

        auth_value = self._parse_auth_value(self._api_token)

        if isinstance(auth_value, str):
            response = await socket.call("loginByToken", auth_value, timeout=self._socket_timeout)
            if not isinstance(response, dict) or not response.get("ok"):
                raise ServiceConnectionError(
                    self.service_name, self._auth_error_message(response or {})
                )
            self._session_jwt = auth_value
            return

        response = await socket.call(
            "login",
            {"username": auth_value.username, "password": auth_value.password},
            timeout=self._socket_timeout,
        )
        if isinstance(response, dict) and response.get("tokenRequired"):
            inline_totp = self._split_inline_totp(auth_value.password)
            if inline_totp is None:
                raise ServiceConnectionError(self.service_name, _AUTH_2FA_REQUIRED)
            password, token = inline_totp
            response = await socket.call(
                "login",
                {
                    "username": auth_value.username,
                    "password": password,
                    "token": token,
                },
                timeout=self._socket_timeout,
            )
        if not isinstance(response, dict) or not response.get("ok"):
            raise ServiceConnectionError(
                self.service_name, self._totp_error_message(response or {})
            )

        session_token = response.get("token")
        if isinstance(session_token, str) and session_token:
            self._session_jwt = session_token

    async def _ensure_socket_authenticated(self) -> _SocketClient:
        async with self._socket_lock:
            if self._socket is not None and self._socket.connected and self._socket_authenticated:
                return self._socket

            await self._disconnect_socket()

            socket = self._socket_factory()
            self._register_socket_handlers(socket)

            try:
                await socket.connect(
                    self._base_url,
                    socketio_path="socket.io",
                    wait_timeout=self._socket_connect_timeout,
                )
                self._socket = socket
                await self._authenticate_socket(socket)
            except ServiceConnectionError:
                await self._disconnect_socket()
                raise
            except (SocketConnectionError, SocketTimeoutError, TimeoutError) as exc:
                await self._disconnect_socket()
                raise ServiceConnectionError(
                    self.service_name,
                    f"Socket.IO connection failed: {exc}",
                ) from exc
            except Exception as exc:
                await self._disconnect_socket()
                raise ServiceConnectionError(
                    self.service_name,
                    f"Unexpected Socket.IO error: {type(exc).__name__}: {exc}",
                ) from exc

            self._socket_authenticated = True
            return socket

    async def _call_event(self, event: str, data: Any = None) -> dict[str, Any]:
        socket = await self._ensure_socket_authenticated()
        try:
            response = await socket.call(event, data, timeout=self._socket_timeout)
        except (BadNamespaceError, SocketConnectionError, SocketTimeoutError, TimeoutError) as exc:
            await self._disconnect_socket()
            raise ServiceConnectionError(
                self.service_name,
                f"Socket.IO event '{event}' failed: {exc}",
            ) from exc
        if not isinstance(response, dict):
            raise ServiceConnectionError(
                self.service_name,
                f"Socket.IO event '{event}' returned an unexpected response shape.",
            )
        return response

    async def _refresh_monitor_list(self) -> dict[str, dict[str, Any]]:
        async with self._monitor_list_refresh_lock:
            waiter = asyncio.Event()
            self._monitor_list_waiter = waiter
            try:
                response = await self._call_event("getMonitorList")
                if not isinstance(response, dict) or not response.get("ok"):
                    raise ToolExecutionError(
                        "uptimekuma_list_monitors",
                        response.get("msg", "Failed to load monitor list"),
                    )
                await asyncio.wait_for(waiter.wait(), timeout=self._timeout)
            except TimeoutError as exc:
                raise ServiceConnectionError(
                    self.service_name,
                    "Timed out waiting for Uptime Kuma monitorList event.",
                ) from exc
            finally:
                if self._monitor_list_waiter is waiter:
                    self._monitor_list_waiter = None

            return dict(self._monitor_list_snapshot)

    async def _get_monitor(self, monitor_id: int) -> dict[str, Any]:
        response = await self._call_event("getMonitor", monitor_id)
        if not isinstance(response, dict) or not response.get("ok"):
            raise ToolExecutionError(
                "uptimekuma_get_monitor",
                response.get("msg", f"Failed to load monitor {monitor_id}"),
            )

        monitor = response.get("monitor")
        if not isinstance(monitor, dict):
            raise ToolExecutionError(
                "uptimekuma_get_monitor",
                f"Uptime Kuma did not return monitor data for {monitor_id}.",
            )
        return monitor

    def get_tool_definitions(self) -> list[ToolDefinition]:
        return list(_TOOLS)

    async def health_check(self) -> bool:
        try:
            response = await self._http_client.get("/api/entry-page")
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict) or "type" not in payload:
                return False
            await self._ensure_socket_authenticated()
            return True
        except httpx.ConnectError as exc:
            raise ServiceConnectionError(self.service_name, f"Cannot connect: {exc}") from exc
        except httpx.TimeoutException as exc:
            raise ServiceConnectionError(self.service_name, f"Timeout: {exc}") from exc
        except httpx.HTTPStatusError as exc:
            raise ServiceConnectionError(
                self.service_name,
                f"HTTP {exc.response.status_code}: {exc.response.text[:200]}",
            ) from exc
        except ValueError as exc:
            raise ServiceConnectionError(
                self.service_name,
                f"Unexpected /api/entry-page response: {exc}",
            ) from exc

    async def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        match tool_name:
            case "uptimekuma_list_monitors":
                monitor_map = await self._refresh_monitor_list()
                return sorted(
                    monitor_map.values(),
                    key=lambda monitor: int(monitor.get("id", 0)),
                )
            case "uptimekuma_get_monitor":
                return await self._get_monitor(int(arguments["monitor_id"]))
            case "uptimekuma_pause_monitor":
                monitor_id = int(arguments["monitor_id"])
                response = await self._call_event("pauseMonitor", monitor_id)
                if not isinstance(response, dict) or not response.get("ok"):
                    raise ToolExecutionError(
                        tool_name,
                        response.get("msg", f"Failed to pause monitor {monitor_id}"),
                    )
                return {
                    "ok": True,
                    "msg": response.get("msg"),
                    "monitor": await self._get_monitor(monitor_id),
                }
            case "uptimekuma_resume_monitor":
                monitor_id = int(arguments["monitor_id"])
                response = await self._call_event("resumeMonitor", monitor_id)
                if not isinstance(response, dict) or not response.get("ok"):
                    raise ToolExecutionError(
                        tool_name,
                        response.get("msg", f"Failed to resume monitor {monitor_id}"),
                    )
                return {
                    "ok": True,
                    "msg": response.get("msg"),
                    "monitor": await self._get_monitor(monitor_id),
                }
            case _:
                raise ToolExecutionError(tool_name, f"Unknown tool: {tool_name}")

    async def close(self) -> None:
        await self._disconnect_socket()
        await self._http_client.aclose()
