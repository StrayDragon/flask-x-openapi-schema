"""
Caching mechanisms for OpenAPI schema generation.

This module provides thread-safe caching utilities to improve performance
when generating OpenAPI schemas. It implements various caching strategies
to reduce computation overhead during schema generation.
"""

import threading
import weakref
from functools import lru_cache
from typing import Any, Dict, Optional, Tuple, Type, TypeVar, Generic, Union

from pydantic import BaseModel

# Type variable for cache values
T = TypeVar("T")

# Maximum size for regular dictionary caches to prevent memory leaks
MAX_CACHE_SIZE = 1000

# Cache for decorated functions to avoid recomputing metadata (weak references)
FUNCTION_METADATA_CACHE = weakref.WeakKeyDictionary()

# Cache for model instances to avoid recomputing and improve performance
MODEL_INSTANCE_CACHE = {}

# Cache for parameter detection results (using dict with size limit)
PARAM_DETECTION_CACHE: Dict[Tuple, Any] = {}

# Cache for OpenAPI parameters extracted from models (using dict with size limit)
OPENAPI_PARAMS_CACHE: Dict[Tuple, Any] = {}

# Cache for OpenAPI metadata generation (using dict with size limit)
METADATA_CACHE: Dict[Tuple, Any] = {}

# Cache for RequestParser instances (using dict with size limit)
REQPARSE_CACHE: Dict[str, Any] = {}


