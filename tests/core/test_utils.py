"""Tests for the utils module.

This module tests the utility functions for converting Pydantic models to OpenAPI schemas.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from flask_x_openapi_schema.core.utils import pydantic_to_openapi_schema


# Define test models
class SimpleModel(BaseModel):
    """A simple model for testing."""

    name: str = Field(..., description="The name")
    age: int = Field(..., description="The age")
    email: str | None = Field(None, description="The email")


class Color(str, Enum):
    """Color enum for testing."""

    RED = "red"
    GREEN = "green"
    BLUE = "blue"


class ComplexModel(BaseModel):
    """A more complex model for testing."""

    id: str = Field(..., description="The ID")
    name: str = Field(..., description="The name")
    description: str | None = Field(None, description="The description")
    tags: list[str] = Field(default_factory=list, description="Tags")
    color: Color = Field(Color.RED, description="The color")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata")


def test_pydantic_to_openapi_schema_simple():
    """Test pydantic_to_openapi_schema with a simple model."""
    # Convert the model to an OpenAPI schema
    schema = pydantic_to_openapi_schema(SimpleModel)

    # Check that the schema was generated correctly
    assert schema["type"] == "object"
    assert "properties" in schema
    assert "name" in schema["properties"]
    assert "age" in schema["properties"]
    assert "email" in schema["properties"]

    # Check property types
    assert schema["properties"]["name"]["type"] == "string"
    assert schema["properties"]["age"]["type"] == "integer"
    # In Pydantic v2, Optional fields are handled differently
    assert "anyOf" in schema["properties"]["email"]

    # Check property descriptions
    assert schema["properties"]["name"]["description"] == "The name"
    assert schema["properties"]["age"]["description"] == "The age"
    assert schema["properties"]["email"]["description"] == "The email"

    # Check required properties
    assert "required" in schema
    assert "name" in schema["required"]
    assert "age" in schema["required"]
    assert "email" not in schema["required"]


def test_pydantic_to_openapi_schema_complex():
    """Test pydantic_to_openapi_schema with a complex model."""
    # Convert the model to an OpenAPI schema
    schema = pydantic_to_openapi_schema(ComplexModel)

    # Check that the schema was generated correctly
    assert schema["type"] == "object"
    assert "properties" in schema
    assert "id" in schema["properties"]
    assert "name" in schema["properties"]
    assert "description" in schema["properties"]
    assert "tags" in schema["properties"]
    assert "color" in schema["properties"]
    assert "metadata" in schema["properties"]

    # Check property types
    assert schema["properties"]["id"]["type"] == "string"
    assert schema["properties"]["name"]["type"] == "string"
    # In Pydantic v2, Optional fields are handled differently
    assert "anyOf" in schema["properties"]["description"]
    assert schema["properties"]["tags"]["type"] == "array"
    assert schema["properties"]["tags"]["items"]["type"] == "string"
    # In Pydantic v2, enums are handled differently
    assert "$ref" in schema["properties"]["color"]
    assert schema["properties"]["metadata"]["type"] == "object"

    # Check property descriptions
    assert schema["properties"]["id"]["description"] == "The ID"
    assert schema["properties"]["name"]["description"] == "The name"
    assert schema["properties"]["description"]["description"] == "The description"
    assert schema["properties"]["tags"]["description"] == "Tags"
    assert schema["properties"]["color"]["description"] == "The color"
    assert schema["properties"]["metadata"]["description"] == "Metadata"

    # Check required properties
    assert "required" in schema
    assert "id" in schema["required"]
    assert "name" in schema["required"]
    assert "description" not in schema["required"]
    assert "tags" not in schema["required"]
    assert "color" not in schema["required"]
    assert "metadata" not in schema["required"]


def test_pydantic_to_openapi_schema_nested():
    """Test pydantic_to_openapi_schema with nested models."""

    # Define a nested model
    class Address(BaseModel):
        """Address model for testing."""

        street: str = Field(..., description="The street")
        city: str = Field(..., description="The city")
        country: str = Field(..., description="The country")

    class User(BaseModel):
        """User model for testing."""

        name: str = Field(..., description="The name")
        address: Address = Field(..., description="The address")

    # Convert the model to an OpenAPI schema
    schema = pydantic_to_openapi_schema(User)

    # Check that the schema was generated correctly
    assert schema["type"] == "object"
    assert "properties" in schema
    assert "name" in schema["properties"]
    assert "address" in schema["properties"]

    # Check that the nested model is referenced correctly
    assert "$ref" in schema["properties"]["address"]
    assert schema["properties"]["address"]["$ref"] == "#/components/schemas/Address"
