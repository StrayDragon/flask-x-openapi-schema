"""
Decorators for adding OpenAPI metadata to API endpoints.
This module is kept for backward compatibility.
"""

from .base import (
    ConventionalPrefixConfig,
    configure_prefixes,
    reset_prefixes,
    GLOBAL_CONFIG_HOLDER,
)

__all__ = [
    "ConventionalPrefixConfig",
    "configure_prefixes",
    "reset_prefixes",
    "GLOBAL_CONFIG_HOLDER",
]
