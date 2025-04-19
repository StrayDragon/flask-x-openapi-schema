"""
Comprehensive benchmark for flask_x_openapi_schema.

This script benchmarks various aspects of the library to identify performance bottlenecks.
"""

import time
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from rich.console import Console
from rich.table import Table

from pydantic import BaseModel, Field

from flask_x_openapi_schema.decorators import openapi_metadata
from flask_x_openapi_schema.schema_generator import OpenAPISchemaGenerator
from flask_x_openapi_schema.utils import pydantic_to_openapi_schema

# Set up rich console for pretty output
console = Console()


# Define models for testing
class SimpleModel(BaseModel):
    """A simple model with a few fields."""

    name: str = Field(..., description="The name")
    value: int = Field(..., description="The value")


class ComplexModel(BaseModel):
    """A more complex model with nested fields."""

    id: str = Field(..., description="The ID")
    name: str = Field(..., description="The name")
    values: List[int] = Field(..., description="List of values")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata")
    nested: Optional[SimpleModel] = Field(None, description="Nested model")


class VeryComplexModel(BaseModel):
    """A very complex model with multiple nested fields."""

    id: str = Field(..., description="The ID")
    name: str = Field(..., description="The name")
    items: List[ComplexModel] = Field(
        default_factory=list, description="List of complex items"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata")
    tags: List[str] = Field(default_factory=list, description="Tags")
    status: str = Field("active", description="Status")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Update timestamp")


@dataclass
class BenchmarkResult:
    """Results of a benchmark run."""

    name: str
    iterations: int
    total_time: float
    avg_time: float

    @property
    def operations_per_second(self) -> float:
        """Calculate operations per second."""
        return self.iterations / self.total_time if self.total_time > 0 else 0


def benchmark(name: str, func, iterations: int = 1000) -> BenchmarkResult:
    """Run a benchmark on a function."""
    console.print(f"Running benchmark: [bold]{name}[/bold]...")

    # Warm up
    for _ in range(5):
        func()

    # Actual benchmark
    start_time = time.time()
    for _ in range(iterations):
        func()
    end_time = time.time()

    total_time = end_time - start_time
    avg_time = total_time / iterations

    result = BenchmarkResult(
        name=name, iterations=iterations, total_time=total_time, avg_time=avg_time
    )

    console.print(f"  Completed {iterations} iterations in {total_time:.4f} seconds")
    console.print(f"  Average time: {avg_time * 1000:.4f} ms per operation")
    console.print(f"  Operations per second: {result.operations_per_second:.2f}")

    return result


def benchmark_pydantic_to_openapi_conversion():
    """Benchmark Pydantic model to OpenAPI schema conversion."""
    # Simple model conversion
    simple_result = benchmark(
        "Simple model conversion",
        lambda: pydantic_to_openapi_schema(SimpleModel),
        iterations=1000,
    )

    # Complex model conversion
    complex_result = benchmark(
        "Complex model conversion",
        lambda: pydantic_to_openapi_schema(ComplexModel),
        iterations=1000,
    )

    # Very complex model conversion
    very_complex_result = benchmark(
        "Very complex model conversion",
        lambda: pydantic_to_openapi_schema(VeryComplexModel),
        iterations=1000,
    )

    return [simple_result, complex_result, very_complex_result]


def benchmark_decorator_creation():
    """Benchmark the creation of decorated functions."""

    # Simple decorator
    def create_simple_decorator():
        @openapi_metadata(summary="Simple endpoint", tags=["test"])
        def simple_endpoint():
            return {"result": "ok"}

        return simple_endpoint

    simple_result = benchmark(
        "Simple decorator creation", create_simple_decorator, iterations=1000
    )

    # Complex decorator with request body
    def create_complex_decorator():
        @openapi_metadata(
            summary="Complex endpoint",
            description="A more complex endpoint",
            tags=["test"],
            request_body=SimpleModel,
            responses={
                "200": {
                    "description": "Success",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/SimpleModel"}
                        }
                    },
                }
            },
        )
        def complex_endpoint(x_request_body: SimpleModel):
            return {"result": "ok"}

        return complex_endpoint

    complex_result = benchmark(
        "Complex decorator creation", create_complex_decorator, iterations=1000
    )

    # Very complex decorator with multiple parameters
    def create_very_complex_decorator():
        @openapi_metadata(
            summary="Very complex endpoint",
            description="A very complex endpoint with multiple parameters",
            tags=["test"],
            request_body=ComplexModel,
            query_model=SimpleModel,
            responses={
                "200": {
                    "description": "Success",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ComplexModel"}
                        }
                    },
                },
                "400": {"description": "Bad request"},
                "404": {"description": "Not found"},
            },
        )
        def very_complex_endpoint(
            x_request_body: ComplexModel,
            x_request_query: SimpleModel,
            x_request_path_id: str,
        ):
            return {"result": "ok"}

        return very_complex_endpoint

    very_complex_result = benchmark(
        "Very complex decorator creation",
        create_very_complex_decorator,
        iterations=1000,
    )

    return [simple_result, complex_result, very_complex_result]