class ThreadSafeCache(Generic[T]):
    """
    Thread-safe generic cache with size limiting.

    This cache implementation provides thread safety using RLock and
    implements a simple LRU-like mechanism to prevent unbounded growth.
    """

    def __init__(self, max_size: int = MAX_CACHE_SIZE):
        """
        Initialize the cache with a maximum size.

        Args:
            max_size: Maximum number of items to store in the cache
        """
        self._cache: Dict[Union[str, Tuple], T] = {}
        self._lock = threading.RLock()
        self._max_size = max_size
        self._access_order: list = []  # Simple LRU tracking

    def get(self, key: Union[str, Tuple]) -> Optional[T]:
        """
        Get a value from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        with self._lock:
            if key in self._cache:
                # Update access order for LRU
                if key in self._access_order:
                    self._access_order.remove(key)
                self._access_order.append(key)
                return self._cache[key]
            return None

    def set(self, key: Union[str, Tuple], value: T) -> None:
        """
        Set a value in the cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        with self._lock:
            # Check if we need to evict items
            if len(self._cache) >= self._max_size and key not in self._cache:
                # Remove oldest item (simple LRU)
                if self._access_order:
                    oldest = self._access_order.pop(0)
                    self._cache.pop(oldest, None)

            # Add new item
            self._cache[key] = value

            # Update access order
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)

    def contains(self, key: Union[str, Tuple]) -> bool:
        """
        Check if a key exists in the cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        with self._lock:
            return key in self._cache

    def clear(self) -> None:
        """Clear the cache and access order list."""
        with self._lock:
            self._cache.clear()
            self._access_order.clear()


# Create singleton instances
MODEL_SCHEMA_CACHE = ThreadSafeCache[Dict[str, Any]]()
MODEL_CACHE = ThreadSafeCache[Any]()


def get_parameter_prefixes(
    config: Optional[Any] = None,
) -> Tuple[str, str, str, str]:
    """
    Get parameter prefixes from config or global defaults.
    This function retrieves parameter prefixes from the provided config or global defaults.

    Args:
        config: Optional configuration object with custom prefixes

    Returns:
        Tuple of (body_prefix, query_prefix, path_prefix, file_prefix)
    """
    from .config import GLOBAL_CONFIG_HOLDER

    # If config is None, use global config
    if config is None:
        prefix_config = GLOBAL_CONFIG_HOLDER.get()
    else:
        prefix_config = config

    # Extract the prefixes directly
    return (
        prefix_config.request_body_prefix,
        prefix_config.request_query_prefix,
        prefix_config.request_path_prefix,
        prefix_config.request_file_prefix,
    )


@lru_cache(maxsize=256)
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

    # Helper function to extract and cache model field types
    def extract_model_types(model: Type[BaseModel]) -> Dict[str, Any]:
        # Create a cache key based on the model's id
        model_key = id(model)

        # Check if we've already cached this model's types
        cached_types = MODEL_CACHE.get(model_key)
        if cached_types is not None:
            return cached_types

        # Get field types from the Pydantic model
        model_types = {
            field_name: field.annotation
            for field_name, field in model.model_fields.items()
        }

        # Cache the result
        MODEL_CACHE.set(model_key, model_types)
        return model_types

    # Add types from request_body if it's a Pydantic model
    if request_body_model and hasattr(request_body_model, "model_fields"):
        param_types.update(extract_model_types(request_body_model))

    # Add types from query_model if it's a Pydantic model
    if query_model and hasattr(query_model, "model_fields"):
        param_types.update(extract_model_types(query_model))

    return param_types


def clear_all_caches() -> None:
    """Clear all caches to free memory or force regeneration.

    This function clears all caches used by the library, including both
    regular dictionary caches and ThreadSafeCache instances.
    """
    import logging
    import gc

    logger = logging.getLogger(__name__)
    logger.debug("Clearing all caches")

    # Clear regular dictionary caches
    PARAM_DETECTION_CACHE.clear()
    OPENAPI_PARAMS_CACHE.clear()
    METADATA_CACHE.clear()
    REQPARSE_CACHE.clear()
    FUNCTION_METADATA_CACHE.clear()

    # Clear ThreadSafeCache instances
    # These need special handling to ensure thread safety
    MODEL_SCHEMA_CACHE.clear()
    MODEL_CACHE.clear()

    # Clear lru_cache decorated functions
    extract_param_types.cache_clear()

    # Force garbage collection to ensure all references are cleaned up
    gc.collect()

    # Log cache stats after clearing
    logger.debug(f"Cache stats after clearing: {get_cache_stats()}")


def get_cache_stats() -> Dict[str, int]:
    """Get statistics about cache usage.

    Returns:
        Dictionary with cache sizes
    """
    # Get sizes of all caches
    stats = {
        "function_metadata": len(FUNCTION_METADATA_CACHE),
        "param_detection": len(PARAM_DETECTION_CACHE),
        "openapi_params": len(OPENAPI_PARAMS_CACHE),
        "metadata": len(METADATA_CACHE),
        "reqparse": len(REQPARSE_CACHE),
    }

    # Add ThreadSafeCache sizes
    # These need to be accessed through their internal _cache attribute
    with MODEL_SCHEMA_CACHE._lock:
        stats["model_schema"] = len(MODEL_SCHEMA_CACHE._cache)

    with MODEL_CACHE._lock:
        stats["model_cache"] = len(MODEL_CACHE._cache)

    return stats


def make_cache_key(*args: Any, **kwargs: Any) -> Tuple:
    """Create a consistent cache key from arguments.

    This helper function creates a hashable cache key from a mix of
    arguments, handling common unhashable types appropriately.

    Args:
        *args: Positional arguments to include in the key
        **kwargs: Keyword arguments to include in the key

    Returns:
        A hashable tuple to use as a cache key
    """
    import logging

    logger = logging.getLogger(__name__)
    logger.debug(f"Creating cache key for args={args}, kwargs={kwargs}")

    def make_hashable(obj):
        """Convert an object to a hashable representation."""
        if isinstance(obj, dict):
            # Convert dict to sorted tuple of items with hashable values
            return tuple(sorted((k, make_hashable(v)) for k, v in obj.items()))
        elif isinstance(obj, (list, tuple)):
            # Convert list/tuple to tuple with hashable values
            return tuple(make_hashable(x) for x in obj)
        elif isinstance(obj, (str, int, float, bool, type(None))):
            # These types are already hashable
            return obj
        elif hasattr(obj, "__dict__"):
            # Use object's id for objects
            return f"obj:{id(obj)}"
        else:
            # For any other type, use string representation and id
            return f"{type(obj).__name__}:{id(obj)}"

    key_parts = []

    # Process positional args
    for arg in args:
        key_parts.append(make_hashable(arg))

    # Process keyword args (sorted by key)
    if kwargs:
        sorted_items = sorted(kwargs.items())
        for k, v in sorted_items:
            key_parts.append((k, make_hashable(v)))

    result = tuple(key_parts)
    logger.debug(f"Created cache key: {result}")

    return result
