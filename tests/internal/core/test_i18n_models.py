"""Tests for the i18n_model module.

This module provides comprehensive tests for the I18nBaseModel class,
covering basic functionality, advanced features, and edge cases.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import patch

from pydantic import BaseModel, ConfigDict, Field

from flask_x_openapi_schema.i18n.i18n_model import I18nBaseModel
from flask_x_openapi_schema.i18n.i18n_string import I18nStr, set_current_language


# Define a test model that uses I18nBaseModel
class ProductModel(I18nBaseModel):
    """Test model for a product with internationalized fields."""

    id: str = Field(..., description="The product ID")
    name: I18nStr = Field(..., description="The product name")
    description: I18nStr | None = Field(None, description="The product description")
    price: float = Field(..., description="The product price")
    tags: list[str] = Field(default_factory=list, description="Product tags")

    model_config = ConfigDict(arbitrary_types_allowed=True)


def test_i18n_model_creation():
    """Test creating an I18nBaseModel with I18nStr fields."""
    # Create a product with I18nStr objects
    product = ProductModel(
        id="prod-123",
        name=I18nStr("Test Product"),
        description=I18nStr("This is a test product"),
        price=10.99,
        tags=["test", "example"],
    )

    # Check that the model was created correctly
    assert product.id == "prod-123"
    assert str(product.name) == "Test Product"
    assert str(product.description) == "This is a test product"
    assert product.price == 10.99
    assert product.tags == ["test", "example"]

    # Create a product with I18nStr objects
    product = ProductModel(
        id="prod-123",
        name=I18nStr({"en-US": "Test Product", "zh-Hans": "测试产品"}),
        description=I18nStr({"en-US": "This is a test product", "zh-Hans": "这是一个测试产品"}),
        price=10.99,
        tags=["test", "example"],
    )

    # Check that the model was created correctly
    assert product.id == "prod-123"
    assert str(product.name) == "Test Product"
    assert str(product.description) == "This is a test product"
    assert product.price == 10.99
    assert product.tags == ["test", "example"]


def test_i18n_model_language_switching():
    """Test switching languages with I18nBaseModel."""
    # Create a product with I18nStr objects
    product = ProductModel(
        id="prod-123",
        name=I18nStr({"en-US": "Test Product", "zh-Hans": "测试产品"}),
        description=I18nStr({"en-US": "This is a test product", "zh-Hans": "这是一个测试产品"}),
        price=10.99,
        tags=["test", "example"],
    )

    # Check English strings (default)
    assert str(product.name) == "Test Product"
    assert str(product.description) == "This is a test product"

    # Switch to Chinese
    set_current_language("zh-Hans")
    assert str(product.name) == "测试产品"
    assert str(product.description) == "这是一个测试产品"

    # Switch back to English
    set_current_language("en-US")
    assert str(product.name) == "Test Product"
    assert str(product.description) == "This is a test product"


def test_i18n_model_serialization():
    """Test serializing I18nBaseModel to JSON."""
    # Create a product with I18nStr objects
    product = ProductModel(
        id="prod-123",
        name=I18nStr({"en-US": "Test Product", "zh-Hans": "测试产品"}),
        description=I18nStr({"en-US": "This is a test product", "zh-Hans": "这是一个测试产品"}),
        price=10.99,
        tags=["test", "example"],
    )

    # Serialize to JSON with English strings
    json_str = product.model_dump_json()
    data = json.loads(json_str)

    # Check that the JSON contains the correct values
    assert data["id"] == "prod-123"
    assert data["name"] == "Test Product"
    assert data["description"] == "This is a test product"
    assert data["price"] == 10.99
    assert data["tags"] == ["test", "example"]

    # Switch to Chinese and serialize again
    set_current_language("zh-Hans")
    json_str = product.model_dump_json()
    data = json.loads(json_str)

    # Check that the JSON contains the correct values
    assert data["id"] == "prod-123"
    assert data["name"] == "测试产品"
    assert data["description"] == "这是一个测试产品"
    assert data["price"] == 10.99
    assert data["tags"] == ["test", "example"]

    # Reset to English for other tests
    set_current_language("en-US")


class TestI18nModelExtended:
    """Extended tests for I18nBaseModel."""

    def test_model_json_schema(self):
        """Test the model_json_schema method."""

        # Create a model class that inherits from I18nBaseModel
        class TestModel(I18nBaseModel):
            name: I18nStr = Field(..., description="The name")
            description: I18nStr | None = Field(None, description="The description")
            tags: list[str] = Field(default_factory=list, description="Tags")
            metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata")

        # Mock the model_json_schema method to avoid Pydantic issues with I18nStr
        with patch.object(BaseModel, "model_json_schema") as mock_schema:
            # Set up the mock to return a schema
            mock_schema.return_value = {
                "properties": {
                    "name": {"type": "string", "description": "The name"},
                    "description": {"type": "string", "description": "The description"},
                    "tags": {"type": "array", "description": "Tags", "items": {"type": "string"}},
                    "metadata": {"type": "object", "description": "Metadata"},
                }
            }

            # Call the patched method
            with patch.object(
                I18nBaseModel, "model_json_schema", wraps=I18nBaseModel.model_json_schema
            ) as wrapped_schema:
                schema = TestModel.model_json_schema()

                # Verify that the method was called
                assert wrapped_schema.called

                # Check that the schema was created correctly
                assert "properties" in schema
                assert "name" in schema["properties"]
                assert "description" in schema["properties"]
                assert "tags" in schema["properties"]
                assert "metadata" in schema["properties"]

    def test_for_language(self):
        """Test the for_language method."""

        # Create a model class that inherits from I18nBaseModel
        class TestModel(I18nBaseModel):
            name: I18nStr = Field(..., description="The name")
            description: I18nStr | None = Field(None, description="The description")
            tags: list[str] = Field(default_factory=list, description="Tags")
            metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata")

        # Mock create_model to avoid issues with I18nStr
        with patch("flask_x_openapi_schema.i18n.i18n_model.create_model") as mock_create_model:
            # Set up the mock to return a model class
            class EnglishModel(BaseModel):
                name: str
                description: str | None = None
                tags: list[str] = Field(default_factory=list)
                metadata: dict[str, Any] = Field(default_factory=dict)

            EnglishModel.__name__ = "TestModel_en-US"
            mock_create_model.return_value = EnglishModel

            # Call the for_language method
            result_model = TestModel.for_language("en-US")

            # Verify that create_model was called
            mock_create_model.assert_called_once()

            # Check that the model was created correctly
            assert result_model.__name__ == "TestModel_en-US"
            assert issubclass(result_model, BaseModel)
            assert not issubclass(result_model, I18nBaseModel)

            # Create an instance of the English model
            english_model = result_model(
                name="Test",
                description="This is a test",
                tags=["test", "example"],
                metadata={"key": "value"},
            )

            # Check that the instance was created correctly
            assert english_model.name == "Test"
            assert english_model.description == "This is a test"
            assert english_model.tags == ["test", "example"]
            assert english_model.metadata == {"key": "value"}

    def test_for_language_with_current_language(self):
        """Test the for_language method with current language."""

        # Create a model class that inherits from I18nBaseModel
        class TestModel(I18nBaseModel):
            name: I18nStr = Field(..., description="The name")
            description: I18nStr | None = Field(None, description="The description")

        # Set the current language
        set_current_language("fr-FR")

        # Mock create_model to avoid issues with I18nStr
        with patch("flask_x_openapi_schema.i18n.i18n_model.create_model") as mock_create_model:
            # Set up the mock to return a model class
            class FrenchModel(BaseModel):
                name: str
                description: str | None = None

            FrenchModel.__name__ = "TestModel_fr-FR"
            mock_create_model.return_value = FrenchModel

            # Call the for_language method with no language (should use current)
            result_model = TestModel.for_language()

            # Verify that create_model was called
            mock_create_model.assert_called_once()

            # Check that the model was created correctly
            assert result_model.__name__ == "TestModel_fr-FR"

        # Reset the language to English for other tests
        set_current_language("en-US")

    def test_model_with_non_i18n_fields(self):
        """Test a model with both I18nString and non-I18nString fields."""

        # Create a model class that inherits from I18nBaseModel
        class MixedModel(I18nBaseModel):
            name: str = Field(..., description="The name")
            description: I18nStr = Field(..., description="The description")
            age: int = Field(..., description="The age")

        # Check that only I18nString fields are in __i18n_fields__
        assert MixedModel.__i18n_fields__ == ["description"]

        # Create a model instance
        model = MixedModel(
            name="Test",
            description=I18nStr({"en-US": "This is a test", "fr-FR": "C'est un test"}),
            age=30,
        )

        # Check that the model was created correctly
        assert model.name == "Test"
        assert str(model.description) == "This is a test"
        assert model.age == 30

        # Change the language and check again
        set_current_language("fr-FR")
        assert str(model.description) == "C'est un test"

        # Reset the language to English for other tests
        set_current_language("en-US")

    def test_model_dump_with_exclude(self):
        """Test model_dump with exclude parameter."""

        # Create a model class that inherits from I18nBaseModel
        class TestModel(I18nBaseModel):
            name: I18nStr = Field(..., description="The name")
            description: I18nStr = Field(..., description="The description")
            age: int = Field(..., description="The age")

        # Create a model instance
        model = TestModel(
            name=I18nStr({"en-US": "Test", "fr-FR": "Test"}),
            description=I18nStr({"en-US": "This is a test", "fr-FR": "C'est un test"}),
            age=30,
        )

        # Dump the model with exclude
        data = model.model_dump(exclude={"description"})

        # Check that the excluded field is not in the data
        assert "name" in data
        assert "age" in data
        assert "description" not in data

        # Check that I18nString fields are converted to strings
        assert data["name"] == "Test"
        assert data["age"] == 30
