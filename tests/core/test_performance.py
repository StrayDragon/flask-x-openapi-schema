"""Performance tests for flask-x-openapi-schema.

This module tests the performance of the library.
"""

from __future__ import annotations

import time

from pydantic import BaseModel, Field

from flask_x_openapi_schema.core.schema_generator import OpenAPISchemaGenerator
from flask_x_openapi_schema.core.utils import pydantic_to_openapi_schema


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


def test_pydantic_to_openapi_schema_performance():
    """Test the performance of pydantic_to_openapi_schema."""
    # Simple model
    start_time = time.time()
    for _ in range(1000):
        schema = pydantic_to_openapi_schema(SimpleModel)
    simple_time = time.time() - start_time

    # Check that the schema was generated correctly
    assert schema["type"] == "object"
    assert "properties" in schema
    assert "name" in schema["properties"]
    assert "age" in schema["properties"]
    assert "email" in schema["properties"]

    # Complex model
    start_time = time.time()
    for _ in range(1000):
        schema = pydantic_to_openapi_schema(ComplexModel)
    complex_time = time.time() - start_time

    # Check that the schema was generated correctly
    assert schema["type"] == "object"
    assert "properties" in schema
    assert "id" in schema["properties"]
    assert "name" in schema["properties"]
    assert "description" in schema["properties"]
    assert "tags" in schema["properties"]
    assert "items" in schema["properties"]
    assert "metadata" in schema["properties"]

    # Print performance results
    print(f"Simple model: {simple_time:.6f} seconds for 1000 iterations")
    print(f"Complex model: {complex_time:.6f} seconds for 1000 iterations")


def test_schema_generator_performance():
    """Test the performance of OpenAPISchemaGenerator."""
    # Create a schema generator
    generator = OpenAPISchemaGenerator(title="Test API", version="1.0.0", description="Test API Description")

    # Register models
    generator._register_model(SimpleModel)
    generator._register_model(ComplexModel)

    # Generate schema
    start_time = time.time()
    for _ in range(100):
        schema = generator.generate_schema()
    generation_time = time.time() - start_time

    # Check that the schema was generated correctly
    assert schema["openapi"] == "3.0.3"
    assert schema["info"]["title"] == "Test API"
    assert schema["info"]["version"] == "1.0.0"
    assert schema["info"]["description"] == "Test API Description"
    assert "components" in schema
    assert "schemas" in schema["components"]
    assert "SimpleModel" in schema["components"]["schemas"]
    assert "ComplexModel" in schema["components"]["schemas"]

    # Print performance results
    print(f"Schema generation: {generation_time:.6f} seconds for 100 iterations")
