"""
Flask-RESTful specific implementations for OpenAPI schema generation.
"""

from .decorators import openapi_metadata
from .resources import OpenAPIIntegrationMixin, OpenAPIBlueprintMixin

__all__ = [
    "openapi_metadata",
    "OpenAPIIntegrationMixin",
    "OpenAPIBlueprintMixin",
]
