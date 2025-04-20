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
from .models.responses import (
    OpenAPIMetaResponse,
    OpenAPIMetaResponseItem,
    create_response,
    success_response,
    error_response,
)
from .i18n.i18n_string import I18nStr, set_current_language, get_current_language
from .x.flask.views import OpenAPIMethodViewMixin
from .x.flask_restful.resources import OpenAPIIntegrationMixin, OpenAPIBlueprintMixin
from .core.schema_generator import OpenAPISchemaGenerator

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
    # Response Models
    "OpenAPIMetaResponse",
    "OpenAPIMetaResponseItem",
    "create_response",
    "success_response",
    "error_response",
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
]
