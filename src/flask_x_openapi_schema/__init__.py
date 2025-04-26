"""Flask-X-OpenAPI-Schema: A Flask extension for generating OpenAPI schemas from Pydantic models."""

from .core.config import (
    GLOBAL_CONFIG_HOLDER,
    ConventionalPrefixConfig,
    configure_prefixes,
    reset_prefixes,
)
from .core.schema_generator import OpenAPISchemaGenerator
from .i18n.i18n_string import I18nStr, get_current_language, set_current_language
from .models.base import BaseRespModel
from .models.file_models import (
    DocumentUploadModel,
    FileUploadModel,
    ImageUploadModel,
    MultipleFileUploadModel,
)
from .models.responses import (
    OpenAPIMetaResponse,
    OpenAPIMetaResponseItem,
    create_response,
    error_response,
    success_response,
)
from .x.flask.views import OpenAPIMethodViewMixin
from .x.flask_restful.resources import OpenAPIBlueprintMixin, OpenAPIIntegrationMixin

__all__ = [
    "GLOBAL_CONFIG_HOLDER",
    # Models
    "BaseRespModel",
    # Configuration
    "ConventionalPrefixConfig",
    "DocumentUploadModel",
    "FileUploadModel",
    # I18n
    "I18nStr",
    "ImageUploadModel",
    "MultipleFileUploadModel",
    "OpenAPIBlueprintMixin",
    # Mixins
    "OpenAPIIntegrationMixin",
    # Response Models
    "OpenAPIMetaResponse",
    "OpenAPIMetaResponseItem",
    # MethodView
    "OpenAPIMethodViewMixin",
    # Schema Generator
    "OpenAPISchemaGenerator",
    "configure_prefixes",
    "create_response",
    "error_response",
    "get_current_language",
    "reset_prefixes",
    "set_current_language",
    "success_response",
    # Decorators
]
