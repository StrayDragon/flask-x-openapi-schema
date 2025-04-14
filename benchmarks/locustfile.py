"""
Locust load test for flask_x_openapi_schema.

This file contains a Locust load test that simulates real-world usage of the library.
It compares the performance of a standard Flask application versus one using flask_x_openapi_schema.

To run:
    locust -f benchmarks/locustfile.py --headless -u 100 -r 10 -t 30s --csv=results
"""

import random
from locust import HttpUser, task, between

# Test data
USER_DATA = [
    {
        "username": f"user{i}",
        "email": f"user{i}@example.com",
        "full_name": f"User {i}",
        "age": random.randint(18, 65),
        "is_active": random.choice([True, False]),
        "tags": random.sample(
            ["test", "user", "api", "benchmark", "performance", "flask", "openapi"],
            k=random.randint(1, 5),
        ),
    }
    for i in range(1, 101)
]

QUERY_PARAMS = "?include_inactive=false&sort_by=username&limit=10&offset=0"


class StandardFlaskUser(HttpUser):
    """User that tests the standard Flask implementation."""

    host = "http://localhost:5000"
    wait_time = between(1, 3)

    @task
    def create_user(self):
        """Create a user using the standard Flask endpoint."""
        user_data = random.choice(USER_DATA)
        user_id = f"user-{random.randint(1000, 9999)}"

        with self.client.post(
            f"/standard/api/users/{user_id}{QUERY_PARAMS}",
            json=user_data,
            catch_response=True,
        ) as response:
            if response.status_code == 201:
                response.success()
            else:
                response.failure(f"Failed with status code: {response.status_code}")


class OpenAPIFlaskUser(HttpUser):
    """User that tests the flask_x_openapi_schema implementation."""

    host = "http://localhost:5000"
    wait_time = between(1, 3)

    @task
    def create_user(self):
        """Create a user using the OpenAPI Flask endpoint."""
        user_data = random.choice(USER_DATA)
        user_id = f"user-{random.randint(1000, 9999)}"

        with self.client.post(
            f"/openapi/api/users/{user_id}{QUERY_PARAMS}",
            json=user_data,
            catch_response=True,
        ) as response:
            if response.status_code == 201:
                response.success()
            else:
                response.failure(f"Failed with status code: {response.status_code}")


# Server implementation for the load test
if __name__ == "__main__":
    from flask import Flask, request, jsonify
    from flask_x_openapi_schema.decorators import openapi_metadata
    from models import UserRequest, UserQueryParams, UserResponse

    app = Flask("load_test_server")

    # Standard Flask implementation
    @app.route("/standard/api/users/<user_id>", methods=["POST"])
    def standard_create_user(user_id):
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

    # OpenAPI Flask implementation
    @app.route("/openapi/api/users/<user_id>", methods=["POST"])
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
    def openapi_create_user(
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

    # Run the server
    if __name__ == "__main__":
        app.run(host="0.0.0.0", port=5000)
