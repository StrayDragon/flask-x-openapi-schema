"""
Core components for OpenAPI schema generation.

This package contains the core functionality that is independent of any specific web framework.
"""

from .config import ConventionalPrefixConfig, configure_prefixes, reset_prefixes, GLOBAL_CONFIG_HOLDER
from .schema_generator import OpenAPISchemaGenerator
from .utils import pydantic_to_openapi_schema, python_type_to_openapi_type

__all__ = [
    # Configuration
    "ConventionalPrefixConfig",
    "configure_prefixes",
    "reset_prefixes",
    "GLOBAL_CONFIG_HOLDER",
    # Schema Generator
    "OpenAPISchemaGenerator",
    # Utilities
    "pydantic_to_openapi_schema",
    "python_type_to_openapi_type",
]