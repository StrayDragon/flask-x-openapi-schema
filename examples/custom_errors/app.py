"""Example of custom error handling with Flask-X-OpenAPI-Schema.

This example demonstrates how to create custom error types by extending the
APIError abstract base class and implementing the to_response method.

IMPORTANT: APIError is an abstract base class and cannot be instantiated directly.
You must create a subclass that implements the to_response() method.

For example, this will raise a TypeError:
    try:
        # This will fail because APIError is abstract
        error = APIError("This will fail")
    except TypeError as e:
        print(f"Error: {e}")
        # Output: Error: APIError is an abstract base class and cannot be instantiated directly.
        # You must create a subclass that implements the to_response() method.
"""

from datetime import datetime
from typing import Any

from flask import Flask, jsonify, request
from pydantic import BaseModel, Field
from pydantic import ValidationError as PydanticValidationError

from flask_x_openapi_schema import APIError, handle_api_error
from flask_x_openapi_schema.x.flask.decorators import openapi_metadata


# Define custom error types by extending APIError
#
# IMPORTANT: You MUST extend APIError to create your own error types.
# Direct instantiation of APIError is not allowed and will raise a TypeError.
#
# The only required method to implement is `to_response()`, which should return
# a tuple containing the response data and HTTP status code.
class CustomError(APIError):
    """Base class for all custom errors in this application."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()
        super().__init__(message)

    def to_response(self) -> tuple[dict[str, Any], int]:
        """Convert the error to a response tuple."""
        response_data = {
            "error": {
                "code": self.code,
                "message": self.message,
                "timestamp": self.timestamp,
            }
        }

        if self.details:
            response_data["error"]["details"] = self.details

        return response_data, self.status_code


class ValidationError(CustomError):
    """Error raised when request data fails validation."""

    def __init__(
        self,
        field_errors: dict[str, list[str]],
        message: str = "Validation failed",
    ):
        super().__init__(
            code="VALIDATION_ERROR",
            message=message,
            status_code=422,
            details={"fields": field_errors},
        )


class NotFoundError(CustomError):
    """Error raised when a requested resource is not found."""

    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        message: str | None = None,
    ):
        if message is None:
            message = f"{resource_type} with ID {resource_id} not found"

        super().__init__(
            code="NOT_FOUND",
            message=message,
            status_code=404,
            details={"resource_type": resource_type, "resource_id": resource_id},
        )


class AuthenticationError(CustomError):
    """Error raised when authentication fails."""

    def __init__(
        self,
        message: str = "Authentication required",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            code="UNAUTHORIZED",
            message=message,
            status_code=401,
            details=details,
        )


app = Flask(__name__)


class User(BaseModel):
    """User model for validation."""

    username: str = Field(..., min_length=3, description="User's username")
    email: str = Field(
        ...,
        pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
        description="User's email",
    )
    age: int = Field(..., ge=18, description="User's age")


@app.errorhandler(APIError)
def handle_api_exception(error):
    """Handle API exceptions."""
    return handle_api_error(error)


@app.errorhandler(PydanticValidationError)
def handle_pydantic_validation_error(error):
    """Handle Pydantic validation errors."""
    field_errors = {}

    for err in error.errors():
        field = ".".join(str(loc) for loc in err["loc"])
        if field not in field_errors:
            field_errors[field] = []
        field_errors[field].append(err["msg"])

    return handle_api_error(ValidationError(field_errors))


@app.errorhandler(Exception)
def handle_exception(error):
    """Handle all other exceptions."""
    app.logger.exception("Unexpected error")
    return handle_api_error(
        CustomError(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred",
            status_code=500,
            details={"error": str(error)},
        ),
        include_traceback=app.debug,
    )


@app.route("/users/<user_id>", methods=["GET"])
@openapi_metadata(
    summary="Get a user by ID",
    description="Retrieve a user by their ID",
    tags=["users"],
)
def get_user(user_id):
    """Get a user by ID."""
    # Simulate a database lookup
    if user_id not in ["1", "2", "3"]:
        # Using the NotFoundError exception
        raise NotFoundError(
            resource_type="User",
            resource_id=user_id,
        )

    # Return a simulated user
    return jsonify(
        {
            "id": user_id,
            "username": f"user{user_id}",
            "email": f"user{user_id}@example.com",
            "age": 25,
        }
    )


@app.route("/users", methods=["POST"])
@openapi_metadata(
    summary="Create a new user",
    description="Create a new user with the provided data",
    tags=["users"],
)
def create_user():
    """Create a new user."""
    # Validate the request data against the User model
    data = request.get_json()
    if not data:
        raise CustomError(
            code="BAD_REQUEST",
            message="No JSON data provided",
            status_code=400,
        )

    # Pydantic validation errors will be caught by the global error handler
    user = User.model_validate(data)

    # Simulate a database operation
    user_id = "4"  # In a real app, this would be generated

    # Return the created user
    return jsonify(
        {
            "id": user_id,
            "username": user.username,
            "email": user.email,
            "age": user.age,
        }
    ), 201


@app.route("/protected", methods=["GET"])
@openapi_metadata(
    summary="Protected resource",
    description="Access a protected resource that requires authentication",
    tags=["auth"],
)
def protected_resource():
    """Access a protected resource."""
    # Check for Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise AuthenticationError(
            message="Authentication required",
            details={"header": "Authorization"},
        )

    # In a real app, you would validate the token
    token = auth_header.split(" ")[1]
    if token != "valid-token":
        raise AuthenticationError(
            message="Invalid token",
            details={"token": "invalid"},
        )

    return jsonify({"message": "You have access to the protected resource"})


if __name__ == "__main__":
    app.run(debug=True)
