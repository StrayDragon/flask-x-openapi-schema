"""Cache factory for creating cache strategies.

This module provides a factory for creating cache strategies based on configuration.
It centralizes the logic for determining which cache strategy to use.
"""

import threading
from enum import Enum, auto
from typing import Any, TypeVar

from .cache_strategy import ActiveCacheStrategy, NullCacheStrategy

# Type variables
K = TypeVar("K")
V = TypeVar("V")


class CacheType(Enum):
    """Enumeration of cache types."""

    SCHEMA = auto()
    PARAM_BINDING = auto()
    MODEL = auto()
    METADATA = auto()
    GENERAL = auto()


class CacheFactory:
    """Factory for creating cache strategies.

    This class is responsible for creating the appropriate cache strategy
    based on the current configuration.
    """

    def __init__(self) -> None:
        """Initialize the cache factory."""
        self._cache_enabled = True
        self._schema_cache_enabled = True
        self._param_binding_cache_enabled = True
        self._model_cache_enabled = True
        self._metadata_cache_enabled = True
        self._max_cache_size = 1000
        self._ttl_cache_duration = 300
        self._lock = threading.RLock()
        self._cache_instances: dict[str, Any] = {}

    def update_config(
        self,
        cache_enabled: bool = True,
        schema_cache_enabled: bool = True,
        param_binding_cache_enabled: bool = True,
        model_cache_enabled: bool = True,
        metadata_cache_enabled: bool = True,
        max_cache_size: int = 1000,
        ttl_cache_duration: int = 300,
    ) -> None:
        """Update the cache configuration.

        Args:
            cache_enabled: Global flag to enable/disable all caching
            schema_cache_enabled: Enable caching for OpenAPI schema generation
            param_binding_cache_enabled: Enable caching for parameter binding
            model_cache_enabled: Enable caching for Pydantic model schemas
            metadata_cache_enabled: Enable caching for OpenAPI metadata
            max_cache_size: Maximum size for regular dictionary caches
            ttl_cache_duration: Default TTL for cache entries in seconds

        """
        with self._lock:
            self._cache_enabled = cache_enabled
            self._schema_cache_enabled = schema_cache_enabled
            self._param_binding_cache_enabled = param_binding_cache_enabled
            self._model_cache_enabled = model_cache_enabled
            self._metadata_cache_enabled = metadata_cache_enabled
            self._max_cache_size = max_cache_size
            self._ttl_cache_duration = ttl_cache_duration

    def is_cache_enabled(self, cache_type: CacheType) -> bool:
        """Check if a specific cache type is enabled.

        Args:
            cache_type: Type of cache to check

        Returns:
            True if the cache type is enabled, False otherwise

        """
        if not self._cache_enabled:
            return False

        if cache_type == CacheType.SCHEMA:
            return self._schema_cache_enabled
        if cache_type == CacheType.PARAM_BINDING:
            return self._param_binding_cache_enabled
        if cache_type == CacheType.MODEL:
            return self._model_cache_enabled
        if cache_type == CacheType.METADATA:
            return self._metadata_cache_enabled
        return True  # General caching is enabled by default

    def get_cache_strategy(
        self, cache_type: CacheType, backing_cache: dict[K, V], name: str, max_size: int | None = None
    ) -> Any:
        """Get a cache strategy for the specified cache type.

        Args:
            cache_type: Type of cache to get
            backing_cache: Dictionary to use for caching
            name: Name of the cache (for reuse)
            max_size: Maximum size of the cache (defaults to global setting)

        Returns:
            A cache strategy (active or null)

        """
        cache_key = f"{name}_{cache_type.name}"

        with self._lock:
            # Check if we already have a cache instance for this key
            if cache_key in self._cache_instances:
                return self._cache_instances[cache_key]

            # Create a new cache instance
            if self.is_cache_enabled(cache_type):
                strategy = ActiveCacheStrategy(
                    backing_cache=backing_cache,
                    max_size=max_size or self._max_cache_size,
                    lock=threading.RLock(),
                )
            else:
                strategy = NullCacheStrategy()

            # Store the cache instance for reuse
            self._cache_instances[cache_key] = strategy
            return strategy

    def clear_all_caches(self) -> None:
        """Clear all cache instances."""
        with self._lock:
            for cache in self._cache_instances.values():
                cache.clear()

    def get_cache_stats(self) -> dict[str, Any]:
        """Get statistics about all cache instances.

        Returns:
            Dictionary with cache statistics

        """
        with self._lock:
            stats = {}
            for name, cache in self._cache_instances.items():
                stats[name] = cache.get_stats()
            return stats


# Create a singleton instance
CACHE_FACTORY = CacheFactory()
