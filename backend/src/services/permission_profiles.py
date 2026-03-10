"""Permission profiles — data-driven presets for tool access per service type."""

from dataclasses import dataclass, field

from domain.entities.service_connection import ServiceType


@dataclass(frozen=True)
class PermissionProfile:
    """A named set of tool enable/disable states."""

    name: str
    label: str
    description: str
    tool_states: dict[str, bool] = field(default_factory=dict)


def _all_enabled(tools: list[str]) -> dict[str, bool]:
    return dict.fromkeys(tools, True)


def _read_only(read_tools: list[str], all_tools: list[str]) -> dict[str, bool]:
    return {t: (t in read_tools) for t in all_tools}


def _all_except(excluded_tools: list[str], all_tools: list[str]) -> dict[str, bool]:
    return {t: (t not in excluded_tools) for t in all_tools}


# ── Forgejo ──────────────────────────────────────────────────────────────

_FORGEJO_TOOLS = [
    "forgejo_list_repos",
    "forgejo_get_repo",
    "forgejo_list_issues",
    "forgejo_create_issue",
    "forgejo_list_pull_requests",
    "forgejo_create_pull_request",
    "forgejo_search_repos",
]
_FORGEJO_READ = [
    "forgejo_list_repos",
    "forgejo_get_repo",
    "forgejo_list_issues",
    "forgejo_list_pull_requests",
    "forgejo_search_repos",
]

# ── Home Assistant ───────────────────────────────────────────────────────

_HA_TOOLS = ["ha_get_entity_state", "ha_list_entities", "ha_call_service", "ha_get_services"]
_HA_READ = ["ha_get_entity_state", "ha_list_entities", "ha_get_services"]

# ── Paperless ────────────────────────────────────────────────────────────

_PAPERLESS_TOOLS = [
    "paperless_search_documents",
    "paperless_get_document",
    "paperless_list_tags",
    "paperless_list_correspondents",
    "paperless_list_document_types",
]
_PAPERLESS_READ = list(_PAPERLESS_TOOLS)  # all are read-only

# ── Immich ───────────────────────────────────────────────────────────────

_IMMICH_TOOLS = [
    "immich_search_photos",
    "immich_get_asset",
    "immich_list_albums",
    "immich_get_album",
    "immich_server_stats",
]
_IMMICH_STANDARD_READ = [
    "immich_search_photos",
    "immich_get_asset",
    "immich_list_albums",
    "immich_get_album",
]
_IMMICH_ADMIN_ONLY = ["immich_server_stats"]


def _make_immich_profiles() -> list[PermissionProfile]:
    return [
        PermissionProfile(
            name="read_only",
            label="Read Only",
            description=(
                "Enable standard Immich read/query tools. "
                "Admin-only server statistics stay disabled."
            ),
            tool_states=_read_only(_IMMICH_STANDARD_READ, _IMMICH_TOOLS),
        ),
        PermissionProfile(
            name="contributor",
            label="Contributor",
            description=(
                "Enable non-admin Immich tools. Server statistics still require an admin API key."
            ),
            tool_states=_all_except(_IMMICH_ADMIN_ONLY, _IMMICH_TOOLS),
        ),
        PermissionProfile(
            name="admin",
            label="Full Access",
            description="Enable all Immich tools, including admin-only server statistics.",
            tool_states=_all_enabled(_IMMICH_TOOLS),
        ),
    ]


# ── Nextcloud ────────────────────────────────────────────────────────────

_NEXTCLOUD_TOOLS = [
    "nextcloud_list_files",
    "nextcloud_search_files",
    "nextcloud_list_notes",
    "nextcloud_get_note",
    "nextcloud_user_status",
]
_NEXTCLOUD_READ = list(_NEXTCLOUD_TOOLS)

# ── Uptime Kuma ──────────────────────────────────────────────────────────

