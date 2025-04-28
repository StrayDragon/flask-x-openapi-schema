"""Tests for the schema_generator module.

This module tests the OpenAPISchemaGenerator class.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from flask_x_openapi_schema.core.schema_generator import OpenAPISchemaGenerator


# Define test models
class SimpleModel(BaseModel):
    """A simple model for testing."""

    name: str = Field(..., description="The name")
    age: int = Field(..., description="The age")
    email: str | None = Field(None, description="The email")


class ComplexModel(BaseModel):
    """A more complex model for testing."""

    id: str = Field(..., description="The ID")
    name: str = Field(..., description="The name")
    description: str | None = Field(None, description="The description")
    tags: list[str] = Field(default_factory=list, description="Tags")
    items: list[SimpleModel] = Field(default_factory=list, description="Items")
    metadata: dict = Field(default_factory=dict, description="Metadata")


def test_schema_generator_basic():
    """Test basic functionality of OpenAPISchemaGenerator."""
    # Create a schema generator
    generator = OpenAPISchemaGenerator(title="Test API", version="1.0.0", description="Test API Description")

    # Generate schema
    schema = generator.generate_schema()

    # Check that the schema was generated correctly
    assert schema["openapi"] == "3.1.0"  # Updated to 3.1.0
    assert schema["info"]["title"] == "Test API"
    assert schema["info"]["version"] == "1.0.0"
    assert schema["info"]["description"] == "Test API Description"
    assert "paths" in schema
    assert "components" in schema
    assert "schemas" in schema["components"]


def test_schema_generator_register_models():
    """Test registering models with OpenAPISchemaGenerator."""
    # Create a schema generator
    generator = OpenAPISchemaGenerator(title="Test API", version="1.0.0", description="Test API Description")

    # Test 1: Register models explicitly
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

    # Test 2: Check that registering the same model twice doesn't cause issues
    # Create a new generator
    generator2 = OpenAPISchemaGenerator(title="Test API", version="1.0.0", description="Test API Description")
    generator2._register_model(SimpleModel)
    generator2._register_model(SimpleModel)  # Register twice
    schema2 = generator2.generate_schema()
    assert "SimpleModel" in schema2["components"]["schemas"]

    # Test 3: Check that nested models are automatically registered
    # Create a new generator
    generator3 = OpenAPISchemaGenerator(title="Test API", version="1.0.0", description="Test API Description")
    # Register only ComplexModel (which references SimpleModel)
    generator3._register_model(ComplexModel)
    schema3 = generator3.generate_schema()

    # Check that both models were registered correctly
    assert "SimpleModel" in schema3["components"]["schemas"]
    assert "ComplexModel" in schema3["components"]["schemas"]

    # Check that the reference is correct
    complex_schema = schema3["components"]["schemas"]["ComplexModel"]
    items_schema = complex_schema["properties"]["items"]
    assert items_schema["type"] == "array"
    assert "items" in items_schema
    assert "$ref" in items_schema["items"]
    assert items_schema["items"]["$ref"] == "#/components/schemas/SimpleModel"
