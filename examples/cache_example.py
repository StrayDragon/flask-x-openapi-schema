"""Example demonstrating the cache functionality in flask-x-openapi-schema."""

import sys
import time

# Add the src directory to the path to avoid import issues
sys.path.insert(0, "/home/l8ng/Projects/__straydragon__/flask-x-openapi-schema/src")

from pydantic import BaseModel, Field
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from flask_x_openapi_schema.core.cache import (
    CacheEvictionPolicy,
    ThreadSafeCache,
    TTLCache,
    get_cache_stats,
    warmup_cache,
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


class PostModel(BaseModel):
    """Post model for demonstration."""

    id: int = Field(..., description="Post ID")
    title: str = Field(..., description="Post title")
    content: str = Field(..., description="Post content")
    author: UserModel = Field(..., description="Post author")
    tags: list[str] = Field(default_factory=list, description="Post tags")
    created_at: str = Field(..., description="Creation timestamp")


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


def demonstrate_cache_warmup():
    """Demonstrate cache warmup functionality."""
    console.rule("[bold green]Cache Warmup Demonstration")

    # Display initial cache stats
    console.print("[bold]Initial Cache Stats:[/bold]")
    rprint(get_cache_stats())

    # Warm up cache with models
    console.print("[bold]Warming up cache...[/bold]")
    start_time = time.time()
    stats = warmup_cache(models=[UserModel, PostModel])
    elapsed = time.time() - start_time

    # Display warmup results
    console.print(f"[bold]Cache warmed up in {elapsed:.4f} seconds[/bold]")
    rprint(f"Warmup Stats: {stats}")

    # Display cache stats after warmup
    console.print("[bold]Cache Stats After Warmup:[/bold]")
    rprint(get_cache_stats())

    # Demonstrate performance improvement
    console.print("[bold]Performance Comparison:[/bold]")

    # Time to generate schema without cache
    # Clear cache for accurate measurement
    from flask_x_openapi_schema import clear_all_caches
    from flask_x_openapi_schema.core.schema_generator import pydantic_to_openapi_schema

    clear_all_caches()

    # Measure cold start
    start_time = time.time()
    _ = pydantic_to_openapi_schema(PostModel)
    cold_time = time.time() - start_time

    # Measure warm start
    start_time = time.time()
    _ = pydantic_to_openapi_schema(PostModel)
    warm_time = time.time() - start_time

    # Display results
    console.print(f"Cold start time: {cold_time:.6f} seconds")
    console.print(f"Warm start time: {warm_time:.6f} seconds")
    console.print(f"Speedup factor: {cold_time / warm_time:.2f}x")


if __name__ == "__main__":
    console.print("[bold blue]Flask-X-OpenAPI-Schema Cache Examples[/bold blue]")

    demonstrate_thread_safe_cache()
    demonstrate_ttl_cache()
    demonstrate_cache_warmup()

    console.print("[bold green]All examples completed successfully![/bold green]")
