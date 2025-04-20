"""
Tests for the i18n_model module.

This module tests the I18nBaseModel class for internationalization support.
"""

import json
from pydantic import Field, ConfigDict
from typing import Optional, List

from flask_x_openapi_schema.i18n.i18n_model import I18nBaseModel
from flask_x_openapi_schema.i18n.i18n_string import I18nStr, set_current_language


# Define a test model that uses I18nBaseModel
class ProductModel(I18nBaseModel):
    """Test model for a product with internationalized fields."""

    id: str = Field(..., description="The product ID")
    name: I18nStr = Field(..., description="The product name")
    description: Optional[I18nStr] = Field(None, description="The product description")
    price: float = Field(..., description="The product price")
    tags: List[str] = Field(default_factory=list, description="Product tags")

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
        description=I18nStr(
            {"en-US": "This is a test product", "zh-Hans": "这是一个测试产品"}
        ),
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
        description=I18nStr(
            {"en-US": "This is a test product", "zh-Hans": "这是一个测试产品"}
        ),
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
        description=I18nStr(
            {"en-US": "This is a test product", "zh-Hans": "这是一个测试产品"}
        ),
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
