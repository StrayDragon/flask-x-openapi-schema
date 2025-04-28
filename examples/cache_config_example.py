"""Example demonstrating cache configuration options.

This example shows how to configure caching behavior in flask_x_openapi_schema.
It demonstrates enabling/disabling different types of caches and measuring performance.
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


def measure_schema_generation(iterations: int = 10) -> tuple[float, float]:
    """Measure schema generation performance with and without caching.

    Args:
        iterations: Number of iterations to run

    Returns:
        Tuple of (cached_time, uncached_time) in seconds
    """
    # First run with caching enabled (default)
    console.print("[bold]Testing with caching enabled:[/bold]")
    clear_all_caches()  # Start with clean caches

    # Configure cache with caching enabled
    configure_cache(
        CacheConfig(
            enabled=True,
        )
    )

    # Warm up
    generate_openapi_schema(blueprint)

    # Measure with caching
    start_time = time.time()
    for _ in range(iterations):
        generate_openapi_schema(blueprint)
    cached_time = time.time() - start_time

    # Cache stats no longer available in simplified cache system
    console.print("Cache stats no longer available in simplified cache system")

    # Now run with caching disabled
    console.print("\n[bold]Testing with caching disabled:[/bold]")
    clear_all_caches()

    # Configure cache with all caches disabled
    configure_cache(
        CacheConfig(
            enabled=False,
        )
    )

    # Measure without caching
    start_time = time.time()
    for _ in range(iterations):
        generate_openapi_schema(blueprint)
    uncached_time = time.time() - start_time

    return cached_time, uncached_time


def demonstrate_cache_config() -> None:
    """Demonstrate different cache configurations."""
    console.rule("[bold green]Cache Configuration Examples")

    # Show current cache configuration
    current_config = get_cache_config()
    console.print("[bold]Current Cache Configuration:[/bold]")
    console.print(f"Enabled: {current_config.enabled}")

    # Example 1: Disable all caching
    console.print("\n[bold]Example 1: Disable all caching[/bold]")
    configure_cache(CacheConfig(enabled=False))
    console.print(f"All caching disabled: {get_cache_config().enabled}")

    # Example 2: Enable caching
    console.print("\n[bold]Example 2: Enable caching[/bold]")
    configure_cache(
        CacheConfig(
            enabled=True,
        )
    )
    config = get_cache_config()
    console.print(f"Caching enabled: {config.enabled}")

    # Reset to default configuration
    configure_cache(CacheConfig())
    console.print("\n[bold]Reset to default configuration[/bold]")


def demonstrate_performance() -> None:
    """Demonstrate performance impact of caching."""
    console.rule("[bold green]Performance Comparison")

    # Measure schema generation performance
    iterations = 100
    cached_time, uncached_time = measure_schema_generation(iterations)

    # Create a table to display results
    table = Table(title=f"Schema Generation Performance ({iterations} iterations)")
    table.add_column("Configuration", style="cyan")
    table.add_column("Time (seconds)", style="green")
    table.add_column("Iterations/second", style="yellow")

    # Add rows for each configuration
    table.add_row(
        "With Caching",
        f"{cached_time:.4f}",
        f"{iterations / cached_time:.2f}",
    )
    table.add_row(
        "Without Caching",
        f"{uncached_time:.4f}",
        f"{iterations / uncached_time:.2f}",
    )
    table.add_row(
        "Speedup",
        f"{uncached_time / cached_time:.2f}x",
        "",
    )

    console.print(table)


if __name__ == "__main__":
    console.print("[bold blue]Flask-X-OpenAPI-Schema Cache Configuration Examples[/bold blue]")

    demonstrate_cache_config()
    demonstrate_performance()

    console.print("[bold green]All examples completed successfully![/bold green]")
