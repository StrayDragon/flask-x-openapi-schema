"""
Benchmark tests for flask_x_openapi_schema.

This file contains benchmarks that compare the performance of using flask_x_openapi_schema
versus a standard Flask application without it.
"""

import json
from typing import List, Optional

import pytest
from flask import Flask, request, jsonify
from pydantic import BaseModel, Field

from flask_x_openapi_schema.decorators import openapi_metadata

# Import models directly
from flask_x_openapi_schema.models.base import BaseRespModel


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


# Sample data for testing
SAMPLE_USER_DATA = {
    "username": "testuser",
    "email": "test@example.com",
    "full_name": "Test User",
    "age": 30,
    "is_active": True,
    "tags": ["test", "user", "benchmark"],
}

SAMPLE_QUERY_PARAMS = {
    "include_inactive": "false",
    "sort_by": "username",
    "limit": "10",
    "offset": "0",
}


def create_standard_flask_app():
    """Create a standard Flask app without flask_x_openapi_schema."""
    app = Flask("standard_flask")

    @app.route("/api/users/<user_id>", methods=["POST"])
    def create_user(user_id):
        # Manual validation and parsing
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        data = request.get_json()

        # Manual validation
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

        # Optional fields
        is_active = data.get("is_active", True)
        if not isinstance(is_active, bool):
            return jsonify({"error": "is_active must be a boolean"}), 400

        tags = data.get("tags", [])
        if not isinstance(tags, list):
            return jsonify({"error": "tags must be a list"}), 400

        # Query parameters
        include_inactive = (
            request.args.get("include_inactive", "false").lower() == "true"
        )
        sort_by = request.args.get("sort_by", "username")

        try:
            limit = int(request.args.get("limit", "10"))
        except ValueError:
            return jsonify({"error": "limit must be an integer"}), 400

        try:
            offset = int(request.args.get("offset", "0"))
        except ValueError:
            return jsonify({"error": "offset must be an integer"}), 400

        # Create response
        response = {
            "id": user_id,
            "username": data["username"],
            "email": data["email"],
            "full_name": data["full_name"],
            "age": data["age"],
            "is_active": is_active,
            "tags": tags,
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": None,
        }

        return jsonify(response), 201

    return app


def create_openapi_flask_app():
    """Create a Flask app with flask_x_openapi_schema."""
    app = Flask("openapi_flask")

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
def standard_client():
    """Flask test client for standard app."""
    app = create_standard_flask_app()
    with app.test_client() as client:
        yield client


@pytest.fixture
def openapi_client():
    """Flask test client for OpenAPI app."""
    app = create_openapi_flask_app()
    with app.test_client() as client:
        yield client


def test_standard_flask(benchmark, standard_client):
    """Benchmark standard Flask implementation."""

    def run():
        response = standard_client.post(
            f"/api/users/test-user-id?{urlencode(SAMPLE_QUERY_PARAMS)}",
            json=SAMPLE_USER_DATA,
            content_type="application/json",
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["id"] == "test-user-id"
        assert data["username"] == SAMPLE_USER_DATA["username"]

    benchmark(run)


def test_openapi_flask(benchmark, openapi_client):
    """Benchmark flask_x_openapi_schema implementation."""

    def run():
        response = openapi_client.post(
            f"/api/users/test-user-id?{urlencode(SAMPLE_QUERY_PARAMS)}",
            json=SAMPLE_USER_DATA,
            content_type="application/json",
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["id"] == "test-user-id"
        assert data["username"] == SAMPLE_USER_DATA["username"]

    benchmark(run)


def urlencode(params):
    """Simple URL parameter encoder."""
    return "&".join(f"{k}={v}" for k, v in params.items())
