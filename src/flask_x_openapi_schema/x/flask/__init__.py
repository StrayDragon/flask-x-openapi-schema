"""
Flask-specific implementations for OpenAPI schema generation.
"""

from .decorators import openapi_metadata
from .views import OpenAPIMethodViewMixin

__all__ = [
    "openapi_metadata",
    "OpenAPIMethodViewMixin",
]
