"""Core components for OpenAPI schema generation.

This package contains the core functionality that is independent of any specific web framework.
It provides configuration, schema generation, and utility functions for OpenAPI schema generation.
"""

from .cache import clear_all_caches
from .config import (
    GLOBAL_CONFIG_HOLDER,
    ConventionalPrefixConfig,
    OpenAPIConfig,
    configure_openapi,
    configure_prefixes,
    get_openapi_config,
    reset_all_config,
    reset_prefixes,
)
from .logger import LogFormat, configure_logging, get_logger
from .schema_generator import OpenAPISchemaGenerator
from .utils import (
    clear_i18n_cache,
    pydantic_to_openapi_schema,
    python_type_to_openapi_type,
)

__all__ = [
    "GLOBAL_CONFIG_HOLDER",
    # Configuration
    "ConventionalPrefixConfig",
    "LogFormat",
    "OpenAPIConfig",
    # Schema Generator
    "OpenAPISchemaGenerator",
    # Cache Management
    "clear_all_caches",
    "clear_i18n_cache",
    # Logging
    "configure_logging",
    "configure_openapi",
    "configure_prefixes",
    "get_logger",
    "get_openapi_config",
    # Utilities
    "pydantic_to_openapi_schema",
    "python_type_to_openapi_type",
    "reset_all_config",
    "reset_prefixes",
]
