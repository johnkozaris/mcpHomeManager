"""Jinja2 template engine for MCP Apps — renders self-contained HTML UIs."""

from datetime import UTC, datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from config import settings


def _status_color(status: str) -> str:
    """Map a health status string to a CSS class name."""
    return {
        "healthy": "status-healthy",
        "unhealthy": "status-unhealthy",
    }.get(status, "status-unknown")


def _status_label(status: str) -> str:
    """Human-readable label for health status."""
    return {
        "healthy": "Healthy",
        "unhealthy": "Unhealthy",
    }.get(status, "Unknown")


def _time_ago(dt: datetime | str | None) -> str:
    """Format a datetime as a human-readable relative time string."""
    if dt is None:
        return "never"
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except ValueError:
            return str(dt)  # Return the raw string if unparseable
    now = datetime.now(UTC)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    delta = now - dt
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return "just now"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    days = hours // 24
    return f"{days}d ago"


_ICON_MAP: dict[str, str] = {
    "forgejo": "\U0001f5a5",  # desktop computer
    "homeassistant": "\U0001f3e0",  # house
    "paperless": "\U0001f4c4",  # document
    "immich": "\U0001f4f7",  # camera
    "nextcloud": "\u2601",  # cloud
    "uptimekuma": "\U0001f7e2",  # green circle
    "adguard": "\U0001f6e1",  # shield
    "generic_rest": "\U0001f517",  # link
}
_DEFAULT_ICON = "\U0001f52c"


def _service_icon(service_type: str) -> str:
    """Return a Unicode icon for a service type.

    Uses plain Unicode characters (not HTML entities) so Jinja2's
    autoescape can handle them safely without Markup().
    """
    return _ICON_MAP.get(service_type, _DEFAULT_ICON)


class TemplateEngine:
    """Renders Jinja2 templates for MCP App UI tools.

    Created once at registration time; the Jinja2 Environment is safe
    for concurrent reads (render calls are pure).
    """

    def __init__(self) -> None:
        templates_dir = Path(__file__).parent / "templates"
        self._env = Environment(  # nosemgrep: direct-use-of-jinja2 — autoescape=True is set
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=True,
            undefined=StrictUndefined,
        )
        self._env.filters["status_color"] = _status_color
        self._env.filters["status_label"] = _status_label
        self._env.filters["time_ago"] = _time_ago
        self._env.filters["service_icon"] = _service_icon
        self._env.globals["app_name"] = settings.app_name

    def render(self, template_name: str, **context: object) -> str:
        """Render a template with the given context and return HTML."""
        return self._env.get_template(template_name).render(**context)
