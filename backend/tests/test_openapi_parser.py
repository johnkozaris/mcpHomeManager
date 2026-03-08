"""Tests for the OpenAPI parser."""

import json

import pytest

from domain.entities.generic_tool_spec import REQUEST_SHAPE_METADATA_KEY
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
    def test_rejects_missing_openapi_version(self):
        with pytest.raises(
            ValueError,
            match=r"expected a root 'openapi' field with a 3\.x version",
        ):
            OpenAPIParser.parse(
                json.dumps(
                    {
                        "info": {"title": "Test", "version": "1.0"},
                        "paths": {"/pets": {"get": {"operationId": "listPets"}}},
                    }
                )
            )

    def test_rejects_non_3x_openapi_version(self):
        with pytest.raises(ValueError, match=r"Unsupported OpenAPI version '2\.0'"):
            OpenAPIParser.parse(
                json.dumps(
                    {
                        "openapi": "2.0",
                        "info": {"title": "Test", "version": "1.0"},
                        "paths": {"/pets": {"get": {"operationId": "listPets"}}},
                    }
                )
            )

    def test_parse_json_spec(self):
        result = OpenAPIParser.parse(json.dumps(PETSTORE_SPEC))
        assert len(result.tools) == 3
        assert result.warnings == []
        names = {s.tool_name for s in result.tools}
        assert names == {"listPets", "createPet", "getPet"}

    def test_parse_yaml_spec(self):
        import yaml

        yaml_content = yaml.dump(PETSTORE_SPEC)
        result = OpenAPIParser.parse(yaml_content)
        assert len(result.tools) == 3
        assert result.warnings == []

    def test_params_include_path_params_and_metadata(self):
        result = OpenAPIParser.parse(json.dumps(PETSTORE_SPEC))
        get_pet = next(s for s in result.tools if s.tool_name == "getPet")
        assert "petId" in get_pet.params_schema["properties"]
        assert "petId" in get_pet.params_schema.get("required", [])
        metadata = get_pet.params_schema[REQUEST_SHAPE_METADATA_KEY]
        assert metadata["parameters"]["petId"]["in"] == "path"

    def test_params_include_body_params_and_metadata(self):
        result = OpenAPIParser.parse(json.dumps(PETSTORE_SPEC))
        create_pet = next(s for s in result.tools if s.tool_name == "createPet")
        props = create_pet.params_schema["properties"]
        assert "name" in props
        assert "tag" in props
        assert "name" in create_pet.params_schema.get("required", [])
        assert create_pet.params_schema[REQUEST_SHAPE_METADATA_KEY]["body"] == {
            "mediaType": "application/json",
            "encoding": "json",
            "propertyNames": ["name", "tag"],
            "required": False,
        }

    def test_merges_path_item_and_operation_parameters(self):
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0"},
            "paths": {
                "/widgets/{widgetId}": {
                    "parameters": [
                        {
                            "name": "widgetId",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        },
                        {"name": "trace", "in": "header", "schema": {"type": "string"}},
                    ],
                    "post": {
                        "operationId": "updateWidget",
                        "parameters": [
                            {"name": "verbose", "in": "query", "schema": {"type": "boolean"}},
                            {
                                "name": "trace",
                                "in": "header",
                                "schema": {"type": "string", "description": "Override"},
                            },
                        ],
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {"name": {"type": "string"}},
                                        "required": ["name"],
                                    }
                                }
                            }
                        },
                    },
                }
            },
        }

        result = OpenAPIParser.parse(json.dumps(spec))
        tool = result.tools[0]
        metadata = tool.params_schema[REQUEST_SHAPE_METADATA_KEY]

        assert result.warnings == []
        assert set(tool.params_schema["properties"]) == {"widgetId", "trace", "verbose", "name"}
        assert metadata["parameters"]["widgetId"]["in"] == "path"
        assert metadata["parameters"]["trace"]["in"] == "header"
        assert metadata["parameters"]["verbose"]["in"] == "query"
        assert tool.params_schema["properties"]["trace"]["description"] == "Override"

    def test_supports_form_urlencoded_request_bodies(self):
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0"},
            "paths": {
                "/sessions": {
                    "post": {
                        "operationId": "createSession",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/x-www-form-urlencoded": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "username": {"type": "string"},
                                            "password": {"type": "string"},
                                        },
                                        "required": ["username", "password"],
                                    }
                                }
                            },
                        },
                    }
                }
            },
        }

        result = OpenAPIParser.parse(json.dumps(spec))
        tool = result.tools[0]
        assert result.warnings == []
        assert tool.params_schema[REQUEST_SHAPE_METADATA_KEY]["body"] == {
            "mediaType": "application/x-www-form-urlencoded",
            "encoding": "form-urlencoded",
            "propertyNames": ["username", "password"],
            "required": True,
        }

    def test_warns_and_skips_unsupported_request_shapes(self):
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0"},
            "paths": {
                "/reports": {
                    "post": {
                        "operationId": "createReport",
                        "requestBody": {
                            "content": {
                                "multipart/form-data": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "file": {"type": "string", "format": "binary"}
                                        },
                                    }
                                }
                            }
                        },
                    },
                    "head": {
                        "operationId": "headReports",
                    },
                }
            },
        }

        result = OpenAPIParser.parse(json.dumps(spec))
        assert result.tools == []
        assert result.warnings == [
            "Skipped createReport: unsupported request body media types (multipart/form-data)",
            "Skipped HEAD /reports: unsupported HTTP method",
        ]

    def test_duplicate_names_across_request_parts_are_rejected(self):
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0"},
            "paths": {
                "/widgets": {
                    "post": {
                        "operationId": "createWidget",
                        "parameters": [
                            {"name": "id", "in": "query", "schema": {"type": "string"}},
                        ],
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {"id": {"type": "string"}},
                                    }
                                }
                            }
                        },
                    }
                }
            },
        }

        result = OpenAPIParser.parse(json.dumps(spec))
        assert result.tools == []
        assert result.warnings == [
            "Skipped createWidget: duplicate argument name 'id' across body and other request parts"
        ]

    def test_resolves_path_item_refs_and_escaped_json_pointer_refs(self):
        spec = {
            "openapi": "3.1.1",
            "info": {"title": "Test", "version": "1.0"},
            "components": {
                "pathItems": {
                    "widgets": {
                        "get": {
                            "operationId": "listWidgets",
                        }
                    }
                },
                "schemas": {
                    "Widget/Input~v2": {
                        "type": "object",
                        "properties": {"name": {"type": "string"}},
                        "required": ["name"],
                    }
                },
            },
            "paths": {
                "/widgets": {
                    "$ref": "#/components/pathItems/widgets",
                },
                "/widgets/import": {
                    "post": {
                        "operationId": "importWidget",
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/Widget~1Input~0v2"
                                    }
                                }
                            }
                        },
                    }
                },
            },
        }

        result = OpenAPIParser.parse(json.dumps(spec))
        names = {tool.tool_name for tool in result.tools}

        assert result.warnings == []
        assert names == {"listWidgets", "importWidget"}

        import_widget = next(tool for tool in result.tools if tool.tool_name == "importWidget")
        assert import_widget.params_schema["properties"]["name"]["type"] == "string"
        assert import_widget.params_schema["required"] == ["name"]

    def test_path_template_parameters_must_be_declared(self):
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0"},
            "paths": {
                "/pets/{petId}": {
                    "get": {
                        "operationId": "getPet",
                    }
                }
            },
        }

        result = OpenAPIParser.parse(json.dumps(spec))
        assert result.tools == []
        assert result.warnings == [
            "Skipped getPet: path template parameters missing OpenAPI path definitions (petId)"
        ]

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
        result = OpenAPIParser.parse(json.dumps(spec))
        assert len(result.tools) == 1
        assert result.tools[0].tool_name == "get_api_users"
