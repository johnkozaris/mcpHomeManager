from abc import ABC, abstractmethod
from typing import Any

from domain.entities.tool_definition import ToolDefinition


class IServiceClient(ABC):
    @abstractmethod
    async def health_check(self) -> bool:
        """Test connectivity to the backing service. Returns True if reachable."""
        ...

    @abstractmethod
    async def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Execute a named tool with the given arguments against the backing service."""
        ...

    @abstractmethod
    def get_tool_definitions(self) -> list[ToolDefinition]:
        """Return all tool definitions this client can serve."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Release underlying HTTP resources."""
        ...

