"""Caching mechanisms for OpenAPI schema generation.

This module provides thread-safe caching utilities to improve performance
when generating OpenAPI schemas. It implements various caching strategies
to reduce computation overhead during schema generation.

Cache Types:
    - ThreadSafeCache: A generic, thread-safe cache with LRU eviction policy
    - TTLCache: Thread-safe cache with time-to-live expiration
    - LFUCache: Thread-safe cache with Least Frequently Used eviction policy
    - WeakKeyDictionary: For function metadata to avoid memory leaks
    - Regular dictionaries with size limits: For parameter detection, OpenAPI parameters, etc.
    - LRU cache decorator: For frequently called functions with stable inputs

Performance Considerations:
    - All caches implement size limits to prevent unbounded memory growth
    - Thread safety is ensured using RLock for all shared caches
    - Cache keys are carefully designed to be both unique and hashable
    - Weak references are used where appropriate to avoid memory leaks
    - Cache clearing is provided to support testing and memory management
    - TTL mechanism automatically removes expired entries
    - Cache statistics provide insights into cache performance

Thread Safety:
    This module is designed to be thread-safe for use in multi-threaded web servers.
    All cache operations use appropriate locking mechanisms to prevent race conditions.
"""

import threading
import time
import weakref
from collections import Counter, OrderedDict
from collections.abc import Callable
from enum import Enum
from functools import lru_cache, wraps
from typing import Any, Generic, TypeVar, cast

from pydantic import BaseModel

from .cache_factory import CACHE_FACTORY, CacheType

# Type variable for cache values
T = TypeVar("T")
K = TypeVar("K")
F = TypeVar("F", bound=Callable[..., Any])

# These constants will be overridden by the cache config
# but are kept here as fallbacks
MAX_CACHE_SIZE = 1000
DEFAULT_TTL = 300  # 5 minutes

# Cache for decorated functions to avoid recomputing metadata (weak references)
FUNCTION_METADATA_CACHE = weakref.WeakKeyDictionary()

# Cache for model instances to avoid recomputing and improve performance
MODEL_INSTANCE_CACHE = {}

# Cache for parameter detection results (using dict with size limit)
PARAM_DETECTION_CACHE: dict[tuple, Any] = {}

# Maximum size for PARAM_DETECTION_CACHE items
MAX_PARAM_DETECTION_CACHE_SIZE = 1000

# Cache for OpenAPI parameters extracted from models (using dict with size limit)
OPENAPI_PARAMS_CACHE: dict[tuple, Any] = {}

# Maximum size for OPENAPI_PARAMS_CACHE items
MAX_OPENAPI_PARAMS_CACHE_SIZE = 1000

# Cache for OpenAPI metadata generation (using dict with size limit)
METADATA_CACHE: dict[tuple, Any] = {}

# Maximum size for METADATA_CACHE items
MAX_METADATA_CACHE_SIZE = 1000

# Cache for RequestParser instances (using dict with size limit)
REQPARSE_CACHE: dict[str, Any] = {}

# Cache for i18n string processing
_I18N_CACHE: dict[tuple, Any] = {}


class CacheEvictionPolicy(Enum):
    """Enumeration of cache eviction policies."""

    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    FIFO = "fifo"  # First In First Out


