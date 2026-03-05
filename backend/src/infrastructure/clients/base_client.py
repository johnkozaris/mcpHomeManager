import re
from abc import ABC, abstractmethod
from typing import Any

import httpx
import structlog

from domain.entities.tool_definition import ToolDefinition
from domain.exceptions import ServiceConnectionError, ToolExecutionError
from domain.ports.service_client import IServiceClient

logger = structlog.get_logger()

_SAFE_PATH_SEGMENT = re.compile(r"^[\w\-.@]+$")


class BaseServiceClient(IServiceClient, ABC):
    """Base HTTP client with shared timeout, error handling, and resource cleanup."""

    service_name: str = "unknown"

    def __init__(
        self,
        base_url: str,
        api_token: str,
        *,
        timeout: float | None = None,
        connect_timeout: float | None = None,
    ) -> None:
        from config import settings

        self._base_url = base_url.rstrip("/")
        self._api_token = api_token
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(
                timeout or settings.http_timeout_seconds,
                connect=connect_timeout or settings.http_connect_timeout_seconds,
            ),
            headers=self._build_headers(api_token),
        )

    @abstractmethod
    def _build_headers(self, token: str) -> dict[str, str]: ...

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            response = await self._client.request(method, path, **kwargs)
            response.raise_for_status()
            if response.headers.get("content-type", "").startswith("application/json"):
                try:
                    return response.json()
                except Exception:
                    return response.text
            return response.text
        except httpx.ConnectError as e:
            raise ServiceConnectionError(self.service_name, f"Cannot connect: {e}") from e
        except httpx.TimeoutException as e:
            raise ServiceConnectionError(self.service_name, f"Timeout: {e}") from e
        except httpx.HTTPStatusError as e:
            raise ToolExecutionError(
                self.service_name,
                f"HTTP {e.response.status_code}: {e.response.text[:200]}",
            ) from e
        except ServiceConnectionError, ToolExecutionError:
            raise
        except Exception as e:
            raise ServiceConnectionError(
                self.service_name, f"Unexpected error: {type(e).__name__}: {e}"
            ) from e

    @staticmethod
    def _validate_path_segment(value: str, name: str) -> str:
        """Validate a user-supplied value is safe for URL path interpolation."""
        if not _SAFE_PATH_SEGMENT.match(value):
            raise ToolExecutionError(name, f"Invalid characters in '{name}': {value!r}")
        return value

    async def close(self) -> None:
        await self._client.aclose()

    @abstractmethod
    def get_tool_definitions(self) -> list[ToolDefinition]: ...

    @abstractmethod
    async def health_check(self) -> bool: ...

    @abstractmethod
    async def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any: ...
