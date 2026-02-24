"""Tests for the OpenAPI parser."""

import json

from services.openapi_parser import OpenAPIParser

PETSTORE_SPEC = {
    "openapi": "3.0.0",
    "info": {"title": "Petstore", "version": "1.0"},
    "paths": {
        "/pets": {
            "get": {
                "operationId": "listPets",
                "summary": "List all pets",
                "parameters": [
                    {"name": "limit", "in": "query", "schema": {"type": "integer"}},
                ],
            },
            "post": {
                "operationId": "createPet",
                "summary": "Create a pet",
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string", "description": "Pet name"},
                                    "tag": {"type": "string"},
                                },
                                "required": ["name"],
                            }
                        }
                    }
                },
            },
        },
        "/pets/{petId}": {
            "get": {
                "operationId": "getPet",
                "summary": "Get a pet by ID",
                "parameters": [
                    {"name": "petId", "in": "path", "required": True, "schema": {"type": "string"}},
                ],
            },
        },
    },
}


class TestOpenAPIParser:
    def test_parse_json_spec(self):
        specs = OpenAPIParser.parse(json.dumps(PETSTORE_SPEC))
        assert len(specs) == 3
        names = {s.tool_name for s in specs}
        assert names == {"listPets", "createPet", "getPet"}

    def test_parse_yaml_spec(self):
        import yaml

        yaml_content = yaml.dump(PETSTORE_SPEC)
        specs = OpenAPIParser.parse(yaml_content)
        assert len(specs) == 3

    def test_params_include_path_params(self):
        specs = OpenAPIParser.parse(json.dumps(PETSTORE_SPEC))
        get_pet = next(s for s in specs if s.tool_name == "getPet")
        assert "petId" in get_pet.params_schema["properties"]
        assert "petId" in get_pet.params_schema.get("required", [])

    def test_params_include_body_params(self):
        specs = OpenAPIParser.parse(json.dumps(PETSTORE_SPEC))
        create_pet = next(s for s in specs if s.tool_name == "createPet")
        props = create_pet.params_schema["properties"]
        assert "name" in props
        assert "tag" in props
        assert "name" in create_pet.params_schema.get("required", [])

    def test_fallback_tool_name_from_path(self):
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0"},
            "paths": {
                "/api/users": {
                    "get": {"summary": "List users"},
                },
            },
        }
        specs = OpenAPIParser.parse(json.dumps(spec))
        assert len(specs) == 1
        assert specs[0].tool_name == "get_api_users"