class CacheBase(Generic[K, T]):
    """Base class for all cache implementations."""

    def __init__(self, max_size: int = MAX_CACHE_SIZE) -> None:
        """Initialize the cache with a maximum size.

        Args:
            max_size: Maximum number of items to store in the cache

        """
        self._lock = threading.RLock()
        self._max_size = max_size
        self._hits = 0
        self._misses = 0

    def get(self, key: K) -> T | None:
        """Get a value from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found

        """
        raise NotImplementedError

    def set(self, key: K, value: T) -> None:
        """Set a value in the cache.

        Args:
            key: Cache key
            value: Value to cache

        """
        raise NotImplementedError

    def contains(self, key: K) -> bool:
        """Check if a key exists in the cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise

        """
        raise NotImplementedError

    def clear(self) -> None:
        """Clear the cache."""
        raise NotImplementedError

    def remove(self, key: K) -> bool:
        """Remove a key from the cache.

        Args:
            key: Cache key

        Returns:
            True if key was removed, False if key was not in cache

        """
        raise NotImplementedError

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics

        """
        with self._lock:
            total_accesses = self._hits + self._misses
            hit_rate = self._hits / total_accesses if total_accesses > 0 else 0
            return {
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
                "max_size": self._max_size,
                "current_size": self.size(),
            }

    def size(self) -> int:
        """Get the current size of the cache.

        Returns:
            Number of items in the cache

        """
        raise NotImplementedError


class ThreadSafeCache(CacheBase[K, T]):
    """Thread-safe generic cache with size limiting.

    This cache implementation provides thread safety using RLock and
    implements a simple LRU-like mechanism to prevent unbounded growth.
    """

    def __init__(
        self, max_size: int = MAX_CACHE_SIZE, eviction_policy: CacheEvictionPolicy = CacheEvictionPolicy.LRU
    ) -> None:
        """Initialize the cache with a maximum size.

        Args:
            max_size: Maximum number of items to store in the cache
            eviction_policy: Policy to use when evicting items from the cache

        """
        super().__init__(max_size)
        self._cache: dict[str | tuple, T] = {}
        self._eviction_policy = eviction_policy

        # Data structures for different eviction policies
        if eviction_policy == CacheEvictionPolicy.LRU:
            self._access_order = OrderedDict()  # More efficient than list for LRU
        elif eviction_policy == CacheEvictionPolicy.LFU:
            self._access_count = Counter()  # Count access frequency
        elif eviction_policy == CacheEvictionPolicy.FIFO:
            self._insertion_order = []  # Track insertion order

    def get(self, key: str | tuple) -> T | None:
        """Get a value from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found

        """
        with self._lock:
            if key in self._cache:
                self._hits += 1

                # Update tracking based on eviction policy
                if self._eviction_policy == CacheEvictionPolicy.LRU:
                    # Move to end (most recently used)
                    self._access_order.move_to_end(key)
                elif self._eviction_policy == CacheEvictionPolicy.LFU:
                    # Increment access count
                    self._access_count[key] += 1

                return self._cache[key]

            self._misses += 1
            return None

    def set(self, key: str | tuple, value: T) -> None:
        """Set a value in the cache.

        Args:
            key: Cache key
            value: Value to cache

        """
        with self._lock:
            # If key already exists, just update the value and tracking
            if key in self._cache:
                self._cache[key] = value

                # Update tracking based on eviction policy
                if self._eviction_policy == CacheEvictionPolicy.LRU:
                    # Move to end (most recently used)
                    self._access_order.move_to_end(key)
                elif self._eviction_policy == CacheEvictionPolicy.LFU:
                    # Reset access count for updated items
                    self._access_count[key] = 1
                # For FIFO, we don't change the insertion order when updating

                return

            # Check if we need to evict items for new keys
            if len(self._cache) >= self._max_size:
                # Force eviction when cache is full
                self._evict_item()

                # Double-check that eviction actually happened
                if len(self._cache) >= self._max_size and self._cache:
                    # If eviction didn't work (e.g., due to empty tracking structures),
                    # remove any item to make space
                    # Remove first item we find
                    first_key = next(iter(self._cache))
                    if first_key in self._cache:
                        del self._cache[first_key]

                    # Also remove from tracking structures
                    if self._eviction_policy == CacheEvictionPolicy.LRU and first_key in self._access_order:
                        del self._access_order[first_key]
                    elif self._eviction_policy == CacheEvictionPolicy.LFU and first_key in self._access_count:
                        del self._access_count[first_key]
                    elif self._eviction_policy == CacheEvictionPolicy.FIFO and first_key in self._insertion_order:
                        self._insertion_order.remove(first_key)

            # Add new item
            self._cache[key] = value

            # Update tracking based on eviction policy
            if self._eviction_policy == CacheEvictionPolicy.LRU:
                self._access_order[key] = None  # OrderedDict doesn't need a value
            elif self._eviction_policy == CacheEvictionPolicy.LFU:
                self._access_count[key] = 1  # Initialize access count
            elif self._eviction_policy == CacheEvictionPolicy.FIFO and key not in self._insertion_order:
                # Only add to insertion order if not already there
                self._insertion_order.append(key)

    def _evict_item(self) -> None:
        """Evict an item based on the current eviction policy."""
        if not self._cache:
            return

        if self._eviction_policy == CacheEvictionPolicy.LRU:
            # Remove least recently used item (first item in OrderedDict)
            if self._access_order:
                try:
                    # Get the first key (least recently used)
                    oldest_key, _ = self._access_order.popitem(last=False)
                    # Remove from cache
                    if oldest_key in self._cache:
                        del self._cache[oldest_key]
                except KeyError:
                    # Handle case where key might have been removed already
                    pass

        elif self._eviction_policy == CacheEvictionPolicy.LFU:
            # Remove least frequently used item
            if self._access_count:
                # Get key with minimum access count that is in the cache
                valid_keys = [k for k in self._access_count if k in self._cache]
                if valid_keys:
                    # Find the key with minimum access count
                    least_used_key = min(valid_keys, key=lambda k: self._access_count[k])
                    # Remove from cache
                    if least_used_key in self._cache:
                        del self._cache[least_used_key]
                    # Remove from access count
                    if least_used_key in self._access_count:
                        del self._access_count[least_used_key]

        elif self._eviction_policy == CacheEvictionPolicy.FIFO and self._insertion_order:
            # Remove oldest item (first in)
            oldest_key = self._insertion_order.pop(0)
            # Remove from cache
            if oldest_key in self._cache:
                del self._cache[oldest_key]

    def contains(self, key: str | tuple) -> bool:
        """Check if a key exists in the cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise

        """
        with self._lock:
            return key in self._cache

    def clear(self) -> None:
        """Clear the cache and tracking data structures."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

            # Clear policy-specific data structures
            if self._eviction_policy == CacheEvictionPolicy.LRU:
                self._access_order.clear()
            elif self._eviction_policy == CacheEvictionPolicy.LFU:
                self._access_count.clear()
            elif self._eviction_policy == CacheEvictionPolicy.FIFO:
                self._insertion_order.clear()

    def remove(self, key: str | tuple) -> bool:
        """Remove a key from the cache.

        Args:
            key: Cache key

        Returns:
            True if key was removed, False if key was not in cache

        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]

                # Remove from policy-specific data structures
                if self._eviction_policy == CacheEvictionPolicy.LRU:
                    if key in self._access_order:
                        del self._access_order[key]
                elif self._eviction_policy == CacheEvictionPolicy.LFU:
                    if key in self._access_count:
                        del self._access_count[key]
                elif self._eviction_policy == CacheEvictionPolicy.FIFO and key in self._insertion_order:
                    self._insertion_order.remove(key)

                return True
            return False

    def size(self) -> int:
        """Get the current size of the cache.

        Returns:
            Number of items in the cache

        """
        with self._lock:
            return len(self._cache)


class TTLCache(ThreadSafeCache[K, T]):
    """Thread-safe cache with time-to-live (TTL) expiration.

    This cache extends ThreadSafeCache to add TTL functionality,
    automatically expiring entries after a specified time period.
    """

    def __init__(
        self,
        max_size: int = MAX_CACHE_SIZE,
        ttl: int = DEFAULT_TTL,
        eviction_policy: CacheEvictionPolicy = CacheEvictionPolicy.LRU,
    ) -> None:
        """Initialize the TTL cache.

        Args:
            max_size: Maximum number of items to store in the cache
            ttl: Default time-to-live in seconds for cache entries
            eviction_policy: Policy to use when evicting items from the cache

        """
        super().__init__(max_size, eviction_policy)
        self._ttl = ttl
        self._expiry_times: dict[str | tuple, float] = {}

    def get(self, key: str | tuple) -> T | None:
        """Get a value from the cache, checking for expiration.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found or expired

        """
        with self._lock:
            # Check if key exists and hasn't expired
            if key in self._cache and key in self._expiry_times:
                if time.time() < self._expiry_times[key]:
                    # Not expired, update access tracking and return
                    self._hits += 1

                    # Update tracking based on eviction policy
                    if self._eviction_policy == CacheEvictionPolicy.LRU:
                        self._access_order.move_to_end(key)
                    elif self._eviction_policy == CacheEvictionPolicy.LFU:
                        self._access_count[key] += 1

                    return self._cache[key]
                # Expired, remove it
                self._remove_expired_entry(key)

            self._misses += 1
            return None

    def set(self, key: str | tuple, value: T, ttl: int | None = None) -> None:
        """Set a value in the cache with a TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)

        """
        with self._lock:
            # Clean expired entries if cache is full
            if len(self._cache) >= self._max_size and key not in self._cache:
                # Try to remove expired entries first
                self._remove_all_expired()

                # If still full, evict based on policy
                if len(self._cache) >= self._max_size:
                    # Force eviction when cache is full
                    self._evict_item()

                    # Double-check that eviction actually happened
                    if len(self._cache) >= self._max_size and self._cache:
                        # If eviction didn't work, remove any item to make space
                        # Remove first item we find
                        first_key = next(iter(self._cache))
                        self._cache.pop(first_key, None)

                        # Also remove from tracking structures
                        if first_key in self._expiry_times:
                            del self._expiry_times[first_key]

                        # And from policy-specific structures
                        if self._eviction_policy == CacheEvictionPolicy.LRU and first_key in self._access_order:
                            del self._access_order[first_key]
                        elif self._eviction_policy == CacheEvictionPolicy.LFU and first_key in self._access_count:
                            del self._access_count[first_key]
                        elif self._eviction_policy == CacheEvictionPolicy.FIFO and first_key in self._insertion_order:
                            self._insertion_order.remove(first_key)

            # Add new item
            self._cache[key] = value

            # Set expiry time
            actual_ttl = ttl if ttl is not None else self._ttl
            self._expiry_times[key] = time.time() + actual_ttl

            # Update tracking based on eviction policy
            if self._eviction_policy == CacheEvictionPolicy.LRU:
                self._access_order[key] = None
            elif self._eviction_policy == CacheEvictionPolicy.LFU:
                self._access_count[key] = 1
            elif self._eviction_policy == CacheEvictionPolicy.FIFO and key not in self._insertion_order:
                self._insertion_order.append(key)

    def _remove_expired_entry(self, key: str | tuple) -> None:
        """Remove a single expired entry.

        Args:
            key: Cache key to remove

        """
        if key in self._cache:
            del self._cache[key]

        if key in self._expiry_times:
            del self._expiry_times[key]

        # Remove from policy-specific data structures
        if self._eviction_policy == CacheEvictionPolicy.LRU:
            if key in self._access_order:
                del self._access_order[key]
        elif self._eviction_policy == CacheEvictionPolicy.LFU:
            if key in self._access_count:
                del self._access_count[key]
        elif self._eviction_policy == CacheEvictionPolicy.FIFO and key in self._insertion_order:
            self._insertion_order.remove(key)

    def _remove_all_expired(self) -> int:
        """Remove all expired entries from the cache.

        Returns:
            Number of entries removed

        """
        now = time.time()
        expired_keys = [k for k, exp_time in self._expiry_times.items() if exp_time <= now]

        for key in expired_keys:
            self._remove_expired_entry(key)

        return len(expired_keys)

    def clear(self) -> None:
        """Clear the cache, expiry times, and tracking data structures."""
        with self._lock:
            super().clear()
            self._expiry_times.clear()

    def remove(self, key: str | tuple) -> bool:
        """Remove a key from the cache.

        Args:
            key: Cache key

        Returns:
            True if key was removed, False if key was not in cache

        """
        with self._lock:
            result = super().remove(key)
            if key in self._expiry_times:
                del self._expiry_times[key]
            return result

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics including TTL information.

        Returns:
            Dictionary with cache statistics

        """
        stats = super().get_stats()
        with self._lock:
            # Add TTL-specific stats
            now = time.time()
            expired_count = sum(1 for exp_time in self._expiry_times.values() if exp_time <= now)

            stats.update(
                {
                    "ttl_default": self._ttl,
                    "expired_entries": expired_count,
                    "active_entries": len(self._cache) - expired_count,
                }
            )

            return stats


