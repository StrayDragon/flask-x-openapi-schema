"""
Flask benchmark applications.

This module contains Flask applications for benchmarking with and without flask-x-openapi-schema.
"""

import json
import time
from datetime import datetime

from flask import Flask, request, jsonify, Response

from flask_x_openapi_schema import OpenAPIMetaResponse, OpenAPIMetaResponseItem
from flask_x_openapi_schema.x.flask import openapi_metadata
from benchmarks.common.models import (
    Error400Resp,
    UserRequest,
    UserQueryParams,
    UserResponse,
    UserRole,
    UserStats,
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

        req = UserRequest.model_validate(data)

        # Create response
        response = req.model_dump(mode='json')
        end_time = time.time()
        processing_time = (end_time - start_time) * 1000

        # Add performance metrics to response headers
        metrics = get_performance_metrics()
        metrics["request_duration_ms"] = processing_time

        # Create response with metrics in headers
        resp = Response(json.dumps(response), status=201, mimetype="application/json")
        resp.headers["X-Processing-Time"] = f"{processing_time:.2f}ms"
        resp.headers["X-DB-Queries"] = str(metrics["db_query_count"])
        resp.headers["X-Cache-Status"] = (
            f"hits={metrics['cache_hits']},misses={metrics['cache_misses']}"
        )

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
        responses=OpenAPIMetaResponse(
            responses={
                "201": OpenAPIMetaResponseItem(
                    model=UserResponse,
                    description="User created successfully",
                ),
                "400": OpenAPIMetaResponseItem(
                    model=Error400Resp,
                    description="Bad request",
                ),
            }
        ),
    )
    def openapi_create_user(
        user_id: str, _x_body: UserRequest = None, _x_query: UserQueryParams = None
    ):
        """Create a user using flask-x-openapi-schema."""
        # Start timing for performance metrics
        start_time = time.time()

        # Create response
        response = _x_body

        # Calculate performance metrics
        end_time = time.time()
        processing_time = (end_time - start_time) * 1000  # Convert to milliseconds

        # Add performance metrics to response headers
        metrics = get_performance_metrics()
        metrics["request_duration_ms"] = processing_time

        # Create response with metrics in headers
        resp = Response(response.model_dump(mode='json'), 201)
        resp.headers["X-Processing-Time"] = f"{processing_time:.2f}ms"
        resp.headers["X-DB-Queries"] = str(metrics["db_query_count"])
        resp.headers["X-Cache-Status"] = (
            f"hits={metrics['cache_hits']},misses={metrics['cache_misses']}"
        )
        return resp

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
