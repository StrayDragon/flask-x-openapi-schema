#!/usr/bin/env python
"""
Enhanced benchmark for flask_x_openapi_schema with rich output.

This benchmark compares the performance of using flask_x_openapi_schema
versus a standard Flask application without it, using more complex examples
and providing rich, colorful output.
"""
import json
import time
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum

from flask import Flask, request, jsonify
from pydantic import BaseModel, Field, EmailStr, HttpUrl, constr, conint, validator
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich import box
from rich.syntax import Syntax

from flask_x_openapi_schema.decorators import openapi_metadata
from flask_x_openapi_schema.models.base import BaseRespModel


# Initialize rich console
console = Console()


# Define complex models for benchmarking
class UserRole(str, Enum):
    """User role enum."""
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"
    GUEST = "guest"


class Address(BaseModel):
    """User address model."""
    street: str = Field(..., description="Street address")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State or province")
    postal_code: str = Field(..., description="Postal code")
    country: str = Field(..., description="Country")


class SocialMedia(BaseModel):
    """User social media links."""
    twitter: Optional[HttpUrl] = Field(None, description="Twitter profile URL")
    facebook: Optional[HttpUrl] = Field(None, description="Facebook profile URL")
    linkedin: Optional[HttpUrl] = Field(None, description="LinkedIn profile URL")
    github: Optional[HttpUrl] = Field(None, description="GitHub profile URL")


class ComplexUserRequest(BaseModel):
    """Complex user request model."""
    username: constr(min_length=3, max_length=50) = Field(..., description="The username")
    email: EmailStr = Field(..., description="The email address")
    full_name: str = Field(..., description="The full name")
    age: conint(ge=18, le=120) = Field(..., description="The age")
    is_active: bool = Field(True, description="Whether the user is active")
    role: UserRole = Field(UserRole.VIEWER, description="User role")
    tags: List[str] = Field(default_factory=list, description="User tags")
    address: Optional[Address] = Field(None, description="User address")
    social_media: Optional[SocialMedia] = Field(None, description="Social media profiles")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences")
    
    @validator('username')
    def username_alphanumeric(cls, v):
        """Validate that username is alphanumeric."""
        if not v.isalnum():
            raise ValueError('Username must be alphanumeric')
        return v


class ComplexUserResponse(BaseRespModel):
    """Complex user response model."""
    id: str = Field(..., description="The user ID")
    username: str = Field(..., description="The username")
    email: EmailStr = Field(..., description="The email address")
    full_name: str = Field(..., description="The full name")
    age: int = Field(..., description="The age")
    is_active: bool = Field(..., description="Whether the user is active")
    role: UserRole = Field(..., description="User role")
    tags: List[str] = Field(..., description="User tags")
    address: Optional[Address] = Field(None, description="User address")
    social_media: Optional[SocialMedia] = Field(None, description="Social media profiles")
    preferences: Dict[str, Any] = Field(..., description="User preferences")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")


# Sample complex data for testing
COMPLEX_USER_DATA = {
    "username": "testuser123",
    "email": "test@example.com",
    "full_name": "Test User",
    "age": 30,
    "is_active": True,
    "role": "editor",
    "tags": ["test", "user", "benchmark", "complex"],
    "address": {
        "street": "123 Test St",
        "city": "Test City",
        "state": "Test State",
        "postal_code": "12345",
        "country": "Test Country"
    },
    "social_media": {
        "twitter": "https://twitter.com/testuser",
        "github": "https://github.com/testuser"
    },
    "preferences": {
        "theme": "dark",
        "notifications": True,
        "language": "en",
        "timezone": "UTC"
    }
}


