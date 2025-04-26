"""Optional dependencies management for flask-x-openapi-schema.

This package provides utilities for managing optional dependencies in a consistent way.
It allows the library to work even when optional dependencies are not installed.
"""

from ._import_utils import (
    MissingDependencyError,
    create_placeholder_class,
    import_optional_dependency,
)

__all__ = [
    "MissingDependencyError",
    "create_placeholder_class",
    "import_optional_dependency",
]