_UPTIMEKUMA_TOOLS = [
    "uptimekuma_list_monitors",
    "uptimekuma_get_monitor",
    "uptimekuma_pause_monitor",
    "uptimekuma_resume_monitor",
]
_UPTIMEKUMA_READ = ["uptimekuma_list_monitors", "uptimekuma_get_monitor"]

# ── AdGuard ──────────────────────────────────────────────────────────────

_ADGUARD_TOOLS = [
    "adguard_status",
    "adguard_query_log",
    "adguard_stats",
    "adguard_list_filters",
    "adguard_list_rewrites",
    "adguard_toggle_protection",
]
_ADGUARD_READ = [
    "adguard_status",
    "adguard_query_log",
    "adguard_stats",
    "adguard_list_filters",
    "adguard_list_rewrites",
]

# ── Nginx Proxy Manager ─────────────────────────────────────────────────

_NPM_TOOLS = [
    "npm_list_proxy_hosts",
    "npm_get_proxy_host",
    "npm_create_proxy_host",
    "npm_delete_proxy_host",
    "npm_list_redirection_hosts",
    "npm_list_streams",
    "npm_list_certificates",
]
_NPM_READ = [
    "npm_list_proxy_hosts",
    "npm_get_proxy_host",
    "npm_list_redirection_hosts",
    "npm_list_streams",
    "npm_list_certificates",
]


# ── Portainer ────────────────────────────────────────────────────────────

_PORTAINER_TOOLS = [
    "portainer_list_endpoints",
    "portainer_list_containers",
    "portainer_get_container",
    "portainer_start_container",
    "portainer_stop_container",
    "portainer_restart_container",
    "portainer_list_stacks",
    "portainer_get_container_logs",
]
_PORTAINER_READ = [
    "portainer_list_endpoints",
    "portainer_list_containers",
    "portainer_get_container",
    "portainer_list_stacks",
    "portainer_get_container_logs",
]


# ── FreshRSS ─────────────────────────────────────────────────────────────

_FRESHRSS_TOOLS = [
    "freshrss_list_feeds",
    "freshrss_get_unread_count",
    "freshrss_get_articles",
    "freshrss_get_unread",
    "freshrss_mark_read",
    "freshrss_star_article",
    "freshrss_add_feed",
]
_FRESHRSS_READ = [
    "freshrss_list_feeds",
    "freshrss_get_unread_count",
    "freshrss_get_articles",
    "freshrss_get_unread",
]


# ── Wallabag ──────────────────────────────────────────────────────────────

_WALLABAG_TOOLS = [
    "wallabag_list_entries",
    "wallabag_get_entry",
    "wallabag_save_url",
    "wallabag_delete_entry",
    "wallabag_list_tags",
    "wallabag_tag_entry",
    "wallabag_search",
]
_WALLABAG_READ = [
    "wallabag_list_entries",
    "wallabag_get_entry",
    "wallabag_list_tags",
    "wallabag_search",
]


# ── Stirling PDF ──────────────────────────────────────────────────────────

_STIRLINGPDF_TOOLS = [
    "stirling_health",
    "stirling_get_operations",
]
_STIRLINGPDF_READ = list(_STIRLINGPDF_TOOLS)  # all are read-only


# ── Wiki.js ──────────────────────────────────────────────────────────────

_WIKIJS_TOOLS = [
    "wikijs_list_pages",
    "wikijs_get_page",
    "wikijs_search",
    "wikijs_create_page",
    "wikijs_update_page",
    "wikijs_list_users",
]
_WIKIJS_READ = [
    "wikijs_list_pages",
    "wikijs_get_page",
    "wikijs_search",
]


# -- Tailscale ────────────────────────────────────────────────────────────

_TAILSCALE_TOOLS = [
    "tailscale_list_devices",
    "tailscale_get_device",
    "tailscale_authorize_device",
    "tailscale_get_device_routes",
    "tailscale_list_dns_nameservers",
]
_TAILSCALE_READ = [
    "tailscale_list_devices",
    "tailscale_get_device",
    "tailscale_get_device_routes",
    "tailscale_list_dns_nameservers",
]


