import msgspec
from litestar import Controller, get

from infrastructure.discovery import discover_services


class DiscoveredServiceResponse(msgspec.Struct):
    service_type: str
    display_name: str
    container_name: str
    image: str
    suggested_url: str
    ports: list[str]


class DiscoveryController(Controller):
    path = "/api/discovery"

    @get("/")
    async def scan(self) -> list[DiscoveredServiceResponse]:
        """Scan Docker for known homelab services."""
        discovered = await discover_services()
        return [
            DiscoveredServiceResponse(
                service_type=d.service_type.value,
                display_name=d.display_name,
                container_name=d.container_name,
                image=d.image,
                suggested_url=d.suggested_url,
                ports=d.ports,
            )
            for d in discovered
        ]
