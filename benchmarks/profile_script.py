"""
Profile script to identify performance bottlenecks in flask_x_openapi_schema.
"""

import cProfile
import json
import pstats
import io
from urllib.parse import urlencode
from flask import Flask, jsonify, request
from pydantic import BaseModel, Field
from typing import List, Optional

from flask_x_openapi_schema.decorators import openapi_metadata
from flask_x_openapi_schema.models.base import BaseRespModel

# Define models for testing
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
        _ = request.args.get("include_inactive", "false").lower() == "true"
        _ = request.args.get("sort_by", "username")

        try:
            _ = int(request.args.get("limit", "10"))
        except ValueError:
            return jsonify({"error": "limit must be an integer"}), 400

        try:
            _ = int(request.args.get("offset", "0"))
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
    def create_user(user_id):
        # Manual handling to avoid the decorator's automatic binding
        # which seems to have an issue with the tags field
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        data = request.get_json()
        try:
            user_request = UserRequest(**data)
            
            # Create response
            response = UserResponse(
                id=user_id,
                username=user_request.username,
                email=user_request.email,
                full_name=user_request.full_name,
                age=user_request.age,
                is_active=user_request.is_active,
                tags=user_request.tags,
                created_at="2023-01-01T00:00:00Z",
                updated_at=None,
            )
            
            return response.to_response(201)
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    return app

def profile_decorator_creation():
    """Profile the creation of a decorated function."""
    pr = cProfile.Profile()
    pr.enable()
    
    # Create the app with decorated function
    app = create_openapi_flask_app()
    
    pr.disable()
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats(20)  # Print top 20 functions by cumulative time
    print("Profile of decorator creation:")
    print(s.getvalue())
    
    return app

def profile_standard_app_request():
    """Profile a standard Flask app request."""
    app = create_standard_flask_app()
    client = app.test_client()
    
    # Prepare the request
    url = f"/api/users/test-user-id?{urlencode(SAMPLE_QUERY_PARAMS)}"
    
    # Profile the request handling
    pr = cProfile.Profile()
    pr.enable()
    
    # Make the request
    response = client.post(
        url,
        json=SAMPLE_USER_DATA,
        content_type="application/json",
    )
    
    pr.disable()
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats(20)  # Print top 20 functions by cumulative time
    print("\nProfile of standard Flask request handling:")
    print(s.getvalue())
    
    # Print response status and data
    print(f"\nStandard Flask response status: {response.status_code}")
    if response.status_code == 201:
        print(f"Response data: {json.loads(response.data)}")
    else:
        print(f"Response error: {response.data}")

def profile_openapi_app_request():
    """Profile an OpenAPI Flask app request."""
    app = create_openapi_flask_app()
    client = app.test_client()
    
    # Prepare the request
    url = f"/api/users/test-user-id?{urlencode(SAMPLE_QUERY_PARAMS)}"
    
    # Profile the request handling
    pr = cProfile.Profile()
    pr.enable()
    
    # Make the request
    response = client.post(
        url,
        json=SAMPLE_USER_DATA,
        content_type="application/json",
    )
    
    pr.disable()
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats(20)  # Print top 20 functions by cumulative time
    print("\nProfile of OpenAPI Flask request handling:")
    print(s.getvalue())
    
    # Print response status and data
    print(f"\nOpenAPI Flask response status: {response.status_code}")
    if response.status_code == 201:
        print(f"Response data: {json.loads(response.data)}")
    else:
        print(f"Response error: {response.data}")

if __name__ == "__main__":
    print("Profiling flask_x_openapi_schema performance...")
    profile_decorator_creation()
    profile_standard_app_request()
    profile_openapi_app_request()