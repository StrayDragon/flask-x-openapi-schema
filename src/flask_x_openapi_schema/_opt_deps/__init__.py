"""
Optional dependencies management for flask-x-openapi-schema.

This package provides utilities for managing optional dependencies in a consistent way.
It allows the library to work even when optional dependencies are not installed.
"""

from ._import_utils import (
    MissingDependencyError,
    import_optional_dependency,
    create_placeholder_class,
)

__all__ = [
    "MissingDependencyError",
    "import_optional_dependency",
    "create_placeholder_class",
]
