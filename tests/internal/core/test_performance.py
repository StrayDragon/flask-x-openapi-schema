"""Performance tests for flask-x-openapi-schema.

This module tests the performance of the library.
"""

from __future__ import annotations

import time

import pytest
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


@pytest.mark.serial
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


@pytest.mark.serial
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
    assert schema["openapi"] == "3.1.0"  # Updated to 3.1.0
    assert schema["info"]["title"] == "Test API"
    assert schema["info"]["version"] == "1.0.0"
    assert schema["info"]["description"] == "Test API Description"
    assert "components" in schema
    assert "schemas" in schema["components"]
    assert "SimpleModel" in schema["components"]["schemas"]
    assert "ComplexModel" in schema["components"]["schemas"]

    # Print performance results
    print(f"Schema generation: {generation_time:.6f} seconds for 100 iterations")


@pytest.mark.serial
def test_i18n_processing_performance():
    """Test the performance of I18nStr processing functions."""
    from flask_x_openapi_schema.core.utils import process_i18n_value
    from flask_x_openapi_schema.i18n.i18n_string import I18nStr, set_current_language

    # Set up test data
    i18n_str = I18nStr({"en-US": "Hello", "zh-Hans": "你好", "ja-JP": "こんにちは"})

    # Test process_i18n_value performance
    set_current_language("en-US")
    start_time = time.time()
    for _ in range(10000):
        process_i18n_value(i18n_str, "en-US")
    value_time_en = time.time() - start_time

    # Test with different language
    set_current_language("zh-Hans")
    start_time = time.time()
    for _ in range(10000):
        process_i18n_value(i18n_str, "zh-Hans")
    value_time_zh = time.time() - start_time

    # Print performance results
    print(f"I18nStr value processing (en-US): {value_time_en:.6f} seconds for 10000 iterations")
    print(f"I18nStr value processing (zh-Hans): {value_time_zh:.6f} seconds for 10000 iterations")

    # Verify results
    assert process_i18n_value(i18n_str, "en-US") == "Hello"
    assert process_i18n_value(i18n_str, "zh-Hans") == "你好"


@pytest.mark.serial
def test_references_cache_performance():
    """Test the performance of _fix_references function with caching."""
    from flask_x_openapi_schema.core.utils import _fix_references, clear_references_cache

    # Create a complex nested schema with references
    test_schema = {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "name": {"type": "string"},
            "items": {
                "type": "array",
                "items": {"$ref": "#/$defs/Item"},
            },
            "metadata": {
                "type": "object",
                "properties": {
                    "created": {"type": "string", "format": "date-time"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "required": ["id", "name"],
        "$defs": {
            "Item": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "quantity": {"type": "integer"},
                },
            },
        },
    }

    # Clear cache before testing
    clear_references_cache()

    # First run (cold cache)
    start_time = time.time()
    for _ in range(1000):
        result = _fix_references(test_schema)
    cold_time = time.time() - start_time

    # Second run (warm cache)
    start_time = time.time()
    for _ in range(1000):
        result = _fix_references(test_schema)
    warm_time = time.time() - start_time

    # Print performance results
    print(f"_fix_references cold cache: {cold_time:.6f} seconds for 1000 iterations")
    print(f"_fix_references warm cache: {warm_time:.6f} seconds for 1000 iterations")
    print(f"Cache speedup factor: {cold_time / warm_time:.2f}x")

    # Verify the result
    assert result["properties"]["items"]["items"]["$ref"] == "#/components/schemas/Item"