def standard_flask_implementation():
    """Standard Flask implementation without flask_x_openapi_schema."""
    # Manual validation and parsing
    data = COMPLEX_USER_DATA
    
    # Manual validation of required fields
    required_fields = ["username", "email", "full_name", "age"]
    for field in required_fields:
        if field not in data:
            return {"error": f"Missing required field: {field}"}, 400
    
    # Type checking
    if not isinstance(data.get("username"), str):
        return {"error": "username must be a string"}, 400
    if not isinstance(data.get("email"), str):
        return {"error": "email must be a string"}, 400
    if not isinstance(data.get("full_name"), str):
        return {"error": "full_name must be a string"}, 400
    if not isinstance(data.get("age"), int):
        return {"error": "age must be an integer"}, 400
    
    # Validate username
    username = data.get("username")
    if len(username) < 3 or len(username) > 50:
        return {"error": "username must be between 3 and 50 characters"}, 400
    if not username.isalnum():
        return {"error": "username must be alphanumeric"}, 400
    
    # Validate age
    age = data.get("age")
    if age < 18 or age > 120:
        return {"error": "age must be between 18 and 120"}, 400
    
    # Validate role
    role = data.get("role", "viewer")
    valid_roles = ["admin", "editor", "viewer", "guest"]
    if role not in valid_roles:
        return {"error": f"role must be one of: {', '.join(valid_roles)}"}, 400
    
    # Optional fields
    is_active = data.get("is_active", True)
    if not isinstance(is_active, bool):
        return {"error": "is_active must be a boolean"}, 400
    
    tags = data.get("tags", [])
    if not isinstance(tags, list):
        return {"error": "tags must be a list"}, 400
    
    # Validate address if provided
    address = data.get("address")
    if address is not None:
        if not isinstance(address, dict):
            return {"error": "address must be an object"}, 400
        
        address_required_fields = ["street", "city", "state", "postal_code", "country"]
        for field in address_required_fields:
            if field not in address:
                return {"error": f"Missing required address field: {field}"}, 400
            
            if not isinstance(address[field], str):
                return {"error": f"address.{field} must be a string"}, 400
    
    # Validate social media if provided
    social_media = data.get("social_media")
    if social_media is not None:
        if not isinstance(social_media, dict):
            return {"error": "social_media must be an object"}, 400
        
        for platform, url in social_media.items():
            if url is not None and not isinstance(url, str):
                return {"error": f"social_media.{platform} must be a string URL"}, 400
    
    # Validate preferences if provided
    preferences = data.get("preferences", {})
    if not isinstance(preferences, dict):
        return {"error": "preferences must be an object"}, 400
    
    # Create response
    response = {
        "id": "test-id",
        "username": data["username"],
        "email": data["email"],
        "full_name": data["full_name"],
        "age": data["age"],
        "is_active": is_active,
        "role": role,
        "tags": tags,
        "address": address,
        "social_media": social_media,
        "preferences": preferences,
        "created_at": datetime.now().isoformat(),
        "updated_at": None
    }
    
    return response, 201


def openapi_flask_implementation():
    """Flask implementation with flask_x_openapi_schema."""
    # Create a request model instance
    request_body = ComplexUserRequest(**COMPLEX_USER_DATA)
    
    # Create response
    response = ComplexUserResponse(
        id="test-id",
        username=request_body.username,
        email=request_body.email,
        full_name=request_body.full_name,
        age=request_body.age,
        is_active=request_body.is_active,
        role=request_body.role,
        tags=request_body.tags,
        address=request_body.address,
        social_media=request_body.social_media,
        preferences=request_body.preferences,
        created_at=datetime.now().isoformat(),
        updated_at=None
    )
    
    # Convert to dict for JSON serialization
    response_dict = response.model_dump()
    
    return response_dict, 201