def initialize_cache_factory() -> None:
    """Initialize the cache factory with settings from configuration.

    This function reads the cache configuration and updates the cache factory.
    """
    try:
        from .config import get_cache_config

        config = get_cache_config()
        CACHE_FACTORY.update_config(
            cache_enabled=config.enabled,
            schema_cache_enabled=config.schema_cache_enabled,
            param_binding_cache_enabled=config.param_binding_cache_enabled,
            model_cache_enabled=config.model_cache_enabled,
            metadata_cache_enabled=config.metadata_cache_enabled,
            max_cache_size=config.max_cache_size,
            ttl_cache_duration=config.ttl_cache_duration,
        )
    except (ImportError, AttributeError):
        # Fallback to defaults if config is not available
        CACHE_FACTORY.update_config(
            cache_enabled=True,
            schema_cache_enabled=True,
            param_binding_cache_enabled=True,
            model_cache_enabled=True,
            metadata_cache_enabled=True,
            max_cache_size=MAX_CACHE_SIZE,
            ttl_cache_duration=DEFAULT_TTL,
        )


# Initialize the cache factory
initialize_cache_factory()

# Create backing dictionaries for caches
_MODEL_SCHEMA_CACHE_DICT: dict[str | tuple, dict[str, Any]] = {}
_MODEL_CACHE_DICT: dict[str | tuple, Any] = {}
_DYNAMIC_SCHEMA_CACHE_DICT: dict[str | tuple, dict[str, Any]] = {}
_REQUEST_DATA_CACHE_DICT: dict[str | tuple, Any] = {}
_PARAM_DETECTION_CACHE_DICT: dict[tuple, Any] = {}
_OPENAPI_PARAMS_CACHE_DICT: dict[tuple, Any] = {}
_METADATA_CACHE_DICT: dict[tuple, Any] = {}


