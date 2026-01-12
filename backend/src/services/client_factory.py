from collections.abc import Callable
from typing import Any

from domain.entities.service_connection import ServiceType
from domain.exceptions import UnsupportedServiceError
from domain.ports.service_client import IServiceClient
from infrastructure.clients.adguard_client import AdGuardClient
from infrastructure.clients.calibreweb_client import CalibreWebClient
from infrastructure.clients.cloudflare_client import CloudflareClient
from infrastructure.clients.forgejo_client import ForgejoClient
from infrastructure.clients.freshrss_client import FreshRSSClient
from infrastructure.clients.generic_rest_client import GenericRestClient, GenericToolSpec
from infrastructure.clients.homeassistant_client import HomeAssistantClient
from infrastructure.clients.immich_client import ImmichClient
from infrastructure.clients.nextcloud_client import NextcloudClient
from infrastructure.clients.npm_client import NginxProxyManagerClient
from infrastructure.clients.paperless_client import PaperlessClient
from infrastructure.clients.portainer_client import PortainerClient
from infrastructure.clients.stirlingpdf_client import StirlingPdfClient
from infrastructure.clients.tailscale_client import TailscaleClient
from infrastructure.clients.uptimekuma_client import UptimeKumaClient
from infrastructure.clients.wallabag_client import WallabagClient
from infrastructure.clients.wikijs_client import WikiJsClient


class ServiceClientFactory:
    """Creates the correct IServiceClient for a given ServiceType."""

    _ClientCtor = Callable[[str, str], IServiceClient]

    _builtin_registry: dict[str, _ClientCtor] = {
        ServiceType.FORGEJO: ForgejoClient,
        ServiceType.HOME_ASSISTANT: HomeAssistantClient,
        ServiceType.PAPERLESS: PaperlessClient,
        ServiceType.IMMICH: ImmichClient,
        ServiceType.NEXTCLOUD: NextcloudClient,
        ServiceType.UPTIME_KUMA: UptimeKumaClient,
        ServiceType.ADGUARD: AdGuardClient,
        ServiceType.NGINX_PROXY_MANAGER: NginxProxyManagerClient,
        ServiceType.PORTAINER: PortainerClient,
        ServiceType.FRESHRSS: FreshRSSClient,
        ServiceType.WALLABAG: WallabagClient,
        ServiceType.STIRLING_PDF: StirlingPdfClient,
        ServiceType.WIKIJS: WikiJsClient,
        ServiceType.CALIBRE_WEB: CalibreWebClient,
        ServiceType.TAILSCALE: TailscaleClient,
        ServiceType.CLOUDFLARE: CloudflareClient,
    }

    def __init__(self) -> None:
        self._registry: dict[str, ServiceClientFactory._ClientCtor] = dict(self._builtin_registry)

    def create(
        self,
        service_type: ServiceType,
        base_url: str,
        api_token: str,
        *,
        tool_definitions: list[GenericToolSpec] | None = None,
        config: dict[str, Any] | None = None,
    ) -> IServiceClient:
        if service_type == ServiceType.GENERIC_REST:
            return GenericRestClient(base_url, api_token, tool_definitions, config=config)
        client_cls = self._registry.get(str(service_type))
        if client_cls is None:
            raise UnsupportedServiceError(service_type)
        return client_cls(base_url, api_token)
