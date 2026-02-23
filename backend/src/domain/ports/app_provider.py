from typing import Any, Protocol, runtime_checkable

from domain.entities.app_definition import AppDefinition


@runtime_checkable
class IAppProvider(Protocol):
    """A service client that can also serve interactive HTML apps.

    Clients return data dicts — template rendering stays in the entrypoints layer.
    """

    def get_app_definitions(self) -> list[AppDefinition]: ...

    async def fetch_app_data(self, app_name: str, arguments: dict[str, Any]) -> dict[str, Any]: ...

    async def handle_app_action(
        self,
        app_name: str,
        action: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]: ...
