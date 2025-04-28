"""Example demonstrating the new cache strategy pattern.

This example shows how to use the new cache strategy pattern in flask_x_openapi_schema.
It demonstrates how to configure caching behavior and measure performance.
"""

import time

from flask import Blueprint, Flask
from flask.views import MethodView
from pydantic import BaseModel, Field
from rich.console import Console
from rich.table import Table

from flask_x_openapi_schema import (
    CacheConfig,
    clear_all_caches,
    configure_cache,
    get_cache_config,
)
from flask_x_openapi_schema.core.cache_factory import CACHE_FACTORY, CacheType
from flask_x_openapi_schema.x.flask import OpenAPIMethodViewMixin, openapi_metadata
from flask_x_openapi_schema.x.flask.views import generate_openapi_schema

# Create console for rich output
console = Console()


# Define Pydantic models
class ItemQuery(BaseModel):
    """Query parameters for item search."""

    name: str | None = Field(None, description="Filter by name")
    category: str | None = Field(None, description="Filter by category")
    limit: int = Field(10, description="Maximum number of items to return")
    offset: int = Field(0, description="Number of items to skip")


class ItemResponse(BaseModel):
    """Response model for an item."""

    id: int = Field(..., description="Item ID")
    name: str = Field(..., description="Item name")
    description: str | None = Field(None, description="Item description")
    price: float = Field(..., description="Item price")
    category: str = Field(..., description="Item category")


class ItemsResponse(BaseModel):
    """Response model for a list of items."""

    items: list[ItemResponse] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")


# Define a MethodView with OpenAPI metadata
class ItemsView(OpenAPIMethodViewMixin, MethodView):
    """API for managing items."""

    @openapi_metadata(
        summary="Get all items",
        description="Get a list of items with optional filtering",
    )
    def get(self, _x_query_params: ItemQuery = None) -> ItemsResponse:
        """Get a list of items with optional filtering."""
        # In a real application, this would query a database
        items = [
            ItemResponse(
                id=1,
                name="Item 1",
                description="Description for Item 1",
                price=10.99,
                category="Category A",
            ),
            ItemResponse(
                id=2,
                name="Item 2",
                description="Description for Item 2",
                price=20.99,
                category="Category B",
            ),
        ]
        return ItemsResponse(items=items, total=len(items))


# Create Flask app and blueprint
app = Flask(__name__)
blueprint = Blueprint("api", __name__, url_prefix="/api")

# Register the view
ItemsView.register_to_blueprint(blueprint, "/items", "items")
app.register_blueprint(blueprint)


def demonstrate_cache_strategies() -> None:
    """Demonstrate the different cache strategies."""
    console.rule("[bold green]Cache Strategy Pattern Examples")

    # Show current cache configuration
    current_config = get_cache_config()
    console.print("[bold]Current Cache Configuration:[/bold]")
    console.print(f"Enabled: {current_config.enabled}")
    console.print(f"Schema Cache Enabled: {current_config.schema_cache_enabled}")
    console.print(f"Parameter Binding Cache Enabled: {current_config.param_binding_cache_enabled}")
    console.print(f"Model Cache Enabled: {current_config.model_cache_enabled}")
    console.print(f"Metadata Cache Enabled: {current_config.metadata_cache_enabled}")

    # Example 1: Using the cache factory directly
    console.print("\n[bold]Example 1: Using the cache factory directly[/bold]")

    # Create a test cache using the factory
    test_dict = {}
    test_cache = CACHE_FACTORY.get_cache_strategy(CacheType.GENERAL, test_dict, "test_cache", 100)

    # Use the cache
    test_cache.set("key1", "value1")
    test_cache.set("key2", "value2")

    console.print(f"Cache contains key1: {test_cache.contains('key1')}")
    console.print(f"Cache value for key1: {test_cache.get('key1')}")
    console.print(f"Cache size: {test_cache.size()}")
    console.print(f"Cache stats: {test_cache.get_stats()}")

    # Example 2: Disabling specific cache types
    console.print("\n[bold]Example 2: Disabling specific cache types[/bold]")

    # Configure cache to disable schema caching
    configure_cache(
        CacheConfig(
            enabled=True,
            schema_cache_enabled=False,
            param_binding_cache_enabled=True,
            model_cache_enabled=True,
            metadata_cache_enabled=True,
        )
    )

    # Check if schema cache is enabled
    is_schema_enabled = CACHE_FACTORY.is_cache_enabled(CacheType.SCHEMA)
    is_param_binding_enabled = CACHE_FACTORY.is_cache_enabled(CacheType.PARAM_BINDING)

    console.print(f"Schema cache enabled: {is_schema_enabled}")
    console.print(f"Parameter binding cache enabled: {is_param_binding_enabled}")

    # Create caches for different types
    schema_cache = CACHE_FACTORY.get_cache_strategy(CacheType.SCHEMA, {}, "schema_test", 100)
    param_cache = CACHE_FACTORY.get_cache_strategy(CacheType.PARAM_BINDING, {}, "param_test", 100)

    # Use the caches
    schema_cache.set("key", "value")
    param_cache.set("key", "value")

    console.print(f"Schema cache contains key: {schema_cache.contains('key')}")
    console.print(f"Schema cache value for key: {schema_cache.get('key')}")
    console.print(f"Parameter cache contains key: {param_cache.contains('key')}")
    console.print(f"Parameter cache value for key: {param_cache.get('key')}")

    # Reset to default configuration
    configure_cache(CacheConfig())
    console.print("\n[bold]Reset to default configuration[/bold]")