# Create cache strategies using the factory
def get_model_schema_cache() -> Any:
    """Get the model schema cache strategy."""
    return CACHE_FACTORY.get_cache_strategy(CacheType.SCHEMA, _MODEL_SCHEMA_CACHE_DICT, "model_schema", 1000)


def get_model_cache() -> Any:
    """Get the model cache strategy."""
    return CACHE_FACTORY.get_cache_strategy(CacheType.MODEL, _MODEL_CACHE_DICT, "model", 1000)


def get_dynamic_schema_cache() -> Any:
    """Get the dynamic schema cache strategy."""
    return CACHE_FACTORY.get_cache_strategy(CacheType.SCHEMA, _DYNAMIC_SCHEMA_CACHE_DICT, "dynamic_schema", 500)


def get_request_data_cache() -> Any:
    """Get the request data cache strategy."""
    return CACHE_FACTORY.get_cache_strategy(CacheType.GENERAL, _REQUEST_DATA_CACHE_DICT, "request_data", 200)


def get_param_detection_cache() -> Any:
    """Get the parameter detection cache strategy."""
    return CACHE_FACTORY.get_cache_strategy(
        CacheType.PARAM_BINDING, _PARAM_DETECTION_CACHE_DICT, "param_detection", 1000
    )


def get_openapi_params_cache() -> Any:
    """Get the OpenAPI parameters cache strategy."""
    return CACHE_FACTORY.get_cache_strategy(CacheType.SCHEMA, _OPENAPI_PARAMS_CACHE_DICT, "openapi_params", 1000)


