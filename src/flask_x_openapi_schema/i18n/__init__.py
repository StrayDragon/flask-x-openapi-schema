"""
Internationalization support for OpenAPI metadata.
"""

from .i18n_string import I18nString, get_current_language, set_current_language

__all__ = [
    "I18nString",
    "get_current_language",
    "set_current_language",
]
