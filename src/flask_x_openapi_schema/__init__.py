"""
Flask-X-OpenAPI-Schema: A Flask extension for generating OpenAPI schemas from Pydantic models.
"""

from .core.config import (
    ConventionalPrefixConfig,
    configure_prefixes,
    reset_prefixes,
    GLOBAL_CONFIG_HOLDER,
)
from .models.base import BaseRespModel
from .models.file_models import (
    FileUploadModel,
    ImageUploadModel,
    DocumentUploadModel,
    MultipleFileUploadModel,
)
from .i18n.i18n_string import I18nStr, set_current_language, get_current_language
from .extensions.flask.views import OpenAPIMethodViewMixin
from .extensions.flask_restful.resources import OpenAPIIntegrationMixin, OpenAPIBlueprintMixin
from .core.schema_generator import OpenAPISchemaGenerator

# Import decorators from extensions
from .extensions.flask import openapi_metadata as flask_openapi_metadata
from .extensions.flask_restful import openapi_metadata as flask_restful_openapi_metadata

# Provide a unified decorator that selects the appropriate implementation
def openapi_metadata(*args, **kwargs):
    """
    Decorator to add OpenAPI metadata to a Flask or Flask-RESTful endpoint.
    
    This decorator automatically selects the appropriate implementation based on the context.
    For Flask MethodView, use flask_openapi_metadata directly.
    For Flask-RESTful Resource, use flask_restful_openapi_metadata directly.
    
    See the documentation for each specific decorator for more details.
    """
    # If called with a function, determine which decorator to use
    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]
        # Check if it's a Flask-RESTful Resource method
        if hasattr(func, "__self__") and hasattr(func.__self__, "as_view"):
            return flask_restful_openapi_metadata(func)
        # Default to Flask decorator
        return flask_openapi_metadata(func)
    
    # If called with keyword arguments, return a decorator function
    def decorator(func):
        # Check if it's a Flask-RESTful Resource method
        if hasattr(func, "__self__") and hasattr(func.__self__, "as_view"):
            return flask_restful_openapi_metadata(**kwargs)(func)
        # Default to Flask decorator
        return flask_openapi_metadata(**kwargs)(func)
    
    return decorator

__all__ = [
    # Configuration
    "ConventionalPrefixConfig",
    "configure_prefixes",
    "reset_prefixes",
    "GLOBAL_CONFIG_HOLDER",
    # Models
    "BaseRespModel",
    "FileUploadModel",
    "ImageUploadModel",
    "DocumentUploadModel",
    "MultipleFileUploadModel",
    # I18n
    "I18nStr",
    "set_current_language",
    "get_current_language",
    # MethodView
    "OpenAPIMethodViewMixin",
    # Mixins
    "OpenAPIIntegrationMixin",
    "OpenAPIBlueprintMixin",
    # Schema Generator
    "OpenAPISchemaGenerator",
    # Decorators
    "openapi_metadata",
    "flask_openapi_metadata",
    "flask_restful_openapi_metadata",
]