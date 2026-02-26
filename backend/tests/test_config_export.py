"""Tests for YAML config export/import."""

import pytest
import yaml

from domain.entities.service_connection import ServiceConnection, ServiceType
from services.config_export import ConfigExporter


def _make_service(
    name: str = "forgejo", svc_type: ServiceType = ServiceType.FORGEJO
) -> ServiceConnection:
    return ServiceConnection(
        name=name,
        display_name=name.title(),
        service_type=svc_type,
        base_url=f"http://{name}:3000",
        api_token_encrypted="encrypted_token",
        config={"key": "value"},
    )


class TestConfigExporter:
    def test_export_yaml(self) -> None:
        exporter = ConfigExporter()
        services = [_make_service("forgejo"), _make_service("paperless", ServiceType.PAPERLESS)]
        result = exporter.export_yaml(services)

        data = yaml.safe_load(result)
        assert data["version"] == "1"
        assert len(data["services"]) == 2
        assert data["services"][0]["name"] == "forgejo"
        assert data["services"][0]["service_type"] == "forgejo"
        assert data["services"][1]["name"] == "paperless"

    def test_export_redacts_tokens(self) -> None:
        exporter = ConfigExporter()
        result = exporter.export_yaml([_make_service()])
        data = yaml.safe_load(result)
        assert data["services"][0]["api_token"] == "<REDACTED>"

    def test_round_trip(self) -> None:
        exporter = ConfigExporter()
        services = [_make_service("forgejo"), _make_service("paperless", ServiceType.PAPERLESS)]
        yaml_content = exporter.export_yaml(services)
        specs = exporter.parse_import(yaml_content)

        assert len(specs) == 2
        assert specs[0].name == "forgejo"
        assert specs[0].service_type == "forgejo"
        assert specs[0].base_url == "http://forgejo:3000"
        assert specs[1].name == "paperless"

    def test_parse_import_validates_service_type(self) -> None:
        exporter = ConfigExporter()
        yaml_content = yaml.dump(
            {
                "version": "1",
                "services": [{"name": "bad", "service_type": "invalid", "base_url": "http://x"}],
            }
        )
        with pytest.raises(ValueError, match="invalid service_type"):
            exporter.parse_import(yaml_content)

    def test_parse_import_requires_name(self) -> None:
        exporter = ConfigExporter()
        yaml_content = yaml.dump(
            {
                "version": "1",
                "services": [{"service_type": "forgejo", "base_url": "http://x"}],
            }
        )
        with pytest.raises(ValueError, match="name"):
            exporter.parse_import(yaml_content)

    def test_parse_import_requires_base_url(self) -> None:
        exporter = ConfigExporter()
        yaml_content = yaml.dump(
            {
                "version": "1",
                "services": [{"name": "test", "service_type": "forgejo"}],
            }
        )
        with pytest.raises(ValueError, match="base_url"):
            exporter.parse_import(yaml_content)

    def test_parse_import_empty_services(self) -> None:
        exporter = ConfigExporter()
        yaml_content = yaml.dump({"version": "1", "services": []})
        specs = exporter.parse_import(yaml_content)
        assert specs == []

    def test_parse_import_invalid_root(self) -> None:
        exporter = ConfigExporter()
        with pytest.raises(ValueError):
            exporter.parse_import("just a string")