def benchmark_schema_generation():
    """Benchmark OpenAPI schema generation."""

    # Simple schema generation
    def generate_simple_schema():
        generator = OpenAPISchemaGenerator(title="Simple API", version="1.0.0")
        return generator.generate_schema()

    simple_result = benchmark(
        "Simple schema generation", generate_simple_schema, iterations=1000
    )

    # Complex schema generation with models
    def generate_complex_schema():
        generator = OpenAPISchemaGenerator(
            title="Complex API", version="1.0.0", description="A more complex API"
        )
        # Register models
        generator._register_model(SimpleModel)
        generator._register_model(ComplexModel)
        return generator.generate_schema()

    complex_result = benchmark(
        "Complex schema generation", generate_complex_schema, iterations=1000
    )

    # Very complex schema generation with many models and paths
    def generate_very_complex_schema():
        generator = OpenAPISchemaGenerator(
            title="Very Complex API",
            version="1.0.0",
            description="A very complex API with many models and paths",
        )
        # Register models
        generator._register_model(SimpleModel)
        generator._register_model(ComplexModel)
        generator._register_model(VeryComplexModel)

        # Add paths
        generator.paths["/api/simple"] = {
            "get": {
                "summary": "Get simple data",
                "responses": {
                    "200": {
                        "description": "Success",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/SimpleModel"}
                            }
                        },
                    }
                },
            }
        }

        generator.paths["/api/complex"] = {
            "post": {
                "summary": "Create complex data",
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ComplexModel"}
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "Created",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ComplexModel"}
                            }
                        },
                    }
                },
            }
        }

        generator.paths["/api/very-complex"] = {
            "post": {
                "summary": "Create very complex data",
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/VeryComplexModel"}
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "Created",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/VeryComplexModel"
                                }
                            }
                        },
                    }
                },
            }
        }

        return generator.generate_schema()

    very_complex_result = benchmark(
        "Very complex schema generation", generate_very_complex_schema, iterations=1000
    )

    return [simple_result, complex_result, very_complex_result]


def create_results_table(results: List[BenchmarkResult], title: str) -> Table:
    """Create a rich table from benchmark results."""
    table = Table(title=title)
    table.add_column("Benchmark", style="cyan")
    table.add_column("Iterations", style="green")
    table.add_column("Total Time (s)", style="yellow")
    table.add_column("Avg Time (ms)", style="yellow")
    table.add_column("Ops/sec", style="red")

    for result in results:
        table.add_row(
            result.name,
            str(result.iterations),
            f"{result.total_time:.4f}",
            f"{result.avg_time * 1000:.4f}",
            f"{result.operations_per_second:.2f}",
        )

    return table


def run_all_benchmarks():
    """Run all benchmarks and display results."""
    console.print(
        "[bold]Starting comprehensive benchmarks for flask_x_openapi_schema...[/bold]"
    )

    # Run benchmarks
    console.print("\n[bold]1. Pydantic to OpenAPI Schema Conversion[/bold]")
    conversion_results = benchmark_pydantic_to_openapi_conversion()

    console.print("\n[bold]2. Decorator Creation[/bold]")
    decorator_results = benchmark_decorator_creation()

    console.print("\n[bold]3. Schema Generation[/bold]")
    schema_results = benchmark_schema_generation()

    # Display summary tables
    console.print("\n[bold]Summary Tables[/bold]")

    console.print(
        create_results_table(
            conversion_results, "Pydantic to OpenAPI Schema Conversion"
        )
    )

    console.print(create_results_table(decorator_results, "Decorator Creation"))

    console.print(create_results_table(schema_results, "Schema Generation"))

    # Overall recommendations
    console.print("\n[bold]Performance Analysis and Recommendations:[/bold]")

    # Identify the slowest operations
    all_results = conversion_results + decorator_results + schema_results
    slowest_ops = sorted(all_results, key=lambda x: x.avg_time, reverse=True)[:3]

    console.print("[bold]Slowest Operations:[/bold]")
    for i, result in enumerate(slowest_ops, 1):
        console.print(
            f"{i}. {result.name}: {result.avg_time * 1000:.4f} ms per operation"
        )

    # Provide recommendations based on the results
    console.print("\n[bold]Recommendations:[/bold]")
    console.print(
        "1. Consider caching schema generation results for frequently used models"
    )
    console.print(
        "2. Optimize the decorator creation process, especially for complex endpoints"
    )
    console.print(
        "3. Look for opportunities to reduce redundant processing in schema generation"
    )
    console.print("4. Consider lazy loading of OpenAPI schemas to improve startup time")


if __name__ == "__main__":
    # Install rich if not already installed
    try:
        import rich
    except ImportError:
        import subprocess
        import sys

        print("Installing rich package for pretty output...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "rich"])
        print("Rich installed successfully!")

    run_all_benchmarks()
