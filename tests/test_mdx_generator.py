"""
Tests for the MDX generator module.

This module tests the generation of MDX documentation from OpenAPI schemas.
"""

import json
import os
import pytest
import yaml

from flask_x_openapi_schema.mdx_generator import (
    generate_mdx_from_openapi,
    _create_mdx_content,
)


@pytest.fixture
def simple_schema():
    """Create a simple OpenAPI schema for testing."""
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Test API",
            "version": "1.0.0",
            "description": "Test API Description",
        },
        "paths": {
            "/test": {
                "get": {
                    "summary": "Test endpoint",
                    "description": "This is a test endpoint",
                    "operationId": "testEndpoint",
                    "parameters": [],
                    "responses": {
                        "200": {
                            "description": "Successful response",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {"message": {"type": "string"}},
                                    }
                                }
                            },
                        }
                    },
                }
            }
        },
    }


@pytest.fixture
def complex_schema():
    """Create a complex OpenAPI schema for testing."""
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Complex API",
            "version": "1.0.0",
            "description": "Complex API Description",
        },
        "paths": {
            "/users/{id}": {
                "get": {
                    "summary": "Get user by ID",
                    "description": "Get a user by their unique identifier",
                    "operationId": "getUserById",
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "description": "User ID",
                            "schema": {"type": "string"},
                        },
                        {
                            "name": "include",
                            "in": "query",
                            "required": False,
                            "description": "Fields to include",
                            "schema": {"type": "string"},
                        },
                    ],
                    "responses": {
                        "200": {
                            "description": "Successful response",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/User"}
                                }
                            },
                        },
                        "404": {"description": "User not found"},
                    },
                },
                "post": {
                    "summary": "Create user",
                    "description": "Create a new user",
                    "operationId": "createUser",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/UserInput"}
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "User created",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/User"}
                                }
                            },
                        },
                        "400": {"description": "Invalid input"},
                    },
                },
            }
        },
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "email": {"type": "string"},
                    },
                },
                "UserInput": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string"},
                    },
                },
            }
        },
    }


@pytest.fixture
def i18n_schema():
    """Create an OpenAPI schema with I18nString objects for testing."""
    return {
        "openapi": "3.0.0",
        "info": {
            "title": {
                "type": "i18n_string",
                "value": {"en-US": "Test API", "zh-Hans": "测试 API"},
            },
            "version": "1.0.0",
            "description": {
                "type": "i18n_string",
                "value": {"en-US": "Test API Description", "zh-Hans": "测试 API 描述"},
            },
        },
        "paths": {
            "/test": {
                "get": {
                    "summary": {
                        "type": "i18n_string",
                        "value": {"en-US": "Test endpoint", "zh-Hans": "测试端点"},
                    },
                    "description": {
                        "type": "i18n_string",
                        "value": {
                            "en-US": "This is a test endpoint",
                            "zh-Hans": "这是一个测试端点",
                        },
                    },
                    "operationId": "testEndpoint",
                    "parameters": [
                        {
                            "name": "param",
                            "in": "query",
                            "required": False,
                            "description": {
                                "type": "i18n_string",
                                "value": {
                                    "en-US": "Test parameter",
                                    "zh-Hans": "测试参数",
                                },
                            },
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": {
                                "type": "i18n_string",
                                "value": {
                                    "en-US": "Successful response",
                                    "zh-Hans": "成功响应",
                                },
                            },
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {"message": {"type": "string"}},
                                    }
                                }
                            },
                        }
                    },
                }
            }
        },
    }


def test_generate_mdx_from_openapi(simple_schema, tmp_path):
    """Test generating MDX from a simple OpenAPI schema."""
    output_file = str(tmp_path / "test.mdx")

    # Generate MDX
    generate_mdx_from_openapi(simple_schema, output_file)

    # Check that the file was created
    assert os.path.exists(output_file)

    # Check the content of the file
    with open(output_file, "r") as f:
        content = f.read()

    # Check that the MDX contains the expected content
    assert "title: Test API" in content
    assert "description: Test API Description" in content
    assert "# Test API" in content
    assert "Version: 1.0.0" in content
    assert "## Endpoint: `/test`" in content
    assert "### GET Test endpoint" in content
    assert "This is a test endpoint" in content
    assert "**Operation ID:** `testEndpoint`" in content
    assert "#### Responses" in content
    assert "**200**: Successful response" in content


