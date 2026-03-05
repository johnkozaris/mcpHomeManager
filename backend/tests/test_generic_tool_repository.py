"""Tests for FakeGenericToolRepository (interface contract) and tool name validation."""

from uuid import uuid4

import pytest

from conftest import FakeGenericToolRepository
from domain.validation import validate_tool_name

@pytest.fixture
def repo() -> FakeGenericToolRepository:
    return FakeGenericToolRepository()


async def test_create_and_get_by_service_id(repo: FakeGenericToolRepository):
    sid = uuid4()
    await repo.create(sid, "list_items", "List items", "GET", "/items", {})
    await repo.create(sid, "create_item", "Create item", "POST", "/items", {"type": "object"})

    rows = await repo.get_by_service_id(sid)
    assert len(rows) == 2
    # Sorted by tool_name
    assert rows[0].tool_name == "create_item"
    assert rows[1].tool_name == "list_items"


async def test_get_by_name(repo: FakeGenericToolRepository):
    sid = uuid4()
    await repo.create(sid, "get_user", "Get a user", "GET", "/users/{id}", {})

    row = await repo.get_by_name(sid, "get_user")
    assert row is not None
    assert row.tool_name == "get_user"
    assert row.description == "Get a user"
    assert row.http_method == "GET"
    assert row.path_template == "/users/{id}"

    # Non-existent tool
    assert await repo.get_by_name(sid, "nonexistent") is None

    # Different service_id
    assert await repo.get_by_name(uuid4(), "get_user") is None


async def test_update(repo: FakeGenericToolRepository):
    sid = uuid4()
    await repo.create(sid, "search", "Search things", "GET", "/search", {"type": "object"})

    updated = await repo.update(
        sid,
        "search",
        description="Search all things",
        http_method="post",
        path_template="/v2/search",
        params_schema={"type": "object", "properties": {"q": {"type": "string"}}},
    )
    assert updated is not None
    assert updated.description == "Search all things"
    assert updated.http_method == "POST"  # upper-cased
    assert updated.path_template == "/v2/search"
    assert updated.params_schema == {"type": "object", "properties": {"q": {"type": "string"}}}


async def test_update_partial(repo: FakeGenericToolRepository):
    sid = uuid4()
    await repo.create(sid, "fetch", "Fetch data", "GET", "/data", {"type": "object"})

    # Only update description
    updated = await repo.update(sid, "fetch", description="Fetch all data")
    assert updated is not None
    assert updated.description == "Fetch all data"
    assert updated.http_method == "GET"  # unchanged
    assert updated.path_template == "/data"  # unchanged
    assert updated.params_schema == {"type": "object"}  # unchanged


async def test_update_not_found(repo: FakeGenericToolRepository):
    sid = uuid4()
    result = await repo.update(sid, "nonexistent", description="new desc")
    assert result is None


async def test_delete(repo: FakeGenericToolRepository):
    sid = uuid4()
    await repo.create(sid, "remove_item", "Remove item", "DELETE", "/items/{id}", {})

    assert await repo.delete(sid, "remove_item") is True
    assert await repo.get_by_name(sid, "remove_item") is None
    assert await repo.get_by_service_id(sid) == []


async def test_delete_not_found(repo: FakeGenericToolRepository):
    sid = uuid4()
    assert await repo.delete(sid, "nonexistent") is False


def test_validate_tool_name_valid():
    # Simple names
    assert validate_tool_name("a") == "a"
    assert validate_tool_name("myTool") == "myTool"
    assert validate_tool_name("list_items") == "list_items"
    assert validate_tool_name("Tool123") == "Tool123"
    assert validate_tool_name("a" * 200) == "a" * 200  # max length


def test_validate_tool_name_invalid():
    invalid_names = [
        "",  # empty string
        "1starts_with_digit",  # starts with number
        "has spaces",  # spaces
        "has-dashes",  # dashes
        "has.dots",  # dots
        "has@special",  # special char
        "a" * 201,  # too long (201 chars)
        "_leading_underscore",  # starts with underscore
    ]
    for name in invalid_names:
        with pytest.raises(ValueError, match="Invalid tool name"):
            validate_tool_name(name)
