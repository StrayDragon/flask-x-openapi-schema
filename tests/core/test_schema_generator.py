"""
Tests for the schema_generator module.

This module tests the OpenAPISchemaGenerator class.
"""

import pytest
from typing import List, Optional

from pydantic import BaseModel, Field

from flask_x_openapi_schema.core.schema_generator import OpenAPISchemaGenerator


# Define test models
class SimpleModel(BaseModel):
    """A simple model for testing."""

    name: str = Field(..., description="The name")
    age: int = Field(..., description="The age")
    email: Optional[str] = Field(None, description="The email")


class ComplexModel(BaseModel):
    """A more complex model for testing."""

    id: str = Field(..., description="The ID")
    name: str = Field(..., description="The name")
    description: Optional[str] = Field(None, description="The description")
    tags: List[str] = Field(default_factory=list, description="Tags")
    items: List[SimpleModel] = Field(default_factory=list, description="Items")
    metadata: dict = Field(default_factory=dict, description="Metadata")


def test_schema_generator_basic():
    """Test basic functionality of OpenAPISchemaGenerator."""
    # Create a schema generator
    generator = OpenAPISchemaGenerator(
        title="Test API", version="1.0.0", description="Test API Description"
    )

    # Generate schema
    schema = generator.generate_schema()

    # Check that the schema was generated correctly
    assert schema["openapi"] == "3.0.3"
    assert schema["info"]["title"] == "Test API"
    assert schema["info"]["version"] == "1.0.0"
    assert schema["info"]["description"] == "Test API Description"
    assert "paths" in schema
    assert "components" in schema
    assert "schemas" in schema["components"]


def test_schema_generator_register_model():
    """Test registering models with OpenAPISchemaGenerator."""
    # Create a schema generator
    generator = OpenAPISchemaGenerator(
        title="Test API", version="1.0.0", description="Test API Description"
    )

    # Register models
    generator._register_model(SimpleModel)
    generator._register_model(ComplexModel)

    # Generate schema
    schema = generator.generate_schema()

    # Check that the models were registered correctly
    assert "SimpleModel" in schema["components"]["schemas"]
    assert "ComplexModel" in schema["components"]["schemas"]

    # Check SimpleModel schema
    simple_schema = schema["components"]["schemas"]["SimpleModel"]
    assert simple_schema["type"] == "object"
    assert "properties" in simple_schema
    assert "name" in simple_schema["properties"]
    assert "age" in simple_schema["properties"]
    assert "email" in simple_schema["properties"]
    assert "required" in simple_schema
    assert "name" in simple_schema["required"]
    assert "age" in simple_schema["required"]
    assert "email" not in simple_schema["required"]

    # Check ComplexModel schema
    complex_schema = schema["components"]["schemas"]["ComplexModel"]
    assert complex_schema["type"] == "object"
    assert "properties" in complex_schema
    assert "id" in complex_schema["properties"]
    assert "name" in complex_schema["properties"]
    assert "description" in complex_schema["properties"]
    assert "tags" in complex_schema["properties"]
    assert "items" in complex_schema["properties"]
    assert "metadata" in complex_schema["properties"]
    assert "required" in complex_schema
    assert "id" in complex_schema["required"]
    assert "name" in complex_schema["required"]
    assert "description" not in complex_schema["required"]


def test_schema_generator_register_model_twice():
    """Test registering the same model twice."""
    # Create a schema generator
    generator = OpenAPISchemaGenerator(
        title="Test API", version="1.0.0", description="Test API Description"
    )

    # Register the same model twice
    generator._register_model(SimpleModel)
    generator._register_model(SimpleModel)

    # Generate schema
    schema = generator.generate_schema()

    # Check that the model was registered correctly
    assert "SimpleModel" in schema["components"]["schemas"]


def test_schema_generator_register_model_with_reference():
    """Test registering models with references to other models."""
    # Create a schema generator
    generator = OpenAPISchemaGenerator(
        title="Test API", version="1.0.0", description="Test API Description"
    )

    # Register ComplexModel (which references SimpleModel)
    generator._register_model(ComplexModel)

    # Generate schema
    schema = generator.generate_schema()

    # Check that both models were registered correctly
    assert "SimpleModel" in schema["components"]["schemas"]
    assert "ComplexModel" in schema["components"]["schemas"]

    # Check that the reference is correct
    complex_schema = schema["components"]["schemas"]["ComplexModel"]
    items_schema = complex_schema["properties"]["items"]
    assert items_schema["type"] == "array"
    assert "items" in items_schema
    assert "$ref" in items_schema["items"]
    assert items_schema["items"]["$ref"] == "#/$defs/SimpleModel"