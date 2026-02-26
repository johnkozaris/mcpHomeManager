"""Tests for AppDefinition entity and IAppProvider protocol."""

from typing import Any, cast

import pytest

from conftest import FakeAppProviderClient
from domain.entities.app_definition import AppDefinition
from domain.ports.app_provider import IAppProvider


def test_app_definition_is_frozen():
    app = AppDefinition(
        name="test",
        service_type="homeassistant",
        title="Test",
        description="A test app",
        template_name="test.html",
    )
    assert app.name == "test"
    assert app.service_type == "homeassistant"
    assert app.title == "Test"
    assert app.description == "A test app"
    assert app.template_name == "test.html"
    assert app.parameters_schema == {}

    # Frozen — cannot mutate
    with pytest.raises(AttributeError):
        cast(Any, app).name = "other"


def test_app_definition_with_params_schema():
    schema = {"type": "object", "properties": {"q": {"type": "string"}}, "required": ["q"]}
    app = AppDefinition(
        name="search",
        service_type="paperless",
        title="Search",
        description="Search docs",
        template_name="search.html",
        parameters_schema=schema,
    )
    assert app.parameters_schema == schema


def test_iapp_provider_isinstance_check():
    client = FakeAppProviderClient()
    assert isinstance(client, IAppProvider)


def test_iapp_provider_get_definitions():
    client = FakeAppProviderClient()
    defs = client.get_app_definitions()
    assert len(defs) == 1
    assert defs[0].name == "test_app"


async def test_iapp_provider_fetch_data():
    client = FakeAppProviderClient()
    data = await client.fetch_app_data("test_app", {})
    assert "test_key" in data


async def test_iapp_provider_handle_action():
    client = FakeAppProviderClient()
    result = await client.handle_app_action("test_app", "refresh", {})
    assert result["action"] == "refresh"
    assert result["handled"] is True