def get_metadata_cache() -> Any:
    """Get the metadata cache strategy."""
    return CACHE_FACTORY.get_cache_strategy(CacheType.METADATA, _METADATA_CACHE_DICT, "metadata", 1000)


# For backward compatibility, create cache objects that mimic the old API
# but use the new strategy pattern internally
class StrategyBasedCache(Generic[K, T]):
    """Cache adapter that uses a strategy internally but presents the old API."""

    def __init__(self, cache_type: CacheType, backing_dict: dict[K, T], name: str, max_size: int = 1000) -> None:
        """Initialize with a strategy from the factory."""
        self._strategy = CACHE_FACTORY.get_cache_strategy(cache_type, backing_dict, name, max_size)

    def get(self, key: K) -> T | None:
        """Get a value from the cache."""
        return self._strategy.get(key)

    def set(self, key: K, value: T) -> None:
        """Set a value in the cache."""
        self._strategy.set(key, value)

    def contains(self, key: K) -> bool:
        """Check if a key exists in the cache."""
        return self._strategy.contains(key)

    def clear(self) -> None:
        """Clear the cache."""
        self._strategy.clear()

    def remove(self, key: K) -> bool:
        """Remove a key from the cache."""
        return self._strategy.remove(key)

    def size(self) -> int:
        """Get the current size of the cache."""
        return self._strategy.size()

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return self._strategy.get_stats()