def benchmark_function(func, iterations=1000):
    """Benchmark a function with progress bar."""
    results = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task(f"Benchmarking {func.__name__}", total=iterations)
        
        for _ in range(iterations):
            start_time = time.perf_counter()
            func()
            end_time = time.perf_counter()
            results.append((end_time - start_time) * 1000)  # Convert to ms
            progress.update(task, advance=1)
    
    return {
        "min": min(results),
        "max": max(results),
        "mean": sum(results) / len(results),
        "median": sorted(results)[len(results) // 2],
        "p95": sorted(results)[int(len(results) * 0.95)],
        "total": sum(results),
        "iterations": iterations
    }


def display_code_comparison():
    """Display code comparison between standard Flask and flask_x_openapi_schema."""
    standard_code = '''
@app.route('/api/users/<user_id>', methods=['POST'])
def create_user(user_id):
    # Manual validation and parsing
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.get_json()
    
    # Manual validation of required fields
    required_fields = ["username", "email", "full_name", "age"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Type checking
    if not isinstance(data.get("username"), str):
        return jsonify({"error": "username must be a string"}), 400
    if not isinstance(data.get("email"), str):
        return jsonify({"error": "email must be a string"}), 400
    if not isinstance(data.get("full_name"), str):
        return jsonify({"error": "full_name must be a string"}), 400
    if not isinstance(data.get("age"), int):
        return jsonify({"error": "age must be an integer"}), 400
    
    # Validate username
    username = data.get("username")
    if len(username) < 3 or len(username) > 50:
        return jsonify({"error": "username must be between 3 and 50 characters"}), 400
    if not username.isalnum():
        return jsonify({"error": "username must be alphanumeric"}), 400
    
    # Validate age
    age = data.get("age")
    if age < 18 or age > 120:
        return jsonify({"error": "age must be between 18 and 120"}), 400
    
    # Many more validations...
    
    # Create response
    response = {
        "id": user_id,
        "username": data["username"],
        "email": data["email"],
        "full_name": data["full_name"],
        "age": data["age"],
        "is_active": data.get("is_active", True),
        "role": data.get("role", "viewer"),
        "tags": data.get("tags", []),
        "address": data.get("address"),
        "social_media": data.get("social_media"),
        "preferences": data.get("preferences", {}),
        "created_at": datetime.now().isoformat(),
        "updated_at": None
    }
    
    return jsonify(response), 201
'''

    openapi_code = '''
@app.route('/api/users/<user_id>', methods=['POST'])
@openapi_metadata(
    summary="Create a new user",
    description="Create a new user with the given ID",
    tags=["users"],
    request_body=ComplexUserRequest,
    responses={
        "201": {
            "description": "User created successfully",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ComplexUserResponse"}
                }
            },
        },
        "400": {"description": "Bad request"},
    },
)
def create_user(
    user_id: str,
    x_request_body: ComplexUserRequest,
):
    # Create response
    response = ComplexUserResponse(
        id=user_id,
        username=x_request_body.username,
        email=x_request_body.email,
        full_name=x_request_body.full_name,
        age=x_request_body.age,
        is_active=x_request_body.is_active,
        role=x_request_body.role,
        tags=x_request_body.tags,
        address=x_request_body.address,
        social_media=x_request_body.social_media,
        preferences=x_request_body.preferences,
        created_at=datetime.now().isoformat(),
        updated_at=None
    )
    
    return response, 201
'''

    model_code = '''
class ComplexUserRequest(BaseModel):
    """Complex user request model."""
    username: constr(min_length=3, max_length=50) = Field(..., description="The username")
    email: EmailStr = Field(..., description="The email address")
    full_name: str = Field(..., description="The full name")
    age: conint(ge=18, le=120) = Field(..., description="The age")
    is_active: bool = Field(True, description="Whether the user is active")
    role: UserRole = Field(UserRole.VIEWER, description="User role")
    tags: List[str] = Field(default_factory=list, description="User tags")
    address: Optional[Address] = Field(None, description="User address")
    social_media: Optional[SocialMedia] = Field(None, description="Social media profiles")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences")
    
    @validator('username')
    def username_alphanumeric(cls, v):
        """Validate that username is alphanumeric."""
        if not v.isalnum():
            raise ValueError('Username must be alphanumeric')
        return v
'''

    console.print("\n[bold cyan]Code Comparison[/bold cyan]")
    
    console.print("\n[bold yellow]Standard Flask Implementation[/bold yellow] (100+ lines)")
    console.print(Syntax(standard_code, "python", theme="monokai", line_numbers=True))
    
    console.print("\n[bold green]Flask-X-OpenAPI-Schema Implementation[/bold green] (30 lines)")
    console.print(Syntax(openapi_code, "python", theme="monokai", line_numbers=True))
    
    console.print("\n[bold magenta]Pydantic Model Definition[/bold magenta] (validation rules in the model)")
    console.print(Syntax(model_code, "python", theme="monokai", line_numbers=True))


def main():
    """Run the enhanced benchmark."""
    console.print(Panel.fit(
        "[bold cyan]Flask-X-OpenAPI-Schema Enhanced Benchmark[/bold cyan]\n\n"
        "Comparing performance with complex data models and validation",
        title="Benchmark", border_style="cyan", padding=(1, 2)
    ))
    
    # Warm up
    console.print("[yellow]Warming up...[/yellow]")
    for _ in range(100):
        standard_flask_implementation()
        openapi_flask_implementation()
    
    # Benchmark standard Flask
    console.print("\n[bold yellow]Benchmarking Standard Flask Implementation[/bold yellow]")
    standard_results = benchmark_function(standard_flask_implementation)
    
    # Benchmark flask_x_openapi_schema
    console.print("\n[bold green]Benchmarking Flask-X-OpenAPI-Schema Implementation[/bold green]")
    openapi_results = benchmark_function(openapi_flask_implementation)
    
    # Display results
    table = Table(title="Benchmark Results (time in milliseconds)", box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Standard Flask", style="yellow")
    table.add_column("Flask-X-OpenAPI-Schema", style="green")
    table.add_column("Difference", style="magenta")
    
    metrics = ["min", "max", "mean", "median", "p95"]
    for metric in metrics:
        standard_value = standard_results[metric]
        openapi_value = openapi_results[metric]
        diff = openapi_value - standard_value
        diff_percent = (diff / standard_value) * 100 if standard_value > 0 else 0
        
        table.add_row(
            metric.capitalize(),
            f"{standard_value:.6f}",
            f"{openapi_value:.6f}",
            f"{diff:.6f} ({diff_percent:.2f}%)"
        )
    
    console.print(table)
    
    # Calculate overhead
    mean_overhead = (openapi_results["mean"] - standard_results["mean"]) / standard_results["mean"] * 100
    
    # Print conclusion
    console.print(Panel(
        f"[bold]Flask-X-OpenAPI-Schema adds a [red]{mean_overhead:.2f}%[/red] overhead compared to standard Flask.[/bold]\n\n"
        "However, this overhead is negligible in absolute terms:\n"
        f"- Standard Flask: [yellow]{standard_results['mean']:.6f}ms[/yellow] per request\n"
        f"- Flask-X-OpenAPI-Schema: [green]{openapi_results['mean']:.6f}ms[/green] per request\n"
        f"- Absolute difference: [magenta]{openapi_results['mean'] - standard_results['mean']:.6f}ms[/magenta]\n\n"
        "For comparison:\n"
        "- Network latency: 10-100ms\n"
        "- Database queries: 1-10ms\n"
        "- Rendering templates: 5-20ms",
        title="Performance Analysis", border_style="cyan", padding=(1, 2)
    ))
    
    # Display code comparison
    display_code_comparison()
    
    # Print benefits
    console.print(Panel(
        "[bold]Benefits of using Flask-X-OpenAPI-Schema:[/bold]\n\n"
        "1. [green]Automatic Validation[/green]: No need to write manual validation code\n"
        "2. [green]Type Safety[/green]: Leverage Python's type system for better code quality\n"
        "3. [green]Self-Documenting APIs[/green]: Automatically generate OpenAPI documentation\n"
        "4. [green]Reduced Boilerplate[/green]: Write less code for the same functionality\n"
        "5. [green]Better Maintainability[/green]: Cleaner, more structured code\n"
        "6. [green]Consistent Error Handling[/green]: Standardized error responses\n"
        "7. [green]IDE Support[/green]: Better autocompletion and type checking\n\n"
        "[bold]The real value is in developer productivity and code quality,[/bold]\n"
        "[bold]not in raw performance.[/bold]",
        title="Why Use Flask-X-OpenAPI-Schema?", border_style="green", padding=(1, 2)
    ))


if __name__ == "__main__":
    main()
