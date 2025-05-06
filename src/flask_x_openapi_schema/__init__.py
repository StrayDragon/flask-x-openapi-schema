"""Flask-X-OpenAPI-Schema: A Flask extension for generating OpenAPI schemas from Pydantic models."""

from .core.cache import (
    clear_all_caches,
)
from .core.config import (
    GLOBAL_CONFIG_HOLDER,
    CacheConfig,
    ConventionalPrefixConfig,
    configure_cache,
    configure_prefixes,
    get_cache_config,
    reset_prefixes,
)

# No default error implementations are provided
from .core.error_handlers import (
    DefaultErrorResponse,
    create_error_response,
    create_status_error_response,
    handle_api_error,
    handle_request_validation_error,
    handle_validation_error,
)
from .core.exceptions import APIError
from .core.logger import LogFormat, configure_logging, get_logger
from .core.schema_generator import OpenAPISchemaGenerator
from .i18n.i18n_string import I18nStr, get_current_language, set_current_language
from .models.base import BaseErrorResponse, BaseRespModel
from .models.content_types import (
    ContentTypeCategory,
    ContentTypeHandler,
    ContentTypeMapping,
    RequestContentTypes,
    ResponseContentTypes,
    detect_content_type_from_model,
)
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

__all__ = [
    "GLOBAL_CONFIG_HOLDER",
    "APIError",
    "BaseErrorResponse",
    "BaseRespModel",
    "CacheConfig",
    "ContentTypeCategory",
    "ContentTypeHandler",
    "ContentTypeMapping",
    "ConventionalPrefixConfig",
    "DefaultErrorResponse",
    "DocumentUploadModel",
    "FileUploadModel",
    "I18nStr",
    "ImageUploadModel",
    "LogFormat",
    "MultipleFileUploadModel",
    "OpenAPIMetaResponse",
    "OpenAPIMetaResponseItem",
    "OpenAPISchemaGenerator",
    "RequestContentTypes",
    "ResponseContentTypes",
    "clear_all_caches",
    "configure_cache",
    "configure_logging",
    "configure_prefixes",
    "create_error_response",
    "create_response",
    "create_status_error_response",
    "detect_content_type_from_model",
    "error_response",
    "get_cache_config",
    "get_current_language",
    "get_logger",
    "handle_api_error",
    "handle_request_validation_error",
    "handle_validation_error",
    "reset_prefixes",
    "set_current_language",
    "success_response",
]
