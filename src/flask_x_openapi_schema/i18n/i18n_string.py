"""Internationalization support for strings in OpenAPI metadata.

This module provides functionality for internationalization (i18n) of strings
used in OpenAPI metadata. It includes utilities for setting and retrieving the
current language, as well as a class for creating internationalized strings that
automatically display in the appropriate language based on context.
"""

import contextvars
from typing import Any, ClassVar

from pydantic_core import CoreSchema, core_schema

_current_language = contextvars.ContextVar[str]("current_language", default="en-US")


def get_current_language() -> str:
    """Get the current language for the current thread.

    This function returns the language code that is currently set for the current thread.
    The language code is used for internationalization of strings in the OpenAPI schema.

    Returns:
        str: The current language code (e.g., "en-US", "zh-Hans")

    Examples:
        >>> from flask_x_openapi_schema import get_current_language
        >>> get_current_language()
        'en-US'

    """
    return _current_language.get()


def set_current_language(language: str) -> None:
    """Set the current language for the current thread.

    This function sets the language code for the current thread. This affects how
    internationalized strings are displayed in the OpenAPI schema and in responses.

    Args:
        language: The language code to set (e.g., "en-US", "zh-Hans")

    Examples:
        >>> from flask_x_openapi_schema import set_current_language
        >>> set_current_language("zh-Hans")

    """
    _current_language.set(language)


class I18nStr:
    """A string class that supports internationalization.

    This class allows you to define strings in multiple languages and automatically
    returns the appropriate string based on the current language setting.

    Args:
        strings: Either a dictionary mapping language codes to strings, or a single string
        default_language: The default language to use if the requested language is not available

    Examples:
        >>> from flask_x_openapi_schema import I18nStr
        >>> greeting = I18nStr({"en-US": "Hello", "zh-Hans": "你好", "ja-JP": "こんにちは"})
        >>> str(greeting)
        'Hello'
        >>> greeting.get("zh-Hans")
        '你好'
        >>> # @openapi_metadata(
        >>> #     summary=I18nStr({
        >>> #         "en-US": "Get an item",
        >>> #         "zh-Hans": "获取一个项目"
        >>> #     })
        >>> # )
        >>> # def get(self, item_id):
        >>> #     pass

    """

    __slots__ = ("default_language", "strings")

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: Any) -> CoreSchema:
        """Generate a pydantic core schema for I18nString.

        Args:
            _source_type: Source type (unused)
            _handler: Handler (unused)

        Returns:
            CoreSchema: A pydantic core schema for I18nString

        """
        return core_schema.is_instance_schema(cls)

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
        strings: dict[str, str] | str,
        default_language: str = "en-US",
    ) -> None:
        """Initialize an I18nString.

        Args:
            strings: Either a dictionary mapping language codes to strings,
                    or a single string (which will be used for all languages)
            default_language: The default language to use if the requested language is not available

        """
        self.default_language = default_language

        if isinstance(strings, str):
            self.strings = dict.fromkeys(self.SUPPORTED_LANGUAGES, strings)

            self.strings[self.default_language] = strings
        else:
            self.strings = strings

            if self.default_language not in self.strings:
                if self.strings:
                    self.strings[self.default_language] = next(iter(self.strings.values()))
                else:
                    self.strings[self.default_language] = ""

    def get(self, language: str | None = None) -> str:
        """Get the string in the specified language.

        Args:
            language: The language code to get the string for.
                     If None, uses the current language.

        Returns:
            str: The string in the requested language, or the default language if not available

        """
        if language is None:
            language = get_current_language()

        if language in self.strings:
            return self.strings[language]

        return self.strings[self.default_language]

    def __str__(self) -> str:
        """Get the string in the current language.

        Returns:
            str: The string in the current language

        """
        return self.get()

    def __repr__(self) -> str:
        """Get a string representation of the I18nString.

        Returns:
            str: A string representation of the I18nString

        """
        return f"I18nString({self.strings})"

    def __eq__(self, other: object) -> bool:
        """Compare this I18nString with another object.

        Args:
            other: The object to compare with

        Returns:
            bool: True if the objects are equal, False otherwise

        """
        if isinstance(other, I18nStr):
            return self.strings == other.strings
        if isinstance(other, str):
            return str(self) == other
        return False

    def __hash__(self) -> int:
        """Get a hash value for the I18nString.

        This is needed for using I18nString as a dictionary key or in sets.

        Returns:
            int: A hash value for the I18nString

        """
        return hash((frozenset(self.strings.items()), self.default_language))

    @classmethod
    def create(cls, **kwargs: Any) -> "I18nStr":
        """Create an I18nString from keyword arguments.

        This is a convenience method for creating an I18nString with named language parameters.

        Args:
            **kwargs: Keyword arguments where the keys are language codes (with underscores
                     instead of hyphens) and the values are the strings in those languages

        Returns:
            I18nStr: An I18nString instance

        Examples:
            >>> from flask_x_openapi_schema.i18n.i18n_string import I18nStr
            >>> greeting = I18nStr.create(en_US="Hello", zh_Hans="你好", ja_JP="こんにちは")
            >>> str(greeting)
            'Hello'

        """
        strings = {k.replace("_", "-"): v for k, v in kwargs.items()}
        return cls(strings)