# ── Cloudflare ───────────────────────────────────────────────────────────

_CLOUDFLARE_TOOLS = [
    "cloudflare_list_zones",
    "cloudflare_list_dns_records",
    "cloudflare_create_dns_record",
    "cloudflare_list_tunnels",
    "cloudflare_get_tunnel",
]
_CLOUDFLARE_READ = [
    "cloudflare_list_zones",
    "cloudflare_list_dns_records",
    "cloudflare_list_tunnels",
    "cloudflare_get_tunnel",
]


# ── Calibre-Web ──────────────────────────────────────────────────────────

_CALIBREWEB_TOOLS = [
    "calibreweb_search_books",
    "calibreweb_list_authors",
    "calibreweb_list_categories",
    "calibreweb_list_series",
    "calibreweb_toggle_read",
]
_CALIBREWEB_READ = [
    "calibreweb_search_books",
    "calibreweb_list_authors",
    "calibreweb_list_categories",
    "calibreweb_list_series",
]


def _make_profiles(
    all_tools: list[str],
    read_tools: list[str],
) -> list[PermissionProfile]:
    return [
        PermissionProfile(
            name="read_only",
            label="Read Only",
            description="Only enable read/query tools. No create, update, or control actions.",
            tool_states=_read_only(read_tools, all_tools),
        ),
        PermissionProfile(
            name="contributor",
            label="Contributor",
            description="Enable all tools. Identical to Full Access.",
            tool_states=_all_enabled(all_tools),
        ),
        PermissionProfile(
            name="admin",
            label="Full Access",
            description="Enable all tools with no restrictions.",
            tool_states=_all_enabled(all_tools),
        ),
    ]


PROFILES: dict[ServiceType, list[PermissionProfile]] = {
    ServiceType.FORGEJO: _make_profiles(_FORGEJO_TOOLS, _FORGEJO_READ),
    ServiceType.HOME_ASSISTANT: _make_profiles(_HA_TOOLS, _HA_READ),
    ServiceType.PAPERLESS: _make_profiles(_PAPERLESS_TOOLS, _PAPERLESS_READ),
    ServiceType.IMMICH: _make_immich_profiles(),
    ServiceType.NEXTCLOUD: _make_profiles(_NEXTCLOUD_TOOLS, _NEXTCLOUD_READ),
    ServiceType.UPTIME_KUMA: _make_profiles(_UPTIMEKUMA_TOOLS, _UPTIMEKUMA_READ),
    ServiceType.ADGUARD: _make_profiles(_ADGUARD_TOOLS, _ADGUARD_READ),
    ServiceType.NGINX_PROXY_MANAGER: _make_profiles(_NPM_TOOLS, _NPM_READ),
    ServiceType.PORTAINER: _make_profiles(_PORTAINER_TOOLS, _PORTAINER_READ),
    ServiceType.FRESHRSS: _make_profiles(_FRESHRSS_TOOLS, _FRESHRSS_READ),
    ServiceType.WALLABAG: _make_profiles(_WALLABAG_TOOLS, _WALLABAG_READ),
    ServiceType.STIRLING_PDF: _make_profiles(_STIRLINGPDF_TOOLS, _STIRLINGPDF_READ),
    ServiceType.WIKIJS: _make_profiles(_WIKIJS_TOOLS, _WIKIJS_READ),
    ServiceType.CALIBRE_WEB: _make_profiles(_CALIBREWEB_TOOLS, _CALIBREWEB_READ),
    ServiceType.TAILSCALE: _make_profiles(_TAILSCALE_TOOLS, _TAILSCALE_READ),
    ServiceType.CLOUDFLARE: _make_profiles(_CLOUDFLARE_TOOLS, _CLOUDFLARE_READ),
    ServiceType.GENERIC_REST: [],  # Generic REST tools are user-defined; no preset profiles
}
