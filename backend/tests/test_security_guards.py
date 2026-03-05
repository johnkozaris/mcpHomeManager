"""Tests for meta-tool admin guard and user context filtering."""

from uuid import uuid4

import pytest

from domain.entities.user import User
from domain.exceptions import ToolExecutionError
from entrypoints.mcp.meta_tools import _require_admin_user, _require_self_mcp_access
from entrypoints.mcp.user_context import (
    can_user_access_service,
    current_user_var,
    filter_services_for_user,
)

def _make_user(*, is_admin: bool = False, allowed_service_ids: list | None = None) -> User:
    return User(
        id=uuid4(),
        username="admin" if is_admin else "viewer",
        api_key_hash="x",
        is_admin=is_admin,
        allowed_service_ids=allowed_service_ids or [],
    )


class TestRequireAdminUser:
    async def test_require_admin_rejects_none_user(self):
        token = current_user_var.set(None)
        try:
            with pytest.raises(ToolExecutionError, match="Admin authentication required"):
                _require_admin_user()
        finally:
            current_user_var.reset(token)

    async def test_require_admin_rejects_non_admin(self):
        user = _make_user(is_admin=False)
        token = current_user_var.set(user)
        try:
            with pytest.raises(ToolExecutionError, match="requires admin privileges"):
                _require_admin_user()
        finally:
            current_user_var.reset(token)

    async def test_require_admin_allows_admin(self):
        user = _make_user(is_admin=True)
        token = current_user_var.set(user)
        try:
            assert _require_admin_user() is None
        finally:
            current_user_var.reset(token)


class TestRequireSelfMcpAccess:
    async def test_rejects_none_user(self):
        token = current_user_var.set(None)
        try:
            with pytest.raises(ToolExecutionError, match="Authentication required"):
                _require_self_mcp_access()
        finally:
            current_user_var.reset(token)

    async def test_rejects_user_without_self_mcp(self):
        user = _make_user(is_admin=False)
        token = current_user_var.set(user)
        try:
            with pytest.raises(ToolExecutionError, match="does not have self-MCP access"):
                _require_self_mcp_access()
        finally:
            current_user_var.reset(token)

    async def test_allows_user_with_self_mcp(self):
        user = User(
            id=uuid4(),
            username="mcpuser",
            api_key_hash="x",
            is_admin=False,
            self_mcp_enabled=True,
        )
        token = current_user_var.set(user)
        try:
            assert _require_self_mcp_access() is None
        finally:
            current_user_var.reset(token)

    async def test_rejects_admin_without_self_mcp(self):
        user = User(
            id=uuid4(),
            username="admin",
            api_key_hash="x",
            is_admin=True,
            self_mcp_enabled=False,
        )
        token = current_user_var.set(user)
        try:
            with pytest.raises(ToolExecutionError, match="does not have self-MCP access"):
                _require_self_mcp_access()
        finally:
            current_user_var.reset(token)


class _FakeService:
    """Minimal stand-in for a service entity with an id attribute."""

    def __init__(self, id):
        self.id = id


class TestFilterServicesForUser:
    async def test_filter_returns_empty_when_user_none(self):
        token = current_user_var.set(None)
        try:
            services = [_FakeService(uuid4())]
            result = await filter_services_for_user(services)
            assert result == []
        finally:
            current_user_var.reset(token)

    async def test_filter_returns_all_for_admin(self):
        user = _make_user(is_admin=True)
        token = current_user_var.set(user)
        try:
            services = [_FakeService(uuid4()), _FakeService(uuid4())]
            result = await filter_services_for_user(services)
            assert result == services
        finally:
            current_user_var.reset(token)

    async def test_filter_restricts_for_non_admin(self):
        allowed_id = uuid4()
        blocked_id = uuid4()
        user = _make_user(is_admin=False, allowed_service_ids=[allowed_id])
        token = current_user_var.set(user)
        try:
            services = [_FakeService(allowed_id), _FakeService(blocked_id)]
            result = await filter_services_for_user(services)
            assert len(result) == 1
            assert result[0].id == allowed_id
        finally:
            current_user_var.reset(token)


class TestCanUserAccessService:
    def test_non_admin_requires_service_id_match(self):
        allowed_id = uuid4()
        user = _make_user(is_admin=False, allowed_service_ids=[allowed_id])
        assert can_user_access_service(user, allowed_id) is True
        assert can_user_access_service(user, uuid4()) is False

    def test_non_admin_cannot_access_missing_service_id(self):
        user = _make_user(is_admin=False)
        assert can_user_access_service(user, None) is False

    def test_admin_can_access_any_service(self):
        user = _make_user(is_admin=True)
        assert can_user_access_service(user, uuid4()) is True
        assert can_user_access_service(user, None) is True
