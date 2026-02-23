"""Tests for MCP Apps — HTML UI tools rendered via Jinja2."""

import json
from datetime import UTC, datetime

import pytest
from jinja2.exceptions import UndefinedError

from entrypoints.mcp.template_engine import TemplateEngine

# -- Helpers --


def _make_service_ctx(
    *,
    name: str = "forgejo",
    display_name: str = "Forgejo",
    service_type: str = "forgejo",
    health_status: str = "healthy",
    is_enabled: bool = True,
    tool_count: int = 3,
) -> dict:
    return {
        "name": name,
        "display_name": display_name,
        "service_type": service_type,
        "health_status": health_status,
        "is_enabled": is_enabled,
        "tool_count": tool_count,
    }


def _make_log_ctx(
    *,
    tool_name: str = "ha_get_entity_state",
    service_name: str = "homeassistant",
    status: str = "success",
    duration_ms: int = 42,
    client_name: str | None = "claude",
    created_at: datetime | None = None,
) -> dict:
    return {
        "tool_name": tool_name,
        "service_name": service_name,
        "status": status,
        "duration_ms": duration_ms,
        "client_name": client_name,
        "created_at": created_at or datetime.now(UTC),
    }


# -- Template Engine --


class TestTemplateEngine:
    def test_render_basic(self) -> None:
        """TemplateEngine renders a template with context variables."""
        engine = TemplateEngine()
        html = engine.render(
            "dashboard.html",
            services=[],
            recent_logs=[],
            stats={"services_total": 0, "services_healthy": 0, "tools_enabled": 0},
        )
        assert "<!DOCTYPE html>" in html
        assert "Dashboard" in html

    def test_render_missing_variable_raises(self) -> None:
        """StrictUndefined causes an error when a required variable is missing."""
        engine = TemplateEngine()
        with pytest.raises(UndefinedError):
            engine.render("dashboard.html")


# -- Dashboard --


class TestDashboardTemplate:
    def test_dashboard_empty(self) -> None:
        """Dashboard renders cleanly with no services or logs."""
        engine = TemplateEngine()
        html = engine.render(
            "dashboard.html",
            services=[],
            recent_logs=[],
            stats={"services_total": 0, "services_healthy": 0, "tools_enabled": 0},
        )
        assert "No services connected yet." in html
        assert "No recent tool calls." in html
        assert "0" in html  # stats show zeroes

    def test_dashboard_with_services(self) -> None:
        """Dashboard shows service cards with names and health badges."""
        engine = TemplateEngine()
        services = [
            _make_service_ctx(name="forgejo", display_name="Forgejo", health_status="healthy"),
            _make_service_ctx(
                name="ha",
                display_name="Home Assistant",
                service_type="homeassistant",
                health_status="unhealthy",
            ),
        ]
        logs = [_make_log_ctx()]
        html = engine.render(
            "dashboard.html",
            services=services,
            recent_logs=logs,
            stats={"services_total": 2, "services_healthy": 1, "tools_enabled": 5},
        )
        assert "Forgejo" in html
        assert "Home Assistant" in html
        assert "status-healthy" in html
        assert "status-unhealthy" in html
        assert "ha_get_entity_state" in html


# -- Control Panel --


class TestControlTemplate:
    def test_control_panel(self) -> None:
        """Control panel renders tool list for a service."""
        engine = TemplateEngine()
        html = engine.render(
            "control.html",
            service={
                "name": "ha",
                "display_name": "Home Assistant",
                "service_type": "homeassistant",
                "health_status": "healthy",
                "base_url": "http://ha:8123",
            },
            tools=[
                {
                    "name": "ha_get_entity_state",
                    "description": "Get entity state",
                    "is_enabled": True,
                },
                {"name": "ha_call_service", "description": "Call a service", "is_enabled": False},
            ],
        )
        assert "Home Assistant" in html
        assert "ha_get_entity_state" in html
        assert "ha_call_service" in html
        assert "enabled" in html
        assert "disabled" in html


# -- Config View --


class TestConfigTemplate:
    def test_config_single_service(self) -> None:
        """Config view renders JSON for one service."""
        engine = TemplateEngine()
        html = engine.render(
            "config.html",
            services=[
                {
                    "name": "paperless",
                    "display_name": "Paperless",
                    "service_type": "paperless",
                    "base_url": "http://paperless:8000",
                    "config": {"tag_filter": "inbox"},
                    "config_json": json.dumps({"tag_filter": "inbox"}, indent=2),
                }
            ],
            single=True,
        )
        assert "Paperless" in html
        assert "tag_filter" in html

    def test_config_all_services(self) -> None:
        """Config view renders multiple services."""
        engine = TemplateEngine()
        html = engine.render(
            "config.html",
            services=[
                {
                    "name": "forgejo",
                    "display_name": "Forgejo",
                    "service_type": "forgejo",
                    "base_url": "http://forgejo:3000",
                    "config": {},
                    "config_json": "{}",
                },
                {
                    "name": "ha",
                    "display_name": "Home Assistant",
                    "service_type": "homeassistant",
                    "base_url": "http://ha:8123",
                    "config": {"area": "living_room"},
                    "config_json": json.dumps({"area": "living_room"}, indent=2),
                },
            ],
            single=False,
        )
        assert "Forgejo" in html
        assert "Home Assistant" in html
        assert "All services" in html


