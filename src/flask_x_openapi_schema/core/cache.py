"""
Caching mechanisms for OpenAPI schema generation.

This module provides thread-safe caching utilities to improve performance
when generating OpenAPI schemas.
"""

import threading
import weakref
from functools import lru_cache
from typing import Any, Dict, Optional, Tuple, Type

from pydantic import BaseModel

# Cache for decorated functions to avoid recomputing metadata
FUNCTION_METADATA_CACHE = weakref.WeakKeyDictionary()

# Cache for model metadata to avoid recomputing schema information
MODEL_CACHE = weakref.WeakKeyDictionary()

# Cache for parameter detection results (using dict since tuples can't be weak referenced)
PARAM_DETECTION_CACHE = {}

# Cache for OpenAPI parameters extracted from models (using dict since tuples can't be weak referenced)
OPENAPI_PARAMS_CACHE = {}

# Cache for OpenAPI metadata generation
METADATA_CACHE = {}

# Cache for RequestParser instances
REQPARSE_CACHE = {}


class ThreadSafeModelSchemaCache:
    """Thread-safe cache for model schemas."""

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a schema from the cache."""
        with self._lock:
            return self._cache.get(key)

    def set(self, key: str, value: Dict[str, Any]) -> None:
        """Set a schema in the cache."""
        with self._lock:
            self._cache[key] = value

    def contains(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        with self._lock:
            return key in self._cache

    def clear(self) -> None:
        """Clear the cache."""
        with self._lock:
            self._cache.clear()


# Create a singleton instance
MODEL_SCHEMA_CACHE = ThreadSafeModelSchemaCache()


@lru_cache(maxsize=128)
def get_parameter_prefixes(
    config: Optional[Any] = None,
) -> Tuple[str, str, str, str]:
    """
    Get parameter prefixes from config or global defaults.

    Args:
        config: Optional configuration object with custom prefixes

    Returns:
        Tuple of (body_prefix, query_prefix, path_prefix, file_prefix)
    """
    from .config import GLOBAL_CONFIG_HOLDER

    prefix_config = config or GLOBAL_CONFIG_HOLDER.get()
    return (
        prefix_config.request_body_prefix,
        prefix_config.request_query_prefix,
        prefix_config.request_path_prefix,
        prefix_config.request_file_prefix,
    )


@lru_cache(maxsize=128)
def extract_param_types(
    request_body_model: Optional[Type[BaseModel]],
    query_model: Optional[Type[BaseModel]],
) -> Dict[str, Any]:
    """
    Extract parameter types from Pydantic models for type annotations.
    This function is cached to avoid recomputing for the same models.

    Args:
        request_body_model: Request body Pydantic model
        query_model: Query parameters Pydantic model

    Returns:
        Dictionary of parameter types
    """
    param_types = {}

    # Add types from request_body if it's a Pydantic model
    if request_body_model and hasattr(request_body_model, "model_fields"):
        # Check if we've already cached this model's field types
        if request_body_model in MODEL_CACHE:
            param_types.update(MODEL_CACHE[request_body_model])
        else:
            # Get field types from the Pydantic model
            model_types = {
                field_name: field.annotation
                for field_name, field in request_body_model.model_fields.items()
            }
            # Cache the result
            MODEL_CACHE[request_body_model] = model_types
            param_types.update(model_types)

    # Add types from query_model if it's a Pydantic model
    if query_model and hasattr(query_model, "model_fields"):
        # Check if we've already cached this model's field types
        if query_model in MODEL_CACHE:
            param_types.update(MODEL_CACHE[query_model])
        else:
            # Get field types from the Pydantic model
            model_types = {
                field_name: field.annotation
                for field_name, field in query_model.model_fields.items()
            }
            # Cache the result
            MODEL_CACHE[query_model] = model_types
            param_types.update(model_types)

    return param_types


def clear_all_caches() -> None:
    """Clear all caches to free memory or force regeneration."""
    PARAM_DETECTION_CACHE.clear()
    OPENAPI_PARAMS_CACHE.clear()
    METADATA_CACHE.clear()
    REQPARSE_CACHE.clear()
    MODEL_SCHEMA_CACHE.clear()
    get_parameter_prefixes.cache_clear()
    extract_param_types.cache_clear()