"""Standalone demonstration of cache implementations."""

import enum
import threading
import time
from collections import Counter, OrderedDict
from typing import Any, Generic, TypeVar

from rich import print as rprint
from rich.console import Console
from rich.table import Table

# Create console for rich output
console = Console()

# Type variables for cache values
K = TypeVar("K")
T = TypeVar("T")

# Default cache settings
MAX_CACHE_SIZE = 1000
DEFAULT_TTL = 300  # 5 minutes


class CacheEvictionPolicy(enum.Enum):
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
        self._cache: dict[K, T] = {}
        self._eviction_policy = eviction_policy

        # Data structures for different eviction policies
        if eviction_policy == CacheEvictionPolicy.LRU:
            self._access_order = OrderedDict()  # More efficient than list for LRU
        elif eviction_policy == CacheEvictionPolicy.LFU:
            self._access_count = Counter()  # Count access frequency
        elif eviction_policy == CacheEvictionPolicy.FIFO:
            self._insertion_order = []  # Track insertion order

    def get(self, key: K) -> T | None:
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

    def set(self, key: K, value: T) -> None:
        """Set a value in the cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        with self._lock:
            # Check if we need to evict items
            if len(self._cache) >= self._max_size and key not in self._cache:
                # Force eviction when cache is full
                self._evict_item()

                # Double-check that eviction actually happened
                if len(self._cache) >= self._max_size and self._cache:
                    # If eviction didn't work (e.g., due to empty tracking structures),
                    # remove any item to make space
                    # Remove first item we find
                    first_key = next(iter(self._cache))
                    self._cache.pop(first_key, None)

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
                self._insertion_order.append(key)

    def _evict_item(self) -> None:
        """Evict an item based on the current eviction policy."""
        if not self._cache:
            return

        if self._eviction_policy == CacheEvictionPolicy.LRU:
            # Remove least recently used item (first item in OrderedDict)
            if self._access_order:
                oldest_key, _ = self._access_order.popitem(last=False)
                self._cache.pop(oldest_key, None)

        elif self._eviction_policy == CacheEvictionPolicy.LFU:
            # Remove least frequently used item
            if self._access_count:
                # Get key with minimum access count that is in the cache
                valid_keys = [k for k in self._access_count if k in self._cache]
                if valid_keys:
                    # Find the key with minimum access count
                    least_used_key = min(valid_keys, key=lambda k: self._access_count[k])
                    self._cache.pop(least_used_key, None)
                    del self._access_count[least_used_key]

        elif self._eviction_policy == CacheEvictionPolicy.FIFO and self._insertion_order:
            # Remove oldest item (first in)
            oldest_key = self._insertion_order.pop(0)
            self._cache.pop(oldest_key, None)

    def contains(self, key: K) -> bool:
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
        self._expiry_times: dict[K, float] = {}

    def get(self, key: K) -> T | None:
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

    def set(self, key: K, value: T, ttl: int | None = None) -> None:
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

    def _remove_expired_entry(self, key: K) -> None:
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

    def remove(self, key: K) -> bool:
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


def demonstrate_thread_safe_cache():
    """Demonstrate ThreadSafeCache with different eviction policies."""
    console.rule("[bold green]ThreadSafeCache Demonstration")

    # Create caches with different eviction policies
    lru_cache = ThreadSafeCache[str, str](max_size=3, eviction_policy=CacheEvictionPolicy.LRU)
    lfu_cache = ThreadSafeCache[str, str](max_size=3, eviction_policy=CacheEvictionPolicy.LFU)
    fifo_cache = ThreadSafeCache[str, str](max_size=3, eviction_policy=CacheEvictionPolicy.FIFO)

    # Populate caches
    for cache in [lru_cache, lfu_cache, fifo_cache]:
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

    # Access patterns
    lru_cache.get("key1")  # Make key1 most recently used

    lfu_cache.get("key1")  # Increase frequency for key1
    lfu_cache.get("key1")
    lfu_cache.get("key2")  # Increase frequency for key2

    # Add new item to each cache, forcing eviction
    lru_cache.set("key4", "value4")  # Should evict key2 or key3 (least recently used)
    lfu_cache.set("key4", "value4")  # Should evict key3 (least frequently used)
    fifo_cache.set("key4", "value4")  # Should evict key1 (first in)

    # Create table to display results
    table = Table(title="Cache Eviction Policy Comparison")
    table.add_column("Key", style="cyan")
    table.add_column("LRU Cache", style="green")
    table.add_column("LFU Cache", style="yellow")
    table.add_column("FIFO Cache", style="red")

    # Add rows for each key
    for key in ["key1", "key2", "key3", "key4"]:
        table.add_row(
            key,
            "✅" if lru_cache.get(key) else "❌",
            "✅" if lfu_cache.get(key) else "❌",
            "✅" if fifo_cache.get(key) else "❌",
        )

    console.print(table)

    # Display cache statistics
    console.print("[bold]Cache Statistics:[/bold]")
    rprint(f"LRU Cache: {lru_cache.get_stats()}")
    rprint(f"LFU Cache: {lfu_cache.get_stats()}")
    rprint(f"FIFO Cache: {fifo_cache.get_stats()}")


def demonstrate_ttl_cache():
    """Demonstrate TTLCache with expiration."""
    console.rule("[bold green]TTLCache Demonstration")

    # Create TTL cache with short expiration
    ttl_cache = TTLCache[str, str](max_size=10, ttl=2)  # 2 seconds TTL

    # Add items with different TTLs
    ttl_cache.set("short_ttl", "This will expire quickly")
    ttl_cache.set("custom_ttl", "This will expire later", ttl=5)  # 5 seconds TTL

    # Display initial state
    console.print("[bold]Initial Cache State:[/bold]")
    rprint(f"short_ttl: {ttl_cache.get('short_ttl')}")
    rprint(f"custom_ttl: {ttl_cache.get('custom_ttl')}")
    rprint(f"Cache Stats: {ttl_cache.get_stats()}")

    # Wait for short TTL to expire
    console.print("[bold yellow]Waiting for short TTL to expire (2 seconds)...[/bold yellow]")
    time.sleep(2.1)

    # Display state after short TTL expires
    console.print("[bold]Cache State After Short TTL Expires:[/bold]")
    rprint(f"short_ttl: {ttl_cache.get('short_ttl')}")
    rprint(f"custom_ttl: {ttl_cache.get('custom_ttl')}")
    rprint(f"Cache Stats: {ttl_cache.get_stats()}")

    # Wait for custom TTL to expire
    console.print("[bold yellow]Waiting for custom TTL to expire (3 more seconds)...[/bold yellow]")
    time.sleep(3.1)

    # Display state after all TTLs expire
    console.print("[bold]Cache State After All TTLs Expire:[/bold]")
    rprint(f"short_ttl: {ttl_cache.get('short_ttl')}")
    rprint(f"custom_ttl: {ttl_cache.get('custom_ttl')}")
    rprint(f"Cache Stats: {ttl_cache.get_stats()}")


if __name__ == "__main__":
    console.print("[bold blue]Cache Implementation Examples[/bold blue]")

    demonstrate_thread_safe_cache()
    demonstrate_ttl_cache()

    console.print("[bold green]All examples completed successfully![/bold green]")
