"""Flask-X-OpenAPI-Schema: A Flask extension for generating OpenAPI schemas from Pydantic models."""

from .core.cache import (
    CacheEvictionPolicy,
    ThreadSafeCache,
    TTLCache,
    clear_all_caches,
    get_cache_stats,
    warmup_cache,
)
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

__all__ = [
    "GLOBAL_CONFIG_HOLDER",
    # Models
    "BaseRespModel",
    # Cache
    "CacheEvictionPolicy",
    # Configuration
    "ConventionalPrefixConfig",
    "DocumentUploadModel",
    "FileUploadModel",
    # I18n
    "I18nStr",
    "ImageUploadModel",
    "MultipleFileUploadModel",
    # Response Models
    "OpenAPIMetaResponse",
    "OpenAPIMetaResponseItem",
    # Schema Generator
    "OpenAPISchemaGenerator",
    "TTLCache",
    "ThreadSafeCache",
    "clear_all_caches",
    # Configuration functions
    "configure_prefixes",
    "create_response",
    "error_response",
    "get_cache_stats",
    "get_current_language",
    "reset_prefixes",
    "set_current_language",
    "success_response",
    "warmup_cache",
    # Decorators
    # ref to .x
]
