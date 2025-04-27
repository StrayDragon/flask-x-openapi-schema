"""Tests for the decorator_factory module.

This module tests the decorator factory pattern implementation.
"""

from __future__ import annotations

import pytest
from pydantic import BaseModel, Field

from flask_x_openapi_schema.core.config import ConventionalPrefixConfig
from flask_x_openapi_schema.core.decorator_factory import (
    FlaskOpenAPIDecoratorFactory,
    FlaskRestfulOpenAPIDecoratorFactory,
    create_decorator_factory,
)
from flask_x_openapi_schema.i18n.i18n_string import I18nStr


# Define test models
class SampleRequestModel(BaseModel):
    """Test request model."""

    name: str = Field(..., description="The name")
    age: int = Field(..., description="The age")


def test_create_decorator_factory():
    """Test create_decorator_factory function."""
    # Test with Flask
    factory = create_decorator_factory("flask")
    assert isinstance(factory, FlaskOpenAPIDecoratorFactory)

    # Test with Flask-RESTful
    factory = create_decorator_factory("flask_restful")
    assert isinstance(factory, FlaskRestfulOpenAPIDecoratorFactory)

    # Test with unsupported framework
    with pytest.raises(ValueError, match="Unsupported framework: unsupported"):
        create_decorator_factory("unsupported")


def test_flask_decorator_factory():
    """Test FlaskOpenAPIDecoratorFactory."""
    factory = FlaskOpenAPIDecoratorFactory()

    # Create a decorator
    decorator = factory.create_decorator(
        summary="Test API",
        description="Test description",
        tags=["test"],
        operation_id="testOperation",
        deprecated=True,
    )

    # Apply the decorator to a function
    @decorator
    def example_function(_x_body: SampleRequestModel):
        return {"message": "Hello, world!"}

    # Check that metadata was attached to the function
    assert hasattr(example_function, "_openapi_metadata")
    metadata = example_function._openapi_metadata

    # Check metadata values
    assert metadata["summary"] == "Test API"
    assert metadata["description"] == "Test description"
    assert metadata["tags"] == ["test"]
    assert metadata["operationId"] == "testOperation"
    assert metadata["deprecated"] is True


def test_flask_restful_decorator_factory():
    """Test FlaskRestfulOpenAPIDecoratorFactory."""
    factory = FlaskRestfulOpenAPIDecoratorFactory()

    # Create a decorator
    decorator = factory.create_decorator(
        summary="Test API",
        description="Test description",
        tags=["test"],
        operation_id="testOperation",
        deprecated=True,
    )

    # Apply the decorator to a function
    @decorator
    def example_function(_x_body: SampleRequestModel):
        return {"message": "Hello, world!"}

    # Check that metadata was attached to the function
    assert hasattr(example_function, "_openapi_metadata")
    metadata = example_function._openapi_metadata

    # Check metadata values
    assert metadata["summary"] == "Test API"
    assert metadata["description"] == "Test description"
    assert metadata["tags"] == ["test"]
    assert metadata["operationId"] == "testOperation"
    assert metadata["deprecated"] is True


def test_decorator_factory_with_i18n():
    """Test decorator factory with I18nStr objects."""
    factory = create_decorator_factory("flask")

    # Create I18nStr objects
    summary = I18nStr({"en": "Test API", "zh": "测试 API"})
    description = I18nStr({"en": "Test description", "zh": "测试描述"})

    # Create a decorator with English language
    decorator = factory.create_decorator(
        summary=summary,
        description=description,
        tags=["test"],
        language="en",
    )

    # Apply the decorator to a function
    @decorator
    def test_function():
        return {"message": "Hello, world!"}

    # Check metadata in English
    metadata = test_function._openapi_metadata
    assert metadata["summary"] == "Test API"
    assert metadata["description"] == "Test description"

    # Create a decorator with Chinese language
    decorator = factory.create_decorator(
        summary=summary,
        description=description,
        tags=["test"],
        language="zh",
    )

    # Apply the decorator to another function
    @decorator
    def test_function_zh():
        return {"message": "你好，世界！"}

    # Check metadata in Chinese
    metadata = test_function_zh._openapi_metadata
    assert metadata["summary"] == "测试 API"
    assert metadata["description"] == "测试描述"


def test_decorator_factory_with_custom_prefixes():
    """Test decorator factory with custom prefixes."""
    factory = create_decorator_factory("flask")

    # Create custom prefix config
    custom_config = ConventionalPrefixConfig(
        request_body_prefix="custom_body",
        request_query_prefix="custom_query",
        request_path_prefix="custom_path",
        request_file_prefix="custom_file",
    )

    # Create a decorator with custom prefixes
    decorator = factory.create_decorator(
        summary="Test API",
        description="Test description",
        prefix_config=custom_config,
    )

    # Apply the decorator to a function with custom prefixes
    @decorator
    def test_function(custom_body: SampleRequestModel, custom_path_id: str):
        return {"message": "Hello, world!"}

    # Check that metadata was attached to the function
    assert hasattr(test_function, "_openapi_metadata")