def test_generate_mdx_from_openapi_with_language(i18n_schema, tmp_path):
    """Test generating MDX from a schema with I18nString objects."""
    output_file = str(tmp_path / "test_en.mdx")

    # Generate MDX in English
    generate_mdx_from_openapi(i18n_schema, output_file, language="en-US")

    # Check the content of the file
    with open(output_file, "r") as f:
        content = f.read()

    # Check that the MDX contains the expected content in English
    assert "title: Test API" in content
    assert "description: Test API Description" in content
    assert "Test endpoint" in content
    assert "This is a test endpoint" in content
    assert "Test parameter" in content
    assert "Successful response" in content

    # Generate MDX in Chinese
    output_file_zh = str(tmp_path / "test_zh.mdx")
    generate_mdx_from_openapi(i18n_schema, output_file_zh, language="zh-Hans")

    # Check the content of the file
    with open(output_file_zh, "r") as f:
        content = f.read()

    # Check that the MDX contains the expected content in Chinese
    assert "title: 测试 API" in content
    assert "description: 测试 API 描述" in content
    assert "测试端点" in content
    assert "这是一个测试端点" in content
    assert "测试参数" in content
    assert "成功响应" in content


def test_create_mdx_content_complex_schema(complex_schema):
    """Test creating MDX content from a complex OpenAPI schema."""
    mdx_content = _create_mdx_content(complex_schema, "en-US")

    # Check that the MDX contains the expected content
    assert "title: Complex API" in mdx_content
    assert "description: Complex API Description" in mdx_content
    assert "# Complex API" in mdx_content
    assert "Version: 1.0.0" in mdx_content
    assert "## Endpoint: `/users/{id}`" in mdx_content
    assert "### GET Get user by ID" in mdx_content
    assert "Get a user by their unique identifier" in mdx_content
    assert "**Operation ID:** `getUserById`" in mdx_content

    # Check path parameters
    assert "**Path Parameters:**" in mdx_content
    assert "| id | string | Yes | User ID |" in mdx_content

    # Check query parameters
    assert "**Query Parameters:**" in mdx_content
    assert "| include | string | No | Fields to include |" in mdx_content

    # Check responses
    assert "**200**: Successful response" in mdx_content
    assert "**404**: User not found" in mdx_content

    # Check POST method
    assert "### POST Create user" in mdx_content
    assert "Create a new user" in mdx_content
    assert "**Operation ID:** `createUser`" in mdx_content

    # Check request body
    assert "**Request Body:**" in mdx_content
    assert "Content Type: `application/json`" in mdx_content
    assert "Schema: `UserInput`" in mdx_content

    # Check responses for POST
    assert "**201**: User created" in mdx_content
    assert "**400**: Invalid input" in mdx_content

    # Check example
    assert "#### Example" in mdx_content
    assert "curl -X GET" in mdx_content
    assert "'https://api.example.com/users/${id}'" in mdx_content

    # Check POST example
    assert "curl -X POST" in mdx_content
    assert "-H 'Content-Type: application/json'" in mdx_content


def test_create_mdx_content_fallback_language(i18n_schema):
    """Test creating MDX content with fallback language."""
    # Use a language that doesn't exist in the schema
    mdx_content = _create_mdx_content(i18n_schema, "fr-FR")

    # Check that it falls back to English
    assert "title: Test API" in mdx_content
    assert "description: Test API Description" in mdx_content
    assert "Test endpoint" in mdx_content
    assert "This is a test endpoint" in mdx_content
    assert "Test parameter" in mdx_content
    assert "Successful response" in mdx_content
