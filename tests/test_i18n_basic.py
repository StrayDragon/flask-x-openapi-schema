"""
Basic tests for the internationalization (i18n) features of flask-x-openapi-schema.

This module tests the i18n functionality of the library without using the openapi_metadata decorator.
"""

import pytest

from flask_x_openapi_schema import (
    I18nStr,
    get_current_language,
    set_current_language,
)


# We'll use a simple class instead of Pydantic model due to compatibility issues
class ProductI18n:
    """Model for a product with internationalized fields."""

    def __init__(self, id, name, description, category):
        self.id = id
        self.name = name
        self.description = description
        self.category = category

    def for_language(self, language):
        """Create a language-specific version of this model."""
        return ProductI18n(
            id=self.id,
            name=self.name,
            description=self.description.get(language),
            category=self.category.get(language),
        )


@pytest.fixture(autouse=True)
def reset_language():
    """Reset language to English before each test."""
    set_current_language("en-US")
    yield
    # Reset back to English after the test
    set_current_language("en-US")


def test_i18n_string():
    """Test the I18nString class."""
    # Create an I18nString
    i18n_text = I18nStr(
        {
            "en-US": "Hello",
            "zh-Hans": "你好",
            "ja-JP": "こんにちは",
        }
    )

    # Test default language (English)
    assert str(i18n_text) == "Hello"
    assert i18n_text.get("en-US") == "Hello"

    # Test switching languages
    set_current_language("zh-Hans")
    assert str(i18n_text) == "你好"
    assert i18n_text.get("zh-Hans") == "你好"

    set_current_language("ja-JP")
    assert str(i18n_text) == "こんにちは"
    assert i18n_text.get("ja-JP") == "こんにちは"

    # Test fallback to default language
    set_current_language("fr-FR")  # Not defined
    assert str(i18n_text) == "Hello"  # Should fall back to default

    # Test direct access with get()
    assert i18n_text.get("zh-Hans") == "你好"
    assert i18n_text.get("ja-JP") == "こんにちは"
    assert i18n_text.get("fr-FR") == "Hello"  # Should fall back to default


def test_i18n_model():
    """Test a simple model with I18nString fields."""
    # Create a model with internationalized fields
    product = ProductI18n(
        id="prod-1",
        name="Example Product",
        description=I18nStr(
            {
                "en-US": "This is an example product with internationalized description",
                "zh-Hans": "这是一个具有国际化描述的示例产品",
                "ja-JP": "これは国際化された説明を持つサンプル製品です",
            }
        ),
        category=I18nStr(
            {
                "en-US": "Examples",
                "zh-Hans": "示例",
                "ja-JP": "例",
            }
        ),
    )

    # Test English
    set_current_language("en-US")
    assert (
        str(product.description)
        == "This is an example product with internationalized description"
    )
    assert str(product.category) == "Examples"

    # Test Chinese
    set_current_language("zh-Hans")
    assert str(product.description) == "这是一个具有国际化描述的示例产品"
    assert str(product.category) == "示例"

    # Test Japanese
    set_current_language("ja-JP")
    assert str(product.description) == "これは国際化された説明を持つサンプル製品です"
    assert str(product.category) == "例"

    # Test language-specific model
    set_current_language("zh-Hans")
    zh_model = product.for_language("zh-Hans")
    assert zh_model.description == "这是一个具有国际化描述的示例产品"
    assert zh_model.category == "示例"

    # Test that the original model is not modified
    set_current_language("en-US")
    assert (
        str(product.description)
        == "This is an example product with internationalized description"
    )


def test_current_language():
    """Test the get_current_language and set_current_language functions."""
    # Set a language first
    set_current_language("en-US")
    assert get_current_language() == "en-US"

    # Test setting and getting language
    set_current_language("zh-Hans")
    assert get_current_language() == "zh-Hans"

    set_current_language("ja-JP")
    assert get_current_language() == "ja-JP"
