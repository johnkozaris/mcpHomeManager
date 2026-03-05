"""Docker-based service auto-discovery.

Scans running containers for known homelab service images and suggests
services to connect to MCP Home Manager.
"""

from dataclasses import dataclass

import structlog

from domain.entities.service_connection import ServiceType

logger = structlog.get_logger()

_KNOWN_IMAGES: dict[str, tuple[ServiceType, str, int]] = {
    "forgejo": (ServiceType.FORGEJO, "Forgejo", 3000),
    "gitea": (ServiceType.FORGEJO, "Gitea", 3000),
    "homeassistant": (ServiceType.HOME_ASSISTANT, "Home Assistant", 8123),
    "ghcr.io/home-assistant": (ServiceType.HOME_ASSISTANT, "Home Assistant", 8123),
    "paperless-ngx": (ServiceType.PAPERLESS, "Paperless-ngx", 8000),
    "immich-server": (ServiceType.IMMICH, "Immich", 2283),
    "ghcr.io/immich-app": (ServiceType.IMMICH, "Immich", 2283),
    "nextcloud": (ServiceType.NEXTCLOUD, "Nextcloud", 80),
    "uptime-kuma": (ServiceType.UPTIME_KUMA, "Uptime Kuma", 3001),
    "adguardhome": (ServiceType.ADGUARD, "AdGuard Home", 80),
    "adguard/adguardhome": (ServiceType.ADGUARD, "AdGuard Home", 80),
}


@dataclass
class DiscoveredService:
    service_type: ServiceType
    display_name: str
    container_name: str
    image: str
    suggested_url: str
    ports: list[str]


async def discover_services() -> list[DiscoveredService]:
    """Scan Docker containers for known homelab services."""
    try:
        import aiodocker
    except ImportError:
        logger.warning("aiodocker not installed — discovery unavailable")
        return []

    discovered: list[DiscoveredService] = []
    try:
        docker = aiodocker.Docker()
        try:
            containers = await docker.containers.list()
            for container in containers:
                try:
                    info = container._container
                    image = info.get("Image", "")
                    names = info.get("Names", [])
                    container_name = names[0].lstrip("/") if names else "unknown"
                except AttributeError, IndexError, TypeError:
                    continue

                for pattern, (svc_type, display_name, default_port) in _KNOWN_IMAGES.items():
                    if pattern in image.lower():
                        ports_info = info.get("Ports", [])
                        port_strs = []
                        for p in ports_info:
                            if isinstance(p, dict):
                                public = p.get("PublicPort", p.get("PrivatePort", "?"))
                                private = p.get("PrivatePort", "?")
                                port_strs.append(f"{public}:{private}")

                        suggested_url = f"http://{container_name}:{default_port}"

                        discovered.append(
                            DiscoveredService(
                                service_type=svc_type,
                                display_name=display_name,
                                container_name=container_name,
                                image=image,
                                suggested_url=suggested_url,
                                ports=port_strs,
                            )
                        )
                        break

        finally:
            await docker.close()

    except Exception as e:
        logger.warning("Docker discovery failed: %s", e)

    return discovered
