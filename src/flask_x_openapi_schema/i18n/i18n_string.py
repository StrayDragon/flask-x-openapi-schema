"""
Internationalization support for strings in OpenAPI metadata.
"""

import contextvars
from typing import Any, ClassVar, Optional, Union

from pydantic_core import CoreSchema, core_schema

# Thread-local storage for current language
_current_language = contextvars.ContextVar[str]("current_language", default="en-US")


def get_current_language() -> str:
    """
    Get the current language for the current thread.

    Returns:
        The current language code (e.g., "en-US", "zh-Hans")
    """
    return _current_language.get()


def set_current_language(language: str) -> None:
    """
    Set the current language for the current thread.

    Args:
        language: The language code to set (e.g., "en-US", "zh-Hans")
    """
    _current_language.set(language)


class I18nStr:
    """
    A string class that supports internationalization.

    This class allows you to define strings in multiple languages and automatically
    returns the appropriate string based on the current language setting.

    Example:
        ```python
        # Create an I18nString with multiple language versions
        greeting = I18nString({
            "en-US": "Hello",
            "zh-Hans": "你好",
            "ja-JP": "こんにちは"
        })

        # Get the string in the current language
        print(str(greeting))  # Outputs the greeting in the current language

        # Get the string in a specific language
        print(greeting.get("zh-Hans"))  # Outputs "你好"
        ```
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: Any
    ) -> CoreSchema:
        """Generate a pydantic core schema for I18nString."""
        return core_schema.is_instance_schema(cls)

    # Default supported languages
    SUPPORTED_LANGUAGES: ClassVar[list[str]] = [
        "en-US",
        "zh-Hans",
        "zh-Hant",
        "pt-BR",
        "es-ES",
        "fr-FR",
        "de-DE",
        "ja-JP",
        "ko-KR",
        "ru-RU",
        "it-IT",
        "uk-UA",
        "vi-VN",
        "ro-RO",
        "pl-PL",
        "hi-IN",
        "tr-TR",
        "fa-IR",
        "sl-SI",
        "th-TH",
    ]

    def __init__(
        self,
        strings: Union[dict[str, str], str],
        default_language: str = "en-US",
    ):
        """
        Initialize an I18nString.

        Args:
            strings: Either a dictionary mapping language codes to strings,
                    or a single string (which will be used for all languages)
            default_language: The default language to use if the requested language is not available
        """
        self.default_language = default_language

        if isinstance(strings, str):
            # If a single string is provided, use it for all languages
            self.strings = dict.fromkeys(self.SUPPORTED_LANGUAGES, strings)
            # Ensure default language is set
            self.strings[self.default_language] = strings
        else:
            # Use the provided dictionary
            self.strings = strings

            # Ensure default language is set
            if self.default_language not in self.strings:
                # If default language is not provided, use the first available language
                if self.strings:
                    self.strings[self.default_language] = next(
                        iter(self.strings.values())
                    )
                else:
                    self.strings[self.default_language] = ""

    def get(self, language: Optional[str] = None) -> str:
        """
        Get the string in the specified language.

        Args:
            language: The language code to get the string for.
                     If None, uses the current language.

        Returns:
            The string in the requested language, or the default language if not available
        """
        if language is None:
            language = get_current_language()

        # Try to get the string in the requested language
        if language in self.strings:
            return self.strings[language]

        # Fall back to default language
        return self.strings[self.default_language]

    def __str__(self) -> str:
        """
        Get the string in the current language.

        Returns:
            The string in the current language
        """
        return self.get()

    def __repr__(self) -> str:
        """
        Get a string representation of the I18nString.

        Returns:
            A string representation of the I18nString
        """
        return f"I18nString({self.strings})"

    def __eq__(self, other: Any) -> bool:
        """
        Compare this I18nString with another object.

        Args:
            other: The object to compare with

        Returns:
            True if the objects are equal, False otherwise
        """
        if isinstance(other, I18nStr):
            return self.strings == other.strings
        elif isinstance(other, str):
            return str(self) == other
        return False

    @classmethod
    def create(cls, **kwargs) -> "I18nStr":
        """
        Create an I18nString from keyword arguments.

        This is a convenience method for creating an I18nString with named language parameters.

        Example:
            ```python
            greeting = I18nString.create(
                en_US="Hello",
                zh_Hans="你好",
                ja_JP="こんにちは"
            )
            ```

        Args:
            **kwargs: Keyword arguments where the keys are language codes (with underscores
                     instead of hyphens) and the values are the strings in those languages

        Returns:
            An I18nString instance
        """
        # Convert keys from snake_case to kebab-case (e.g., en_US -> en-US)
        strings = {k.replace("_", "-"): v for k, v in kwargs.items()}
        return cls(strings)
