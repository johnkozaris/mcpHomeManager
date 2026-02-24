"""YAML config export/import for service connections."""

from dataclasses import dataclass, field

import yaml

from domain.entities.service_connection import ServiceConnection, ServiceType

_REDACTED = "<REDACTED>"


@dataclass(frozen=True)
class ImportedServiceSpec:
    """Parsed service specification from a YAML import."""

    name: str
    display_name: str
    service_type: str
    base_url: str
    config: dict = field(default_factory=dict)


class ConfigExporter:
    """Exports and imports service configurations as YAML."""

    def export_yaml(self, services: list[ServiceConnection]) -> str:
        """Serialize services to YAML with tokens redacted."""
        data = {
            "version": "1",
            "services": [
                {
                    "name": svc.name,
                    "display_name": svc.display_name,
                    "service_type": svc.service_type.value,
                    "base_url": svc.base_url,
                    "api_token": _REDACTED,
                    "enabled": svc.is_enabled,
                    "config": svc.config or {},
                }
                for svc in services
            ],
        }
        return yaml.dump(data, default_flow_style=False, sort_keys=False)

    def parse_import(self, yaml_content: str) -> list[ImportedServiceSpec]:
        """Parse and validate a YAML config file."""
        data = yaml.safe_load(yaml_content)
        if not isinstance(data, dict):
            raise ValueError("Invalid YAML: expected a mapping at root")

        raw_services = data.get("services", [])
        if not isinstance(raw_services, list):
            raise ValueError("Invalid YAML: 'services' must be a list")

        result: list[ImportedServiceSpec] = []
        valid_types = {t.value for t in ServiceType}

        for i, entry in enumerate(raw_services):
            if not isinstance(entry, dict):
                raise ValueError(f"Service entry {i} must be a mapping")

            name = entry.get("name")
            if not name or not isinstance(name, str):
                raise ValueError(f"Service entry {i}: 'name' is required")

            display_name = str(entry.get("display_name", name))
            service_type = entry.get("service_type", "")
            if service_type not in valid_types:
                raise ValueError(
                    f"Service entry {i}: invalid service_type '{service_type}'. "
                    f"Must be one of: {', '.join(sorted(valid_types))}"
                )

            base_url = entry.get("base_url", "")
            if not base_url:
                raise ValueError(f"Service entry {i}: 'base_url' is required")

            config = entry.get("config", {})
            if not isinstance(config, dict):
                config = {}

            result.append(
                ImportedServiceSpec(
                    name=name,
                    display_name=display_name,
                    service_type=service_type,
                    base_url=base_url,
                    config=config,
                )
            )

        return result
