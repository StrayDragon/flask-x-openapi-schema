"""
Core components for OpenAPI schema generation.

This package contains the core functionality that is independent of any specific web framework.
It provides configuration, schema generation, and utility functions for OpenAPI schema generation.
"""

from .cache import clear_all_caches, get_cache_stats
from .config import (
    ConventionalPrefixConfig,
    OpenAPIConfig,
    configure_prefixes,
    configure_openapi,
    reset_prefixes,
    reset_all_config,
    get_openapi_config,
    GLOBAL_CONFIG_HOLDER,
)
from .schema_generator import OpenAPISchemaGenerator
from .utils import (
    pydantic_to_openapi_schema,
    python_type_to_openapi_type,
    clear_i18n_cache,
)

__all__ = [
    # Cache Management
    "clear_all_caches",
    "get_cache_stats",
    # Configuration
    "ConventionalPrefixConfig",
    "OpenAPIConfig",
    "configure_prefixes",
    "configure_openapi",
    "reset_prefixes",
    "reset_all_config",
    "get_openapi_config",
    "GLOBAL_CONFIG_HOLDER",
    # Schema Generator
    "OpenAPISchemaGenerator",
    # Utilities
    "pydantic_to_openapi_schema",
    "python_type_to_openapi_type",
    "clear_i18n_cache",
]
