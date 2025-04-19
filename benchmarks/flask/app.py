"""
Flask benchmark applications.

This module contains Flask applications for benchmarking with and without flask-x-openapi-schema.
"""

import json
import time
from datetime import datetime

from flask import Flask, request, jsonify, Response

from flask_x_openapi_schema.x.flask import openapi_metadata
from benchmarks.common.models import (
    UserRequest, UserQueryParams, UserResponse, UserRole,
    AddressModel, ContactInfo, Preferences, UserStats
)
from benchmarks.common.utils import get_performance_metrics


def create_standard_flask_app():
    """Create a standard Flask application without flask-x-openapi-schema."""
    app = Flask("standard_flask_app")

    @app.route("/standard/api/users/<user_id>", methods=["POST"])
    def standard_create_user(user_id):
        """Create a user using standard Flask."""
        # Manual validation and parsing
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        data = request.get_json()

        # Start timing for performance metrics
        start_time = time.time()

        # Manual validation of required fields
        required_fields = ["username", "email", "full_name", "age"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # Type checking for basic fields
        if not isinstance(data.get("username"), str):
            return jsonify({"error": "username must be a string"}), 400
        if not isinstance(data.get("email"), str):
            return jsonify({"error": "email must be a string"}), 400
        if not isinstance(data.get("full_name"), str):
            return jsonify({"error": "full_name must be a string"}), 400
        if not isinstance(data.get("age"), int):
            return jsonify({"error": "age must be an integer"}), 400

        # Validate username length
        username = data.get("username")
        if len(username) < 3 or len(username) > 50:
            return jsonify({"error": "username must be between 3 and 50 characters"}), 400

        # Validate email format
        email = data.get("email")
        if "@" not in email:
            return jsonify({"error": "email must be a valid email address"}), 400

        # Validate age range
        age = data.get("age")
        if age < 18 or age > 120:
            return jsonify({"error": "age must be between 18 and 120"}), 400

        # Optional fields with validation
        is_active = data.get("is_active", True)
        if not isinstance(is_active, bool):
            return jsonify({"error": "is_active must be a boolean"}), 400

        # Role validation
        role = data.get("role", "user")
        if not isinstance(role, str):
            return jsonify({"error": "role must be a string"}), 400
        valid_roles = [r.value for r in UserRole]
        if role not in valid_roles:
            return jsonify({"error": f"role must be one of: {', '.join(valid_roles)}"}), 400

        # Tags validation
        tags = data.get("tags", [])
        if not isinstance(tags, list):
            return jsonify({"error": "tags must be a list"}), 400
        for tag in tags:
            if not isinstance(tag, str):
                return jsonify({"error": "all tags must be strings"}), 400

        # Addresses validation
        addresses = data.get("addresses", [])
        if not isinstance(addresses, list):
            return jsonify({"error": "addresses must be a list"}), 400
        for addr in addresses:
            if not isinstance(addr, dict):
                return jsonify({"error": "each address must be an object"}), 400
            for field in ["street", "city", "state", "postal_code", "country"]:
                if field not in addr:
                    return jsonify({"error": f"address missing required field: {field}"}), 400
                if not isinstance(addr[field], str):
                    return jsonify({"error": f"address field {field} must be a string"}), 400
            if "is_primary" in addr and not isinstance(addr["is_primary"], bool):
                return jsonify({"error": "address is_primary must be a boolean"}), 400

        # Contact info validation
        contact_info = data.get("contact_info")
        if contact_info is not None:
            if not isinstance(contact_info, dict):
                return jsonify({"error": "contact_info must be an object"}), 400
            for field in ["phone", "alternative_email", "emergency_contact"]:
                if field in contact_info and not isinstance(contact_info[field], str):
                    return jsonify({"error": f"contact_info field {field} must be a string"}), 400

        # Preferences validation
        preferences = data.get("preferences")
        if preferences is not None:
            if not isinstance(preferences, dict):
                return jsonify({"error": "preferences must be an object"}), 400
            for field in ["theme", "language", "timezone", "email_frequency"]:
                if field in preferences and not isinstance(preferences[field], str):
                    return jsonify({"error": f"preferences field {field} must be a string"}), 400
            if "notifications_enabled" in preferences and not isinstance(preferences["notifications_enabled"], bool):
                return jsonify({"error": "preferences notifications_enabled must be a boolean"}), 400

        # Metadata validation
        metadata = data.get("metadata", {})
        if not isinstance(metadata, dict):
            return jsonify({"error": "metadata must be an object"}), 400

        # Query parameters validation
        include_inactive = request.args.get("include_inactive", "false").lower() == "true"
        sort_by = request.args.get("sort_by", "username")
        sort_order = request.args.get("sort_order", "asc")
        if sort_order not in ["asc", "desc"]:
            return jsonify({"error": "sort_order must be 'asc' or 'desc'"}), 400

        try:
            limit = int(request.args.get("limit", "10"))
            if limit < 1 or limit > 100:
                return jsonify({"error": "limit must be between 1 and 100"}), 400
        except ValueError:
            return jsonify({"error": "limit must be an integer"}), 400

        try:
            offset = int(request.args.get("offset", "0"))
            if offset < 0:
                return jsonify({"error": "offset must be non-negative"}), 400
        except ValueError:
            return jsonify({"error": "offset must be an integer"}), 400

        # Additional query parameters
        filter_role = request.args.get("filter_role")
        if filter_role and filter_role not in [r.value for r in UserRole]:
            return jsonify({"error": f"filter_role must be one of: {', '.join([r.value for r in UserRole])}"}), 400

        search = request.args.get("search")

        try:
            min_age = request.args.get("min_age")
            if min_age:
                min_age = int(min_age)
                if min_age < 18 or min_age > 120:
                    return jsonify({"error": "min_age must be between 18 and 120"}), 400
        except ValueError:
            return jsonify({"error": "min_age must be an integer"}), 400

        try:
            max_age = request.args.get("max_age")
            if max_age:
                max_age = int(max_age)
                if max_age < 18 or max_age > 120:
                    return jsonify({"error": "max_age must be between 18 and 120"}), 400
        except ValueError:
            return jsonify({"error": "max_age must be an integer"}), 400

        tags_filter = request.args.get("tags")
        if tags_filter:
            tags_filter = tags_filter.split(",")

        created_after = request.args.get("created_after")
        created_before = request.args.get("created_before")

        # Create response with all fields
        created_at = datetime.now().isoformat()

        # Create user stats
        stats = {
            "login_count": 0,
            "last_login": None,
            "post_count": 0,
            "comment_count": 0,
            "reputation": 0
        }

        # Create response
        response = {
            "id": user_id,
            "username": data["username"],
            "email": data["email"],
            "full_name": data["full_name"],
            "age": data["age"],
            "is_active": is_active,
            "role": role,
            "tags": tags,
            "addresses": addresses,
            "contact_info": contact_info,
            "preferences": preferences,
            "metadata": metadata,
            "stats": stats,
            "created_at": created_at,
            "updated_at": None,
        }

        # Calculate performance metrics
        end_time = time.time()
        processing_time = (end_time - start_time) * 1000  # Convert to milliseconds

        # Add performance metrics to response headers
        metrics = get_performance_metrics()
        metrics["request_duration_ms"] = processing_time

        # Create response with metrics in headers
        resp = Response(json.dumps(response), status=201, mimetype='application/json')
        resp.headers['X-Processing-Time'] = f"{processing_time:.2f}ms"
        resp.headers['X-DB-Queries'] = str(metrics["db_query_count"])
        resp.headers['X-Cache-Status'] = f"hits={metrics['cache_hits']},misses={metrics['cache_misses']}"

        return resp

    return app


def create_openapi_flask_app():
    """Create a Flask application with flask-x-openapi-schema."""
    app = Flask("openapi_flask_app")

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
    def openapi_create_user(user_id: str, x_request_body: UserRequest = None, x_request_query: UserQueryParams = None):
        """Create a user using flask-x-openapi-schema."""
        try:
            # Start timing for performance metrics
            start_time = time.time()

            # Create user stats
            stats = UserStats(
                login_count=0,
                last_login=None,
                post_count=0,
                comment_count=0,
                reputation=0
            )

            # Create response with current timestamp
            created_at = datetime.now().isoformat()

            # Create response
            response = UserResponse(
                id=user_id,
                username=x_request_body.username,
                email=x_request_body.email,
                full_name=x_request_body.full_name,
                age=x_request_body.age,
                is_active=x_request_body.is_active,
                role=x_request_body.role,
                tags=x_request_body.tags,
                addresses=x_request_body.addresses,
                contact_info=x_request_body.contact_info,
                preferences=x_request_body.preferences,
                metadata=x_request_body.metadata,
                stats=stats,
                created_at=created_at,
                updated_at=None,
            )

            # Calculate performance metrics
            end_time = time.time()
            processing_time = (end_time - start_time) * 1000  # Convert to milliseconds

            # Add performance metrics to response headers
            metrics = get_performance_metrics()
            metrics["request_duration_ms"] = processing_time

            # Create response with metrics in headers
            resp = response.to_response(201)
            resp.headers['X-Processing-Time'] = f"{processing_time:.2f}ms"
            resp.headers['X-DB-Queries'] = str(metrics["db_query_count"])
            resp.headers['X-Cache-Status'] = f"hits={metrics['cache_hits']},misses={metrics['cache_misses']}"

            return resp
        except Exception as e:
            # Log the error for debugging
            print(f"Error in openapi_create_user: {e}")
            return jsonify({"error": str(e)}), 400

    return app


def create_combined_app():
    """Create a combined Flask application with both standard and OpenAPI endpoints."""
    app = Flask("combined_flask_app")

    # Register standard endpoints
    standard_app = create_standard_flask_app()
    for rule in standard_app.url_map.iter_rules():
        if rule.endpoint != "static":
            app.add_url_rule(
                rule.rule,
                endpoint=rule.endpoint,
                view_func=standard_app.view_functions[rule.endpoint],
                methods=rule.methods,
            )

    # Register OpenAPI endpoints
    openapi_app = create_openapi_flask_app()
    for rule in openapi_app.url_map.iter_rules():
        if rule.endpoint != "static":
            app.add_url_rule(
                rule.rule,
                endpoint=rule.endpoint,
                view_func=openapi_app.view_functions[rule.endpoint],
                methods=rule.methods,
            )

    return app


# Create the combined app
app = create_combined_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)