def measure_performance() -> None:
    """Measure performance with different cache configurations."""
    console.rule("[bold green]Performance Comparison")

    iterations = 100

    # Measure with all caches enabled
    configure_cache(CacheConfig(enabled=True))
    clear_all_caches()

    console.print("[bold]Testing with all caches enabled:[/bold]")
    start_time = time.time()
    for _ in range(iterations):
        generate_openapi_schema(blueprint)
    all_enabled_time = time.time() - start_time

    # Measure with schema cache disabled
    configure_cache(
        CacheConfig(
            enabled=True,
            schema_cache_enabled=False,
            param_binding_cache_enabled=True,
        )
    )
    clear_all_caches()

    console.print("[bold]Testing with schema cache disabled:[/bold]")
    start_time = time.time()
    for _ in range(iterations):
        generate_openapi_schema(blueprint)
    schema_disabled_time = time.time() - start_time

    # Measure with parameter binding cache disabled
    configure_cache(
        CacheConfig(
            enabled=True,
            schema_cache_enabled=True,
            param_binding_cache_enabled=False,
        )
    )
    clear_all_caches()

    console.print("[bold]Testing with parameter binding cache disabled:[/bold]")
    start_time = time.time()
    for _ in range(iterations):
        generate_openapi_schema(blueprint)
    param_disabled_time = time.time() - start_time

    # Measure with all caches disabled
    configure_cache(CacheConfig(enabled=False))
    clear_all_caches()

    console.print("[bold]Testing with all caches disabled:[/bold]")
    start_time = time.time()
    for _ in range(iterations):
        generate_openapi_schema(blueprint)
    all_disabled_time = time.time() - start_time

    # Create a table to display results
    table = Table(title=f"Schema Generation Performance ({iterations} iterations)")
    table.add_column("Configuration", style="cyan")
    table.add_column("Time (seconds)", style="green")
    table.add_column("Iterations/second", style="yellow")
    table.add_column("Relative Speed", style="magenta")

    # Add rows for each configuration
    table.add_row(
        "All Caches Enabled",
        f"{all_enabled_time:.4f}",
        f"{iterations / all_enabled_time:.2f}",
        "1.00x",
    )
    table.add_row(
        "Schema Cache Disabled",
        f"{schema_disabled_time:.4f}",
        f"{iterations / schema_disabled_time:.2f}",
        f"{schema_disabled_time / all_enabled_time:.2f}x slower",
    )
    table.add_row(
        "Parameter Binding Cache Disabled",
        f"{param_disabled_time:.4f}",
        f"{iterations / param_disabled_time:.2f}",
        f"{param_disabled_time / all_enabled_time:.2f}x slower",
    )
    table.add_row(
        "All Caches Disabled",
        f"{all_disabled_time:.4f}",
        f"{iterations / all_disabled_time:.2f}",
        f"{all_disabled_time / all_enabled_time:.2f}x slower",
    )

    console.print(table)

    # Reset to default configuration
    configure_cache(CacheConfig())


if __name__ == "__main__":
    console.print("[bold blue]Flask-X-OpenAPI-Schema Cache Strategy Pattern Examples[/bold blue]")

    demonstrate_cache_strategies()
    measure_performance()

    console.print("[bold green]All examples completed successfully![/bold green]")
