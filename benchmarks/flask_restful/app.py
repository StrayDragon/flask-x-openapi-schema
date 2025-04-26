"""Flask-RESTful benchmark applications.

This module contains Flask-RESTful applications for benchmarking with and without flask-x-openapi-schema.
"""

from flask import Flask, jsonify, request
from flask_restful import Api, Resource, reqparse

from benchmarks.common.models import (
    Error400Resp,
    UserQueryParams,
    UserRequest,
    UserResponse,
    UserRole,
)
from flask_x_openapi_schema import OpenAPIMetaResponse, OpenAPIMetaResponseItem
from flask_x_openapi_schema.x.flask_restful import openapi_metadata


def create_standard_flask_restful_app(app: Flask):
    """Create a standard Flask-RESTful application without flask-x-openapi-schema."""
    api = Api(app)

    class StandardUserResource(Resource):
        """Standard Flask-RESTful resource for user operations."""

        def post(self, user_id):
            """Create a user using standard Flask-RESTful."""
            # Create a request parser for body parameters
            parser = reqparse.RequestParser()
            parser.add_argument(
                "username",
                type=str,
                required=True,
                help="Username is required",
                location="json",
            )
            parser.add_argument(
                "email",
                type=str,
                required=True,
                help="Email is required",
                location="json",
            )
            parser.add_argument(
                "full_name",
                type=str,
                required=True,
                help="Full name is required",
                location="json",
            )
            parser.add_argument("age", type=int, required=True, help="Age is required", location="json")
            parser.add_argument("is_active", type=bool, default=True, location="json")
            parser.add_argument("tags", type=list, default=[], location="json")

            # Parse query parameters
            query_parser = reqparse.RequestParser()
            query_parser.add_argument("include_inactive", type=bool, default=False, location="args")
            query_parser.add_argument("sort_by", type=str, default="username", location="args")
            query_parser.add_argument("sort_order", type=str, default="asc", location="args")
            query_parser.add_argument("limit", type=int, default=10, location="args")
            query_parser.add_argument("offset", type=int, default=0, location="args")
            query_parser.add_argument("filter_role", type=str, default=None, location="args")
            query_parser.add_argument("search", type=str, default=None, location="args")
            query_parser.add_argument("min_age", type=int, default=None, location="args")
            query_parser.add_argument("max_age", type=int, default=None, location="args")
            query_parser.add_argument("tags", type=str, default=None, location="args")
            query_parser.add_argument("created_after", type=str, default=None, location="args")
            query_parser.add_argument("created_before", type=str, default=None, location="args")

            # Parse arguments
            args = parser.parse_args(strict=False, req=request)
            query_args = query_parser.parse_args(strict=False, req=request)

            # Validate filter_role if present
            if query_args.get("filter_role"):
                valid_roles = [role.value for role in UserRole]
                print(f"Valid roles: {valid_roles}")
                print(f"Current filter_role: {query_args['filter_role']}")
                if query_args["filter_role"] not in valid_roles:
                    return jsonify({"error": f"filter_role must be one of: {', '.join(valid_roles)}"}), 400

            # Create response
            response = {
                "id": user_id,
                "username": args["username"],
                "email": args["email"],
                "full_name": args["full_name"],
                "age": args["age"],
                "is_active": args["is_active"],
                "tags": args["tags"],
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": None,
            }

            return response, 201

    # Register the resource
    api.add_resource(StandardUserResource, "/standard/api/users/<user_id>")

    return app


def create_openapi_flask_restful_app(app: Flask):
    """Create a Flask-RESTful application with flask-x-openapi-schema."""
    api = Api(app)

    class OpenAPIUserResource(Resource):
        """Flask-RESTful resource with OpenAPI metadata for user operations."""

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
                },
            ),
        )
        def post(self, user_id, _x_body: UserRequest = None, _x_query: UserQueryParams = None):
            """Create a user using flask-x-openapi-schema."""
            if _x_query and _x_query.filter_role:
                valid_roles = list(UserRole)
                print(f"Valid roles: {[role.value for role in valid_roles]}")
                print(f"Current filter_role: {_x_query.filter_role}")
                if _x_query.filter_role not in valid_roles:
                    return jsonify(
                        {"error": f"filter_role must be one of: {', '.join([role.value for role in UserRole])}"},
                    ), 400

            # Create response
            response = UserResponse(
                id=user_id,
                username=_x_body.username,
                email=_x_body.email,
                full_name=_x_body.full_name,
                age=_x_body.age,
                is_active=_x_body.is_active,
                tags=_x_body.tags,
                created_at="2023-01-01T00:00:00Z",
                updated_at=None,
            )

            return response.to_response(201)

    # Register the resource
    api.add_resource(OpenAPIUserResource, "/openapi/api/users/<user_id>")

    return app


def create_combined_app():
    """Create a combined Flask application with both standard and OpenAPI endpoints."""
    app = Flask("combined_flask_restful_app")

    create_standard_flask_restful_app(app)
    create_openapi_flask_restful_app(app)

    return app


# Create the combined app
app = create_combined_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)  # noqa: S104
