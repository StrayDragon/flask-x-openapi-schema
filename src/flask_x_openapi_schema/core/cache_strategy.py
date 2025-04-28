"""Cache strategy implementations.

This module provides different cache strategy implementations using the Strategy pattern.
It allows for different caching behaviors without conditional logic at each cache usage point.
"""

import threading
from abc import ABC, abstractmethod
from collections.abc import Callable
from functools import lru_cache, wraps
from typing import Any, Generic, Optional, TypeVar, cast

# Type variables
K = TypeVar("K")
V = TypeVar("V")
F = TypeVar("F", bound=Callable[..., Any])


class CacheStrategy(Generic[K, V], ABC):
    """Abstract base class for cache strategies."""

    @abstractmethod
    def get(self, key: K) -> V | None:
        """Get a value from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found or disabled

        """

    @abstractmethod
    def set(self, key: K, value: V) -> None:
        """Set a value in the cache.

        Args:
            key: Cache key
            value: Value to cache

        """

    @abstractmethod
    def clear(self) -> None:
        """Clear the cache."""

    @abstractmethod
    def contains(self, key: K) -> bool:
        """Check if a key exists in the cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise

        """

    @abstractmethod
    def remove(self, key: K) -> bool:
        """Remove a key from the cache.

        Args:
            key: Cache key

        Returns:
            True if key was removed, False if key was not in cache

        """

    @abstractmethod
    def size(self) -> int:
        """Get the current size of the cache.

        Returns:
            Number of items in the cache

        """

    @abstractmethod
    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics

        """

    @abstractmethod
    def function_cache_decorator(self, func: F) -> F:
        """Create a function decorator that uses this cache strategy.

        Args:
            func: Function to decorate

        Returns:
            Decorated function

        """


class ActiveCacheStrategy(Generic[K, V]):
    """Active cache strategy that actually caches values.

    This strategy implements caching using a backing cache implementation.
    """

    def __init__(self, backing_cache: dict[K, V], max_size: int = 1000, lock: Optional[threading.RLock] = None) -> None:  # noqa: UP007
        """Initialize the active cache strategy.

        Args:
            backing_cache: Dictionary to use for caching
            max_size: Maximum size of the cache
            lock: Optional lock for thread safety

        """
        self._cache = backing_cache
        self._max_size = max_size
        self._lock = lock or threading.RLock()
        self._hits = 0
        self._misses = 0

    def get(self, key: K) -> V | None:
        """Get a value from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found

        """
        with self._lock:
            if key in self._cache:
                self._hits += 1
                return self._cache[key]
            self._misses += 1
            return None

    def set(self, key: K, value: V) -> None:
        """Set a value in the cache.

        Args:
            key: Cache key
            value: Value to cache

        """
        with self._lock:
            # Check if we need to evict items
            if len(self._cache) >= self._max_size and key not in self._cache:
                # Simple eviction: clear the cache if it's full
                self._cache.clear()
            self._cache[key] = value

    def clear(self) -> None:
        """Clear the cache."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def contains(self, key: K) -> bool:
        """Check if a key exists in the cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise

        """
        with self._lock:
            return key in self._cache

    def remove(self, key: K) -> bool:
        """Remove a key from the cache.

        Args:
            key: Cache key

        Returns:
            True if key was removed, False if key was not in cache

        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def size(self) -> int:
        """Get the current size of the cache.

        Returns:
            Number of items in the cache

        """
        with self._lock:
            return len(self._cache)

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
                "enabled": True,
            }

    def function_cache_decorator(self, func: F) -> F:
        """Create a function decorator that uses this cache strategy.

        Args:
            func: Function to decorate

        Returns:
            Decorated function

        """
        # Use lru_cache with appropriate size
        cached_func = lru_cache(maxsize=self._max_size)(func)

        # Add cache_clear method to the wrapped function
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return cached_func(*args, **kwargs)

        wrapper.cache_clear = cached_func.cache_clear
        return cast("F", wrapper)


class NullCacheStrategy(Generic[K, V]):
    """Null cache strategy that doesn't cache anything.

    This strategy implements the cache interface but doesn't actually cache anything.
    It's used when caching is disabled.
    """

    def get(self, key: K) -> V | None:  # noqa: ARG002
        """Get a value from the cache (always returns None).

        Args:
            key: Cache key

        Returns:
            None (caching disabled)

        """
        return None

    def set(self, key: K, value: V) -> None:
        """Set a value in the cache (does nothing).

        Args:
            key: Cache key
            value: Value to cache

        """

    def clear(self) -> None:
        """Clear the cache (does nothing)."""

    def contains(self, key: K) -> bool:  # noqa: ARG002
        """Check if a key exists in the cache (always False).

        Args:
            key: Cache key

        Returns:
            False (caching disabled)

        """
        return False

    def remove(self, key: K) -> bool:  # noqa: ARG002
        """Remove a key from the cache (always False).

        Args:
            key: Cache key

        Returns:
            False (caching disabled)

        """
        return False

    def size(self) -> int:
        """Get the current size of the cache (always 0).

        Returns:
            0 (caching disabled)

        """
        return 0

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics

        """
        return {
            "hits": 0,
            "misses": 0,
            "hit_rate": 0.0,
            "max_size": 0,
            "current_size": 0,
            "enabled": False,
        }

    def function_cache_decorator(self, func: F) -> F:
        """Create a function decorator that uses this cache strategy.

        Args:
            func: Function to decorate

        Returns:
            Original function (caching disabled)

        """
        return func
