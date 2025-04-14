"""
Comprehensive benchmarks for flask_x_openapi_schema.

This file contains more detailed benchmarks that test different aspects of the library:
1. Request validation performance
2. Response serialization performance
3. OpenAPI schema generation performance
4. Performance with different payload sizes
"""

import json
from typing import List, Optional

import pytest
from flask import Flask
from pydantic import BaseModel, Field
from flask_x_openapi_schema.models.base import BaseRespModel

from flask_x_openapi_schema.decorators import openapi_metadata
from flask_x_openapi_schema.schema_generator import generate_schema


# Define models inline for benchmarking
class UserRequest(BaseModel):
    """User request model."""

    username: str = Field(..., description="The username")
    email: str = Field(..., description="The email address")
    full_name: str = Field(..., description="The full name")
    age: int = Field(..., description="The age")
    is_active: bool = Field(True, description="Whether the user is active")
    tags: List[str] = Field(default_factory=list, description="User tags")


class UserQueryParams(BaseModel):
    """User query parameters."""

    include_inactive: bool = Field(False, description="Include inactive users")
    sort_by: str = Field("username", description="Field to sort by")
    limit: int = Field(10, description="Maximum number of results")
    offset: int = Field(0, description="Offset for pagination")


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


# Test data with different payload sizes
SMALL_PAYLOAD = {
    "username": "user1",
    "email": "user1@example.com",
    "full_name": "User One",
    "age": 25,
    "is_active": True,
    "tags": ["small"],
}

MEDIUM_PAYLOAD = {
    "username": "user2",
    "email": "user2@example.com",
    "full_name": "User Two With a Longer Name",
    "age": 30,
    "is_active": True,
    "tags": ["medium", "payload", "test", "benchmark", "performance"],
}

LARGE_PAYLOAD = {
    "username": "user3",
    "email": "user3@example.com",
    "full_name": "User Three With an Even Longer Name for Testing Purposes",
    "age": 35,
    "is_active": True,
    "tags": [
        "large",
        "payload",
        "test",
        "benchmark",
        "performance",
        "flask",
        "openapi",
        "schema",
        "validation",
        "serialization",
        "deserialization",
        "json",
        "api",
        "rest",
        "http",
        "web",
        "server",
        "client",
        "request",
        "response",
    ],
}


@pytest.fixture
def app():
    """Create a Flask app with flask_x_openapi_schema."""
    app = Flask("benchmark_app")

    @app.route("/api/users/<user_id>", methods=["POST"])
    @openapi_metadata(
        summary="Create a new user",
        description="Create a new user with the given ID",
        tags=["users"],
        request_body=UserRequest,
        query_model=UserQueryParams,
        responses={
            "201": {
                "description": "User created successfully",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/UserResponse"}
                    }
                },
            },
            "400": {"description": "Bad request"},
        },
    )
    def create_user(
        user_id: str,
        x_request_body: UserRequest,
        x_request_query: UserQueryParams,
        x_request_path_user_id: str,
    ):
        # Create response
        response = UserResponse(
            id=user_id,
            username=x_request_body.username,
            email=x_request_body.email,
            full_name=x_request_body.full_name,
            age=x_request_body.age,
            is_active=x_request_body.is_active,
            tags=x_request_body.tags,
            created_at="2023-01-01T00:00:00Z",
            updated_at=None,
        )

        return response, 201

    return app


@pytest.fixture
def client(app):
    """Flask test client."""
    with app.test_client() as client:
        yield client


def test_request_validation(benchmark):
    """Benchmark request validation performance."""

    def run():
        # Create a request model instance and validate it
        user = UserRequest(**MEDIUM_PAYLOAD)
        assert user.username == MEDIUM_PAYLOAD["username"]
        assert user.email == MEDIUM_PAYLOAD["email"]
        assert user.age == MEDIUM_PAYLOAD["age"]

    benchmark(run)


def test_response_serialization(benchmark):
    """Benchmark response serialization performance."""
    # Create a response model instance
    response = UserResponse(
        id="test-id",
        username=MEDIUM_PAYLOAD["username"],
        email=MEDIUM_PAYLOAD["email"],
        full_name=MEDIUM_PAYLOAD["full_name"],
        age=MEDIUM_PAYLOAD["age"],
        is_active=MEDIUM_PAYLOAD["is_active"],
        tags=MEDIUM_PAYLOAD["tags"],
        created_at="2023-01-01T00:00:00Z",
        updated_at=None,
    )

    def run():
        # Serialize the response to JSON
        json_data = response.model_dump_json()
        assert json_data is not None
        # Parse it back to ensure it's valid JSON
        parsed = json.loads(json_data)
        assert parsed["id"] == "test-id"

    benchmark(run)


def test_schema_generation(benchmark):
    """Benchmark OpenAPI schema generation performance."""
    app = Flask("schema_benchmark")

    @app.route("/api/users/<user_id>", methods=["POST"])
    @openapi_metadata(
        summary="Create a new user",
        description="Create a new user with the given ID",
        tags=["users"],
        request_body=UserRequest,
        query_model=UserQueryParams,
        responses={
            "201": {
                "description": "User created successfully",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/UserResponse"}
                    }
                },
            },
            "400": {"description": "Bad request"},
        },
    )
    def create_user(
        user_id: str,
        x_request_body: UserRequest,
        x_request_query: UserQueryParams,
        x_request_path_user_id: str,
    ):
        return {"id": user_id}, 201

    def run():
        # Generate OpenAPI schema
        schema = generate_schema(app, title="Benchmark API", version="1.0.0")
        assert schema is not None
        assert "paths" in schema
        assert "/api/users/{user_id}" in schema["paths"]

    benchmark(run)


def test_small_payload(benchmark, client):
    """Benchmark with small payload."""

    def run():
        response = client.post(
            "/api/users/test-id?include_inactive=false&sort_by=username&limit=10&offset=0",
            json=SMALL_PAYLOAD,
            content_type="application/json",
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["id"] == "test-id"

    benchmark(run)


def test_medium_payload(benchmark, client):
    """Benchmark with medium payload."""

    def run():
        response = client.post(
            "/api/users/test-id?include_inactive=false&sort_by=username&limit=10&offset=0",
            json=MEDIUM_PAYLOAD,
            content_type="application/json",
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["id"] == "test-id"

    benchmark(run)


def test_large_payload(benchmark, client):
    """Benchmark with large payload."""

    def run():
        response = client.post(
            "/api/users/test-id?include_inactive=false&sort_by=username&limit=10&offset=0",
            json=LARGE_PAYLOAD,
            content_type="application/json",
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["id"] == "test-id"

    benchmark(run)