# -- Security --


class TestSecurity:
    def test_no_unexpected_script_tags(self) -> None:
        """No rendered template should contain unexpected <script> tags.

        The base template has one intentional <script> for the mcpAction
        postMessage bridge — we allow that but forbid any others.
        """
        engine = TemplateEngine()

        dashboard = engine.render(
            "dashboard.html",
            services=[_make_service_ctx()],
            recent_logs=[_make_log_ctx()],
            stats={"services_total": 1, "services_healthy": 1, "tools_enabled": 3},
        )
        # Only the base template's mcpAction script should be present
        assert dashboard.lower().count("<script") == 1
        assert "mcpaction" in dashboard.lower()

        control = engine.render(
            "control.html",
            service={
                "name": "ha",
                "display_name": "HA",
                "service_type": "homeassistant",
                "health_status": "healthy",
                "base_url": "http://ha:8123",
            },
            tools=[],
        )
        assert control.lower().count("<script") == 1

        config = engine.render(
            "config.html",
            services=[],
            single=False,
        )
        assert config.lower().count("<script") == 1

    def test_xss_escaped_display_name(self) -> None:
        """XSS in display_name is escaped in the dashboard."""
        engine = TemplateEngine()
        xss = '<img src=x onerror="alert(1)">'

        html = engine.render(
            "dashboard.html",
            services=[_make_service_ctx(display_name=xss)],
            recent_logs=[],
            stats={"services_total": 1, "services_healthy": 0, "tools_enabled": 0},
        )
        assert xss not in html
        assert "&lt;img" in html

    def test_xss_escaped_tool_description(self) -> None:
        """XSS in tool description is escaped in the control panel."""
        engine = TemplateEngine()
        xss = '<script>alert("xss")</script>'

        html = engine.render(
            "control.html",
            service={
                "name": "test",
                "display_name": "Test",
                "service_type": "forgejo",
                "health_status": "healthy",
                "base_url": "http://test:3000",
            },
            tools=[{"name": "t", "description": xss, "is_enabled": True}],
        )
        # The injected XSS should be escaped (the base template's mcpAction script is allowed)
        assert 'alert("xss")' not in html
        assert "&lt;script&gt;" in html

    def test_xss_escaped_tool_name(self) -> None:
        """XSS in tool name is escaped in the control panel."""
        engine = TemplateEngine()
        xss = "<img src=x onerror=alert(1)>"

        html = engine.render(
            "control.html",
            service={
                "name": "test",
                "display_name": "Test",
                "service_type": "forgejo",
                "health_status": "healthy",
                "base_url": "http://test:3000",
            },
            tools=[{"name": xss, "description": "desc", "is_enabled": True}],
        )
        assert xss not in html
        assert "&lt;img" in html

    def test_xss_escaped_base_url(self) -> None:
        """XSS in base_url is escaped in the control panel."""
        engine = TemplateEngine()
        xss = 'javascript:alert(1)"><script>x</script>'

        html = engine.render(
            "control.html",
            service={
                "name": "test",
                "display_name": "Test",
                "service_type": "forgejo",
                "health_status": "healthy",
                "base_url": xss,
            },
            tools=[],
        )
        # The injected XSS should be escaped
        assert 'alert(1)"><script>x</script>' not in html
        assert "&lt;script&gt;" in html

    def test_xss_escaped_config_json(self) -> None:
        """XSS in config JSON values is escaped in config view."""
        engine = TemplateEngine()
        xss = '<script>alert("xss")</script>'

        html = engine.render(
            "config.html",
            services=[
                {
                    "name": "test",
                    "display_name": "Test",
                    "service_type": "forgejo",
                    "base_url": "http://test",
                    "config": {"key": xss},
                    "config_json": json.dumps({"key": xss}),
                }
            ],
            single=True,
        )
        assert "<script>alert" not in html

    def test_xss_escaped_audit_log_fields(self) -> None:
        """XSS in audit log tool_name and service_name is escaped."""
        engine = TemplateEngine()
        xss = "<img src=x onerror=alert(1)>"

        html = engine.render(
            "dashboard.html",
            services=[],
            recent_logs=[_make_log_ctx(tool_name=xss, service_name=xss)],
            stats={"services_total": 0, "services_healthy": 0, "tools_enabled": 0},
        )
        assert xss not in html
        assert "&lt;img" in html

    def test_no_api_token_in_output(self) -> None:
        """Encrypted API tokens must never appear in any rendered template."""
        engine = TemplateEngine()

        # Control panel — service context never includes api_token_encrypted
        html = engine.render(
            "control.html",
            service={
                "name": "test",
                "display_name": "Test",
                "service_type": "forgejo",
                "health_status": "healthy",
                "base_url": "http://test:3000",
            },
            tools=[],
        )
        assert "api_token" not in html.lower()
        assert "encrypted" not in html.lower()
