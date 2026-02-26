"""Tests for permission profiles."""

from typing import Any, cast

import pytest

from domain.entities.service_connection import ServiceType
from services.permission_profiles import PROFILES, PermissionProfile


class TestPermissionProfiles:
    def test_all_service_types_have_profiles(self) -> None:
        for svc_type in ServiceType:
            assert svc_type in PROFILES, f"Missing profiles for {svc_type}"
            if svc_type == ServiceType.GENERIC_REST:
                continue  # Generic REST has user-defined tools, no preset profiles
            assert len(PROFILES[svc_type]) >= 2, f"Need at least 2 profiles for {svc_type}"

    def test_profile_structure(self) -> None:
        for profiles in PROFILES.values():
            for profile in profiles:
                assert isinstance(profile, PermissionProfile)
                assert profile.name
                assert profile.label
                assert profile.description
                assert isinstance(profile.tool_states, dict)

    def test_read_only_profile_disables_writes(self) -> None:
        forgejo_profiles = PROFILES[ServiceType.FORGEJO]
        read_only = next(p for p in forgejo_profiles if p.name == "read_only")

        assert read_only.tool_states["forgejo_list_repos"] is True
        assert read_only.tool_states["forgejo_create_issue"] is False
        assert read_only.tool_states["forgejo_create_pull_request"] is False

    def test_admin_profile_enables_all(self) -> None:
        forgejo_profiles = PROFILES[ServiceType.FORGEJO]
        admin = next(p for p in forgejo_profiles if p.name == "admin")

        assert all(v is True for v in admin.tool_states.values())

    def test_profile_is_frozen(self) -> None:
        profile = PROFILES[ServiceType.FORGEJO][0]
        with pytest.raises(AttributeError):
            cast(Any, profile).name = "changed"

    def test_ha_read_only_disables_call_service(self) -> None:
        ha_profiles = PROFILES[ServiceType.HOME_ASSISTANT]
        read_only = next(p for p in ha_profiles if p.name == "read_only")
        assert read_only.tool_states["ha_call_service"] is False
        assert read_only.tool_states["ha_get_entity_state"] is True

    def test_uptimekuma_read_only(self) -> None:
        profiles = PROFILES[ServiceType.UPTIME_KUMA]
        read_only = next(p for p in profiles if p.name == "read_only")
        assert read_only.tool_states["uptimekuma_list_monitors"] is True
        assert read_only.tool_states["uptimekuma_pause_monitor"] is False
