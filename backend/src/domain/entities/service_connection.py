from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID


class ServiceType(StrEnum):
    FORGEJO = "forgejo"
    HOME_ASSISTANT = "homeassistant"
    PAPERLESS = "paperless"
    IMMICH = "immich"
    NEXTCLOUD = "nextcloud"
    UPTIME_KUMA = "uptimekuma"
    ADGUARD = "adguard"
    NGINX_PROXY_MANAGER = "nginxproxymanager"
    PORTAINER = "portainer"
    FRESHRSS = "freshrss"
    WALLABAG = "wallabag"
    STIRLING_PDF = "stirlingpdf"
    WIKIJS = "wikijs"
    CALIBRE_WEB = "calibreweb"
    TAILSCALE = "tailscale"
    CLOUDFLARE = "cloudflare"
    GENERIC_REST = "generic_rest"


class HealthStatus(StrEnum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ServiceConnection:
    name: str
    display_name: str
    service_type: ServiceType
    base_url: str
    api_token_encrypted: str
    is_enabled: bool = True
    health_status: HealthStatus = HealthStatus.UNKNOWN
    last_health_check: datetime | None = None
    config: dict = field(default_factory=dict)
    id: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def mark_healthy(self) -> None:
        self.health_status = HealthStatus.HEALTHY
        self.last_health_check = datetime.now(UTC)

    def mark_unhealthy(self) -> None:
        self.health_status = HealthStatus.UNHEALTHY
        self.last_health_check = datetime.now(UTC)

    def update_connection(
        self,
        *,
        display_name: str | None = None,
        base_url: str | None = None,
        api_token_encrypted: str | None = None,
        is_enabled: bool | None = None,
        config: dict | None = None,
    ) -> None:
        if display_name is not None:
            self.display_name = display_name
        if base_url is not None:
            self.base_url = base_url
        if api_token_encrypted is not None:
            self.api_token_encrypted = api_token_encrypted
        if is_enabled is not None:
            self.is_enabled = is_enabled
        if config is not None:
            self.config = config