# Create singleton instances with the adapter for backward compatibility
MODEL_SCHEMA_CACHE = StrategyBasedCache(CacheType.SCHEMA, _MODEL_SCHEMA_CACHE_DICT, "model_schema", 1000)
MODEL_CACHE = StrategyBasedCache(CacheType.MODEL, _MODEL_CACHE_DICT, "model", 1000)
DYNAMIC_SCHEMA_CACHE = StrategyBasedCache(CacheType.SCHEMA, _DYNAMIC_SCHEMA_CACHE_DICT, "dynamic_schema", 500)
REQUEST_DATA_CACHE = StrategyBasedCache(CacheType.GENERAL, _REQUEST_DATA_CACHE_DICT, "request_data", 200)

# Create regular dictionary caches for backward compatibility
PARAM_DETECTION_CACHE = _PARAM_DETECTION_CACHE_DICT
OPENAPI_PARAMS_CACHE = _OPENAPI_PARAMS_CACHE_DICT
METADATA_CACHE = _METADATA_CACHE_DICT


def get_parameter_prefixes(
    config: Any | None = None,
) -> tuple[str, str, str, str]:
    """Get parameter prefixes from config or global defaults.

    This function retrieves parameter prefixes from the provided config or global defaults.

    Args:
        config: Optional configuration object with custom prefixes

    Returns:
        Tuple of (body_prefix, query_prefix, path_prefix, file_prefix)

    """
    from .config import GLOBAL_CONFIG_HOLDER

    # If config is None, use global config
    prefix_config = GLOBAL_CONFIG_HOLDER.get() if config is None else config

    # Extract the prefixes directly
    return (
        prefix_config.request_body_prefix,
        prefix_config.request_query_prefix,
        prefix_config.request_path_prefix,
        prefix_config.request_file_prefix,
    )


def conditional_cache(cache_type: str = "param_binding"):  # noqa: ANN201
    """Conditionally apply caching based on configuration.

    This decorator checks the cache configuration and only applies caching
    if it's enabled for the specified cache type. It uses the cache factory
    to determine if caching should be enabled.

    Args:
        cache_type: Type of cache to check ("schema", "param_binding", "model", "metadata")

    Returns:
        Decorator function that conditionally applies caching

    """
    # Map string cache types to CacheType enum
    cache_type_map = {
        "schema": CacheType.SCHEMA,
        "param_binding": CacheType.PARAM_BINDING,
        "model": CacheType.MODEL,
        "metadata": CacheType.METADATA,
        "general": CacheType.GENERAL,
    }

    cache_type_enum = cache_type_map.get(cache_type, CacheType.GENERAL)

    def decorator(func: F) -> F:
        # Check if caching is enabled for this type using the factory
        if not CACHE_FACTORY.is_cache_enabled(cache_type_enum):
            return func

        # Create a unique name for this function's cache
        # func_name = f"{func.__module__}.{func.__qualname__}"  # noqa: ERA001

        # Apply lru_cache with appropriate size from factory
        max_size = CACHE_FACTORY._max_cache_size  # noqa: SLF001
        cached_func = lru_cache(maxsize=max_size)(func)

        # Add cache_clear method to the wrapped function
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return cached_func(*args, **kwargs)

        wrapper.cache_clear = cached_func.cache_clear
        return cast("F", wrapper)

    return decorator


