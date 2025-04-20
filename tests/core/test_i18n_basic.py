"""
Basic tests for the i18n features of flask-x-openapi-schema.

This module tests the internationalization functionality of the library.
"""

from flask_x_openapi_schema.i18n.i18n_string import (
    I18nStr,
    set_current_language,
    get_current_language,
)


def test_i18n_string_basic():
    """Test basic functionality of I18nStr."""
    # Create an I18nStr with a single language
    i18n_str = I18nStr("Hello, world!")

    # Check that the string is stored correctly
    assert i18n_str.get() == "Hello, world!"
    assert str(i18n_str) == "Hello, world!"

    # Create an I18nStr with multiple languages
    i18n_str = I18nStr({"en-US": "Hello, world!", "zh-Hans": "你好，世界！"})

    # Check that the strings are stored correctly
    assert i18n_str.get("en-US") == "Hello, world!"
    assert i18n_str.get("zh-Hans") == "你好，世界！"

    # Check that the default language is used when no language is specified
    assert i18n_str.get() == "Hello, world!"


def test_i18n_string_current_language():
    """Test I18nStr with current language."""
    # Create an I18nStr with multiple languages
    i18n_str = I18nStr({"en-US": "Hello, world!", "zh-Hans": "你好，世界！"})

    # Check the default language
    assert get_current_language() == "en-US"
    assert str(i18n_str) == "Hello, world!"

    # Change the current language
    set_current_language("zh-Hans")
    assert get_current_language() == "zh-Hans"
    assert str(i18n_str) == "你好，世界！"

    # Reset the language to English for other tests
    set_current_language("en-US")


def test_i18n_string_fallback():
    """Test I18nStr fallback behavior."""
    # Create an I18nStr with multiple languages
    i18n_str = I18nStr({"en-US": "Hello, world!", "zh-Hans": "你好，世界！"})

    # Check that the default language is used when an unknown language is specified
    assert i18n_str.get("fr-FR") == "Hello, world!"

    # Create an I18nStr with a different default language
    i18n_str = I18nStr(
        {"en-US": "Hello, world!", "zh-Hans": "你好，世界！"},
        default_language="zh-Hans",
    )

    # Check that the new default language is used when an unknown language is specified
    assert i18n_str.get("fr-FR") == "你好，世界！"


def test_i18n_string_serialization():
    """Test I18nStr serialization."""
    # Create an I18nStr with multiple languages
    i18n_str = I18nStr({"en-US": "Hello, world!", "zh-Hans": "你好，世界！"})

    # Check that the string can be serialized to JSON
    import json

    serialized = json.dumps({"message": str(i18n_str)})
    deserialized = json.loads(serialized)

    assert deserialized["message"] == "Hello, world!"

    # Change the current language and check serialization again
    set_current_language("zh-Hans")
    serialized = json.dumps({"message": str(i18n_str)})
    deserialized = json.loads(serialized)

    assert deserialized["message"] == "你好，世界！"

    # Reset the language to English for other tests
    set_current_language("en-US")
