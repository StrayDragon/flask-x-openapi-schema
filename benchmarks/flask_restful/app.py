"""
Flask-RESTful benchmark applications.

This module contains Flask-RESTful applications for benchmarking with and without flask-x-openapi-schema.
"""

from flask import Flask, request
from flask_restful import Api, Resource, reqparse

from flask_x_openapi_schema.x.flask_restful import openapi_metadata
from benchmarks.common.models import UserRequest, UserQueryParams, UserResponse


def create_standard_flask_restful_app():
    """Create a standard Flask-RESTful application without flask-x-openapi-schema."""
    app = Flask("standard_flask_restful_app")
    api = Api(app)

    class StandardUserResource(Resource):
        """Standard Flask-RESTful resource for user operations."""

        def post(self, user_id):
            """Create a user using standard Flask-RESTful."""
            # Create a request parser
            parser = reqparse.RequestParser()
            parser.add_argument("username", type=str, required=True, help="Username is required")
            parser.add_argument("email", type=str, required=True, help="Email is required")
            parser.add_argument("full_name", type=str, required=True, help="Full name is required")
            parser.add_argument("age", type=int, required=True, help="Age is required")
            parser.add_argument("is_active", type=bool, default=True)
            parser.add_argument("tags", type=list, default=[])

            # Parse query parameters
            query_parser = reqparse.RequestParser()
            query_parser.add_argument("include_inactive", type=bool, default=False, location="args")
            query_parser.add_argument("sort_by", type=str, default="username", location="args")
            query_parser.add_argument("limit", type=int, default=10, location="args")
            query_parser.add_argument("offset", type=int, default=0, location="args")

            # Parse arguments
            args = parser.parse_args(strict=True)
            query_args = query_parser.parse_args()

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
    api.add_resource(StandardUserResource, "/standard/api/users/<string:user_id>")

    return app


def create_openapi_flask_restful_app():
    """Create a Flask-RESTful application with flask-x-openapi-schema."""
    app = Flask("openapi_flask_restful_app")
    api = Api(app)

    class OpenAPIUserResource(Resource):
        """Flask-RESTful resource with OpenAPI metadata for user operations."""

        @openapi_metadata(
            summary="Create a new user",
            description="Create a new user with the given ID",
            tags=["users"],
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
            }
        )
        def post(self, user_id, _x_body: UserRequest = None, _x_query: UserQueryParams = None):
            """Create a user using flask-x-openapi-schema."""
            try:
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
            except Exception as e:
                # Log the error for debugging
                print(f"Error in OpenAPIUserResource.post: {e}")
                return {"error": str(e)}, 400

    # Register the resource
    api.add_resource(OpenAPIUserResource, "/openapi/api/users/<string:user_id>")

    return app


def create_combined_app():
    """Create a combined Flask application with both standard and OpenAPI endpoints."""
    app = Flask("combined_flask_restful_app")
    api = Api(app)

    # Standard Flask-RESTful resource
    class StandardUserResource(Resource):
        """Standard Flask-RESTful resource for user operations."""

        def post(self, user_id):
            """Create a user using standard Flask-RESTful."""
            # Create a request parser
            parser = reqparse.RequestParser()
            parser.add_argument("username", type=str, required=True, help="Username is required")
            parser.add_argument("email", type=str, required=True, help="Email is required")
            parser.add_argument("full_name", type=str, required=True, help="Full name is required")
            parser.add_argument("age", type=int, required=True, help="Age is required")
            parser.add_argument("is_active", type=bool, default=True)
            parser.add_argument("tags", type=list, default=[])

            # Parse query parameters
            query_parser = reqparse.RequestParser()
            query_parser.add_argument("include_inactive", type=bool, default=False, location="args")
            query_parser.add_argument("sort_by", type=str, default="username", location="args")
            query_parser.add_argument("limit", type=int, default=10, location="args")
            query_parser.add_argument("offset", type=int, default=0, location="args")

            # Parse arguments
            args = parser.parse_args(strict=True)
            query_args = query_parser.parse_args()

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

    # OpenAPI Flask-RESTful resource
    class OpenAPIUserResource(Resource):
        """Flask-RESTful resource with OpenAPI metadata for user operations."""

        @openapi_metadata(
            summary="Create a new user",
            description="Create a new user with the given ID",
            tags=["users"],
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
            }
        )
        def post(self, user_id, _x_body: UserRequest = None, _x_query: UserQueryParams = None):
            """Create a user using flask-x-openapi-schema."""
            try:
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
            except Exception as e:
                # Log the error for debugging
                print(f"Error in OpenAPIUserResource.post: {e}")
                return {"error": str(e)}, 400

    # Register the resources
    api.add_resource(StandardUserResource, "/standard/api/users/<string:user_id>")
    api.add_resource(OpenAPIUserResource, "/openapi/api/users/<string:user_id>")

    return app


# Create the combined app
app = create_combined_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)