@conditional_cache(cache_type="param_binding")
def extract_param_types(
    request_body_model: type[BaseModel] | None,
    query_model: type[BaseModel] | None,
) -> dict[str, Any]:
    """Extract parameter types from Pydantic models for type annotations.

    This function is cached to avoid recomputing for the same models.

    Args:
        request_body_model: Request body Pydantic model
        query_model: Query parameters Pydantic model

    Returns:
        Dictionary of parameter types

    """
    param_types = {}

    # Helper function to extract and cache model field types
    def extract_model_types(model: type[BaseModel]) -> dict[str, Any]:
        # Create a cache key based on the model's id
        model_key = id(model)

        # Get the model cache strategy
        model_cache = get_model_cache()

        # Check if we've already cached this model's types
        cached_types = model_cache.get(model_key)
        if cached_types is not None:
            return cached_types

        # Get field types from the Pydantic model
        model_types = {field_name: field.annotation for field_name, field in model.model_fields.items()}

        # Cache the result
        model_cache.set(model_key, model_types)
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
    regular dictionary caches and strategy-based caches.
    """
    import gc

    from flask_x_openapi_schema.core.logger import get_logger

    logger = get_logger(__name__)
    logger.debug("Clearing all caches")

    # Use the cache factory to clear all caches
    CACHE_FACTORY.clear_all_caches()

    # Also clear the backing dictionaries directly for safety
    _MODEL_SCHEMA_CACHE_DICT.clear()
    _MODEL_CACHE_DICT.clear()
    _DYNAMIC_SCHEMA_CACHE_DICT.clear()
    _REQUEST_DATA_CACHE_DICT.clear()
    _PARAM_DETECTION_CACHE_DICT.clear()
    _OPENAPI_PARAMS_CACHE_DICT.clear()
    _METADATA_CACHE_DICT.clear()

    # Clear other caches that aren't managed by the factory
    REQPARSE_CACHE.clear()
    FUNCTION_METADATA_CACHE.clear()
    _I18N_CACHE.clear()

    # Clear lru_cache decorated functions
    import contextlib

    # Use contextlib.suppress to ignore AttributeError
    with contextlib.suppress(AttributeError):
        # If caching is disabled, cache_clear won't exist
        extract_param_types.cache_clear()  # type: ignore[attr-defined]

    # Clear utils module caches
    from .utils import clear_i18n_cache, clear_references_cache, process_i18n_value

    clear_references_cache()
    clear_i18n_cache()
    # Use contextlib.suppress to ignore AttributeError
    with contextlib.suppress(AttributeError):
        # If caching is disabled, cache_clear won't exist
        process_i18n_value.cache_clear()  # type: ignore[attr-defined]

    # Force garbage collection to ensure all references are cleaned up
    gc.collect()

    # Log cache stats after clearing
    logger.debug(f"Cache stats after clearing: {get_cache_stats()}")


def get_cache_stats() -> dict[str, Any]:
    """Get statistics about cache usage.

    Returns:
        Dictionary with detailed cache statistics including:
        - Size of each cache
        - Hit/miss rates for cache strategies
        - Overall memory usage estimation

    """
    # Get statistics from the cache factory
    factory_stats = CACHE_FACTORY.get_cache_stats()

    # Get sizes of regular dictionary caches not managed by the factory
    stats = {
        "function_metadata": len(FUNCTION_METADATA_CACHE),
        "reqparse": len(REQPARSE_CACHE),
        "i18n_cache": len(_I18N_CACHE),
    }

    # Add factory statistics
    stats.update(factory_stats)

    # Calculate total entries across all caches
    total_entries = stats["function_metadata"] + stats["reqparse"] + stats["i18n_cache"]

    # Add sizes from factory-managed caches
    for cache_name, cache_stats in stats.items():
        # Skip non-dictionary entries and entries without current_size
        if not isinstance(cache_stats, dict) or "current_size" not in cache_stats:
            continue

        # Skip known non-factory caches
        if cache_name in ["function_metadata", "reqparse", "i18n_cache"]:
            continue

        total_entries += cache_stats["current_size"]

    stats["total_entries"] = total_entries

    # Get configuration from the factory
    # We use a helper function to avoid accessing private members directly
    from .config import CacheConfig, get_cache_config

    # Get the current cache configuration
    config: CacheConfig = get_cache_config()
    stats["config"] = {
        "enabled": config.enabled,
        "schema_cache_enabled": config.schema_cache_enabled,
        "param_binding_cache_enabled": config.param_binding_cache_enabled,
        "model_cache_enabled": config.model_cache_enabled,
        "metadata_cache_enabled": config.metadata_cache_enabled,
        "max_cache_size": config.max_cache_size,
        "ttl_cache_duration": config.ttl_cache_duration,
    }

    return stats


def warmup_cache(models: list[type[BaseModel]] | None = None) -> dict[str, Any]:
    """Preload common data into caches to improve initial performance.

    This function preloads frequently used data into caches to avoid
    cold-start performance issues. It can be called during application
    initialization to prepare caches for use.

    Args:
        models: List of Pydantic models to preload into schema cache

    Returns:
        Dictionary with statistics about the warmup operation

    """
    from flask_x_openapi_schema.core.logger import get_logger

    logger = get_logger(__name__)
    logger.info("Warming up caches")

    stats = {
        "models_processed": 0,
        "schemas_generated": 0,
        "time_taken": 0,
    }

    if not models:
        logger.info("No models provided for cache warmup")
        return stats

    import time

    start_time = time.time()

    # Get cache strategies
    model_schema_cache = get_model_schema_cache()
    model_cache = get_model_cache()

    # Process models to generate and cache schemas
    for model in models:
        if not hasattr(model, "model_fields"):
            logger.warning(f"Skipping non-Pydantic model: {model}")
            continue

        # Generate and cache schema
        from .schema_generator import pydantic_to_openapi_schema

        schema = pydantic_to_openapi_schema(model)

        # Store in cache
        model_key = id(model)
        model_schema_cache.set(model_key, schema)

        # Extract and cache field types
        model_types = {field_name: field.annotation for field_name, field in model.model_fields.items()}
        model_cache.set(model_key, model_types)

        stats["models_processed"] += 1
        stats["schemas_generated"] += 1

    # Calculate time taken
    stats["time_taken"] = time.time() - start_time

    logger.info(f"Cache warmup completed in {stats['time_taken']:.2f} seconds")
    logger.info(f"Processed {stats['models_processed']} models")
    logger.info(f"Generated {stats['schemas_generated']} schemas")

    return stats


def make_cache_key(*args: Any, **kwargs: Any) -> tuple:
    """Create a consistent cache key from arguments.

    This helper function creates a hashable cache key from a mix of
    arguments, handling common unhashable types appropriately.

    Args:
        *args: Positional arguments to include in the key
        **kwargs: Keyword arguments to include in the key

    Returns:
        A hashable tuple to use as a cache key

    """
    from flask_x_openapi_schema.core.logger import get_logger

    logger = get_logger(__name__)
    logger.debug(f"Creating cache key for args={args}, kwargs={kwargs}")

    def make_hashable(obj):  # noqa: ANN001, ANN202
        """Convert an object to a hashable representation."""
        if isinstance(obj, dict):
            # Convert dict to sorted tuple of items with hashable values
            return tuple(sorted((k, make_hashable(v)) for k, v in obj.items()))
        if isinstance(obj, (list, tuple)):
            # Convert list/tuple to tuple with hashable values
            return tuple(make_hashable(x) for x in obj)
        if isinstance(obj, (str, int, float, bool, type(None))):
            # These types are already hashable
            return obj
        if hasattr(obj, "__dict__"):
            # Use object's id for objects
            return f"obj:{id(obj)}"
        # For any other type, use string representation and id
        return f"{type(obj).__name__}:{id(obj)}"

    # Process positional args
    key_parts = [make_hashable(arg) for arg in args]

    # Process keyword args (sorted by key)
    if kwargs:
        sorted_items = sorted(kwargs.items())
        for k, v in sorted_items:
            key_parts.append((k, make_hashable(v)))

    result = tuple(key_parts)
    logger.debug(f"Created cache key: {result}")

    return result
