"""Simple example demonstrating the cache functionality."""

# Import directly from the cache module to avoid Flask import issues
import sys
import time

from pydantic import BaseModel, Field
from rich import print as rprint
from rich.console import Console
from rich.table import Table

sys.path.insert(0, "/home/l8ng/Projects/__straydragon__/flask-x-openapi-schema/src")
from flask_x_openapi_schema.core.cache import (
    CacheEvictionPolicy,
    ThreadSafeCache,
    TTLCache,
)

console = Console()


class UserModel(BaseModel):
    """User model for demonstration."""

    id: int = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    is_active: bool = Field(True, description="Whether the user is active")
    roles: list[str] = Field(default_factory=list, description="User roles")
    metadata: dict[str, str] | None = Field(None, description="User metadata")


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
    console.print("[bold blue]Flask-X-OpenAPI-Schema Cache Examples[/bold blue]")

    demonstrate_thread_safe_cache()
    demonstrate_ttl_cache()

    console.print("[bold green]All examples completed successfully![/bold green]")
