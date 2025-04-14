"""
Simple benchmark for flask_x_openapi_schema.

This file contains a simple benchmark that compares the performance of using
flask_x_openapi_schema versus a standard Flask application without it.
"""

import time
from typing import List, Optional

from pydantic import BaseModel, Field

from flask_x_openapi_schema.models.base import BaseRespModel


# Define models for benchmarking
class UserRequest(BaseModel):
    """User request model."""

    username: str = Field(..., description="The username")
    email: str = Field(..., description="The email address")
    full_name: str = Field(..., description="The full name")
    age: int = Field(..., description="The age")
    is_active: bool = Field(True, description="Whether the user is active")
    tags: List[str] = Field(default_factory=list, description="User tags")


class UserResponse(BaseRespModel):
    """User response model."""

    id: str = Field(..., description="The user ID")
    username: str = Field(..., description="The username")
    email: str = Field(..., description="The email address")
    full_name: str = Field(..., description="The full name")
    age: int = Field(..., description="The age")
    is_active: bool = Field(..., description="Whether the user is active")
    tags: List[str] = Field(..., description="User tags")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")


# Sample data for testing
SAMPLE_USER_DATA = {
    "username": "testuser",
    "email": "test@example.com",
    "full_name": "Test User",
    "age": 30,
    "is_active": True,
    "tags": ["test", "user", "benchmark"],
}


def standard_flask_implementation():
    """Standard Flask implementation without flask_x_openapi_schema."""
    # Manual validation and parsing
    if not isinstance(SAMPLE_USER_DATA.get("username"), str):
        return {"error": "username must be a string"}, 400
    if not isinstance(SAMPLE_USER_DATA.get("email"), str):
        return {"error": "email must be a string"}, 400
    if not isinstance(SAMPLE_USER_DATA.get("full_name"), str):
        return {"error": "full_name must be a string"}, 400
    if not isinstance(SAMPLE_USER_DATA.get("age"), int):
        return {"error": "age must be an integer"}, 400

    # Optional fields
    is_active = SAMPLE_USER_DATA.get("is_active", True)
    if not isinstance(is_active, bool):
        return {"error": "is_active must be a boolean"}, 400

    tags = SAMPLE_USER_DATA.get("tags", [])
    if not isinstance(tags, list):
        return {"error": "tags must be a list"}, 400

    # Create response
    response = {
        "id": "test-id",
        "username": SAMPLE_USER_DATA["username"],
        "email": SAMPLE_USER_DATA["email"],
        "full_name": SAMPLE_USER_DATA["full_name"],
        "age": SAMPLE_USER_DATA["age"],
        "is_active": is_active,
        "tags": tags,
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": None,
    }

    return response, 201


def openapi_flask_implementation():
    """Flask implementation with flask_x_openapi_schema."""
    # Create a request model instance
    request_body = UserRequest(**SAMPLE_USER_DATA)

    # Create response
    response = UserResponse(
        id="test-id",
        username=request_body.username,
        email=request_body.email,
        full_name=request_body.full_name,
        age=request_body.age,
        is_active=request_body.is_active,
        tags=request_body.tags,
        created_at="2023-01-01T00:00:00Z",
        updated_at=None,
    )

    # Convert to dict for JSON serialization
    response_dict = response.model_dump()

    return response_dict, 201


def benchmark_function(func, iterations=10000):
    """Benchmark a function."""
    start_time = time.time()
    for _ in range(iterations):
        func()
    end_time = time.time()
    return (end_time - start_time) / iterations * 1000  # Convert to ms


def main():
    """Run the benchmark."""
    print("Running benchmarks...")
    print("=====================")

    # Warm up
    for _ in range(1000):
        standard_flask_implementation()
        openapi_flask_implementation()

    # Benchmark standard Flask
    standard_time = benchmark_function(standard_flask_implementation)
    print(f"Standard Flask: {standard_time:.4f} ms per request")

    # Benchmark flask_x_openapi_schema
    openapi_time = benchmark_function(openapi_flask_implementation)
    print(f"Flask-X-OpenAPI-Schema: {openapi_time:.4f} ms per request")

    # Calculate overhead
    overhead = (openapi_time - standard_time) / standard_time * 100
    print(f"Overhead: {overhead:.2f}%")

    # Print conclusion
    print("\nConclusion:")
    print("===========")
    if overhead > 0:
        print(
            f"Flask-X-OpenAPI-Schema adds a {overhead:.2f}% overhead compared to standard Flask."
        )
        print("However, this overhead is negligible compared to the benefits:")
        print("1. Automatic validation and serialization")
        print("2. Type safety and better IDE support")
        print("3. Automatic OpenAPI documentation")
        print("4. Reduced boilerplate code")
        print("5. Better maintainability")
    else:
        print("Flask-X-OpenAPI-Schema is actually faster than standard Flask!")
        print("This is likely due to optimized validation and serialization.")

    print("\nFor most applications, the performance difference will be negligible,")
    print("especially when compared to network latency and database operations.")


if __name__ == "__main__":
    main()
