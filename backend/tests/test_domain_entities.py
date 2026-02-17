"""Tests for domain entities."""

from datetime import UTC
from typing import Any, cast

import pytest

from domain.entities.audit_entry import AuditEntry, CallStatus
from domain.entities.service_connection import (
    HealthStatus,
    ServiceConnection,
    ServiceType,
)
from domain.entities.tool_definition import ToolDefinition


class TestServiceConnection:
    def test_defaults(self) -> None:
        svc = ServiceConnection(
            name="forgejo",
            display_name="Forgejo",
            service_type=ServiceType.FORGEJO,
            base_url="http://forgejo:3000",
            api_token_encrypted="encrypted",
        )
        assert svc.is_enabled is True
        assert svc.health_status == HealthStatus.UNKNOWN
        assert svc.last_health_check is None
        assert svc.config == {}
        assert svc.id is None

    def test_mark_healthy(self) -> None:
        svc = ServiceConnection(
            name="test",
            display_name="Test",
            service_type=ServiceType.FORGEJO,
            base_url="http://test",
            api_token_encrypted="enc",
        )
        svc.mark_healthy()
        assert svc.health_status == HealthStatus.HEALTHY
        assert svc.last_health_check is not None
        assert svc.last_health_check.tzinfo == UTC

    def test_mark_unhealthy(self) -> None:
        svc = ServiceConnection(
            name="test",
            display_name="Test",
            service_type=ServiceType.FORGEJO,
            base_url="http://test",
            api_token_encrypted="enc",
        )
        svc.mark_unhealthy()
        assert svc.health_status == HealthStatus.UNHEALTHY
        assert svc.last_health_check is not None

    def test_update_connection_partial(self) -> None:
        svc = ServiceConnection(
            name="test",
            display_name="Old Name",
            service_type=ServiceType.FORGEJO,
            base_url="http://old",
            api_token_encrypted="enc",
        )
        svc.update_connection(display_name="New Name")
        assert svc.display_name == "New Name"
        assert svc.base_url == "http://old"  # unchanged

    def test_update_connection_all_fields(self) -> None:
        svc = ServiceConnection(
            name="test",
            display_name="Old",
            service_type=ServiceType.FORGEJO,
            base_url="http://old",
            api_token_encrypted="old-enc",
        )
        svc.update_connection(
            display_name="New",
            base_url="http://new",
            api_token_encrypted="new-enc",
            is_enabled=False,
            config={"key": "value"},
        )
        assert svc.display_name == "New"
        assert svc.base_url == "http://new"
        assert svc.api_token_encrypted == "new-enc"
        assert svc.is_enabled is False
        assert svc.config == {"key": "value"}

    def test_update_connection_none_does_not_change(self) -> None:
        svc = ServiceConnection(
            name="test",
            display_name="Keep",
            service_type=ServiceType.FORGEJO,
            base_url="http://keep",
            api_token_encrypted="keep",
            is_enabled=True,
        )
        svc.update_connection()  # all None
        assert svc.display_name == "Keep"
        assert svc.base_url == "http://keep"
        assert svc.is_enabled is True


class TestServiceType:
    def test_all_types_are_strings(self) -> None:
        for st in ServiceType:
            assert isinstance(st.value, str)

    def test_expected_types(self) -> None:
        expected = {
            "forgejo",
            "homeassistant",
            "paperless",
            "immich",
            "nextcloud",
            "uptimekuma",
            "adguard",
            "nginxproxymanager",
            "portainer",
            "freshrss",
            "wallabag",
            "stirlingpdf",
            "wikijs",
            "calibreweb",
            "tailscale",
            "cloudflare",
            "generic_rest",
        }
        assert {st.value for st in ServiceType} == expected


class TestToolDefinition:
    def test_frozen(self) -> None:
        tool = ToolDefinition(
            name="test_tool",
            service_type=ServiceType.FORGEJO,
            description="A test tool",
        )
        # frozen dataclass should raise on mutation
        with pytest.raises(AttributeError):
            cast(Any, tool).name = "changed"

    def test_defaults(self) -> None:
        tool = ToolDefinition(
            name="t",
            service_type=ServiceType.PAPERLESS,
            description="desc",
        )
        assert tool.is_enabled is True
        assert tool.parameters_schema == {}


class TestAuditEntry:
    def test_success_entry(self) -> None:
        entry = AuditEntry(
            service_name="forgejo",
            tool_name="list_repos",
            input_summary="{}",
            status=CallStatus.SUCCESS,
            duration_ms=42,
        )
        assert entry.error_message is None
        assert entry.id is None

    def test_error_entry(self) -> None:
        entry = AuditEntry(
            service_name="forgejo",
            tool_name="list_repos",
            input_summary="{}",
            status=CallStatus.ERROR,
            duration_ms=100,
            error_message="Connection refused",
        )
        assert entry.status == CallStatus.ERROR
        assert entry.error_message == "Connection refused"
