"""
Tests for the i18n_string module to improve coverage.
"""

from flask_x_openapi_schema.i18n.i18n_string import (
    I18nStr,
    set_current_language,
)


class TestI18nStringCoverage:
    """Tests for i18n_string to improve coverage."""

    def test_create_class_method(self):
        """Test the create class method."""
        # Create an I18nString using the create method
        i18n_str = I18nStr.create(en_US="Hello", zh_Hans="你好", ja_JP="こんにちは")

        # Check that the string was created correctly
        assert i18n_str.strings == {
            "en-US": "Hello",
            "zh-Hans": "你好",
            "ja-JP": "こんにちは",
        }

        # Check that the string can be accessed in different languages
        assert i18n_str.get("en-US") == "Hello"
        assert i18n_str.get("zh-Hans") == "你好"
        assert i18n_str.get("ja-JP") == "こんにちは"

    def test_eq_with_different_types(self):
        """Test the __eq__ method with different types."""
        # Create an I18nString
        i18n_str = I18nStr({"en-US": "Hello", "zh-Hans": "你好"})

        # Test equality with another I18nString
        other_str = I18nStr({"en-US": "Hello", "zh-Hans": "你好"})
        assert i18n_str == other_str

        # Test equality with a string
        set_current_language("en-US")
        assert i18n_str == "Hello"

        set_current_language("zh-Hans")
        assert i18n_str == "你好"

        # Test equality with other types
        assert i18n_str != 123
        assert i18n_str != ["Hello"]
        assert i18n_str != {"en-US": "Hello"}

        # Reset to English for other tests
        set_current_language("en-US")

    def test_language_fallback_complex(self):
        """Test complex language fallback scenarios."""
        # Create an I18nString with multiple languages
        i18n_str = I18nStr(
            {
                "en-US": "Hello",
                "en-GB": "Hello (UK)",
                "zh-Hans": "你好",
                "zh-Hant": "你好 (Traditional)",
                "fr-FR": "Bonjour",
            }
        )

        # Test with exact language matches
        assert i18n_str.get("en-US") == "Hello"
        assert i18n_str.get("zh-Hans") == "你好"
        assert i18n_str.get("fr-FR") == "Bonjour"

        # Test with languages that don't exist (should fall back to default)
        assert i18n_str.get("de-DE") == "Hello"  # Falls back to default (en-US)
        assert i18n_str.get("ja-JP") == "Hello"  # Falls back to default (en-US)

        # Test with a different default language
        i18n_str = I18nStr(
            {"en-US": "Hello", "zh-Hans": "你好", "fr-FR": "Bonjour"},
            default_language="fr-FR",
        )

        assert i18n_str.get("de-DE") == "Bonjour"  # Falls back to default (fr-FR)

        # Test with empty strings dictionary
        i18n_str = I18nStr({})
        assert i18n_str.get("en-US") == ""  # Empty default

        # Test with a single string and no default language
        i18n_str = I18nStr("Hello")
        assert i18n_str.get("en-US") == "Hello"
        assert i18n_str.get("zh-Hans") == "Hello"  # Falls back to default (en-US)

    def test_init_with_empty_dict(self):
        """Test initializing I18nString with an empty dictionary."""
        # Create an I18nString with an empty dictionary
        i18n_str = I18nStr({})

        # Check that the default language was set with an empty string
        assert i18n_str.strings["en-US"] == ""
        assert i18n_str.get() == ""

        # Create an I18nString with a non-empty dictionary but missing default language
        i18n_str = I18nStr({"zh-Hans": "你好"})

        # Check that the default language was set with the first available language
        assert i18n_str.strings["en-US"] == "你好"
        assert i18n_str.get() == "你好"
