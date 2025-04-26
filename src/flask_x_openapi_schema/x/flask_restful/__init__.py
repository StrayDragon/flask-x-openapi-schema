"""Flask-RESTful specific implementations for OpenAPI schema generation."""

from .decorators import openapi_metadata
from .resources import OpenAPIBlueprintMixin, OpenAPIIntegrationMixin

__all__ = [
    "OpenAPIBlueprintMixin",
    "OpenAPIIntegrationMixin",
    "openapi_metadata",
]
