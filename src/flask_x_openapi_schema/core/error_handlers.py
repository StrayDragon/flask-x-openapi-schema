"""Error handling utilities.

This module provides utilities for handling errors and generating consistent error responses.
It includes functions for creating error responses, mapping HTTP status codes to error types,
and handling validation errors.

Examples:
    Basic usage with Flask:

    ```python
    from flask import Flask
    from flask_x_openapi_schema.core.error_handlers import create_error_response

    app = Flask(__name__)


    @app.route("/example")
    def example():
        # Create an error response
        return create_error_response(
            error_code="VALIDATION_ERROR",
            message="Invalid input data",
            status_code=400,
            details={"field": "username", "reason": "Username is required"},
        )
    ```

    Using exceptions:

    ```python
    from flask import Flask, request
    from flask_x_openapi_schema.core.exceptions import APIError
    from flask_x_openapi_schema.core.error_handlers import handle_api_error

    app = Flask(__name__)


    @app.route("/example")
    def example():
        try:
            # Validate input
            if not request.json.get("username"):
                raise APIError(
                    error_code="VALIDATION_ERROR",
                    message="Invalid input data",
                    status_code=422,
                    details={"username": {"type": "value_error.missing", "msg": "Field required"}},
                )
            # Process request
            return {"result": "success"}
        except Exception as e:
            return handle_api_error(e)
    ```

"""

import logging
import traceback
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from flask_x_openapi_schema.core.exceptions import APIError
from flask_x_openapi_schema.models.base import BaseErrorResponse

logger = logging.getLogger(__name__)


class DefaultErrorResponse(BaseErrorResponse):
    """Default implementation of BaseErrorResponse.

    This class provides a standard implementation of BaseErrorResponse
    that can be used throughout the application for consistent error handling.
    """


# Map of HTTP status codes to error types
HTTP_STATUS_TO_ERROR_TYPE = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    406: "NOT_ACCEPTABLE",
    409: "CONFLICT",
    415: "UNSUPPORTED_MEDIA_TYPE",
    422: "VALIDATION_ERROR",
    429: "TOO_MANY_REQUESTS",
    500: "INTERNAL_SERVER_ERROR",
    501: "NOT_IMPLEMENTED",
    502: "BAD_GATEWAY",
    503: "SERVICE_UNAVAILABLE",
    504: "GATEWAY_TIMEOUT",
}


def create_error_response(
    error_code: str,
    message: str,
    details: dict[str, Any] | None = None,
    error_response_class: type[BaseErrorResponse] = DefaultErrorResponse,
) -> dict[str, Any]:
    """Create a standardized error response.

    This function creates a standardized error response using the provided
    error response class. It ensures that all error responses have a consistent
    format throughout the application.

    Args:
        error_code: Error identifier or code.
        message: Human-readable error message.
        details: Optional additional error details.
        error_response_class: The error response class to use.

    Returns:
        A dictionary containing the error response data.

    Examples:
        >>> response_data = create_error_response(
        ...     error_code="VALIDATION_ERROR",
        ...     message="Invalid input data",
        ...     status_code=400,
        ...     details={"field": "username", "reason": "Username is required"},
        ... )
        >>> response_data["error"]
        'VALIDATION_ERROR'

    """
    error = error_response_class(
        error=error_code,
        message=message,
        details=details,
    )
    # Get just the response data, not the status code
    return error.to_dict()


def get_error_code_for_status(status_code: int) -> str:
    """Get the error code for a given HTTP status code.

    Args:
        status_code: HTTP status code.

    Returns:
        The error code for the given status code.

    """
    return HTTP_STATUS_TO_ERROR_TYPE.get(status_code, f"ERROR_{status_code}")


def create_status_error_response(
    status_code: int,
    message: str | None = None,
    details: dict[str, Any] | None = None,
    error_response_class: type[BaseErrorResponse] = DefaultErrorResponse,
) -> tuple[dict[str, Any], int]:
    """Create an error response based on HTTP status code.

    This function creates a standardized error response using the provided
    HTTP status code. It automatically determines the error code based on
    the status code.

    Args:
        status_code: HTTP status code for the response.
        message: Human-readable error message. If not provided, a default
            message will be generated based on the status code.
        details: Optional additional error details.
        error_response_class: The error response class to use.

    Returns:
        A tuple containing the error response dictionary and the HTTP status code.

    Examples:
        >>> response = create_status_error_response(404, "User not found")
        >>> response[1]
        404
        >>> response[0]["error"]
        'NOT_FOUND'

    """
    error_code = get_error_code_for_status(status_code)

    if message is None:
        # Generate a default message based on the status code
        status_messages = {
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            405: "Method Not Allowed",
            406: "Not Acceptable",
            409: "Conflict",
            415: "Unsupported Media Type",
            422: "Validation Error",
            429: "Too Many Requests",
            500: "Internal Server Error",
            501: "Not Implemented",
            502: "Bad Gateway",
            503: "Service Unavailable",
            504: "Gateway Timeout",
        }
        message = status_messages.get(status_code, f"Error {status_code}")

    response_data = create_error_response(
        error_code=error_code,
        message=message,
        details=details,
        error_response_class=error_response_class,
    )
    return response_data, status_code


def handle_validation_error(
    error: PydanticValidationError,
    error_response_class: type[BaseErrorResponse] = DefaultErrorResponse,
) -> tuple[dict[str, Any], int]:
    """Handle Pydantic validation errors.

    This function creates a standardized error response for Pydantic validation
    errors. It extracts the validation error details and formats them in a
    consistent way.

    Args:
        error: The Pydantic validation error.
        error_response_class: The error response class to use.

    Returns:
        A tuple containing the error response dictionary and the HTTP status code.

    Examples:
        >>> from pydantic import BaseModel, Field, ValidationError
        >>> class User(BaseModel):
        ...     username: str = Field(..., min_length=3)
        >>> try:
        ...     User(username="a")
        ... except ValidationError as e:
        ...     response = handle_validation_error(e)
        >>> response[1]
        422
        >>> response[0]["error"]
        'VALIDATION_ERROR'

    """
    details = {}

    for error_item in error.errors():
        field = ".".join(str(loc) for loc in error_item["loc"])
        details[field] = {
            "type": error_item["type"],
            "msg": error_item["msg"],
        }

    response_data = create_error_response(
        error_code="VALIDATION_ERROR",
        message="Validation error",
        details=details,
        error_response_class=error_response_class,
    )
    return response_data, 422


def handle_request_validation_error(
    model_name: str,
    error: Exception,
    error_response_class: type[BaseErrorResponse] = DefaultErrorResponse,
) -> tuple[dict[str, Any], int]:
    """Handle request validation errors.

    This function creates a standardized error response for request validation
    errors. It is used when a request fails validation against a model.

    Args:
        model_name: The name of the model that failed validation.
        error: The exception that occurred during validation.
        error_response_class: The error response class to use.

    Returns:
        A tuple containing the error response dictionary and the HTTP status code.

    """
    if isinstance(error, PydanticValidationError):
        return handle_validation_error(error, error_response_class)

    logger.exception(f"Error validating request against model {model_name}")

    response_data = create_error_response(
        error_code="VALIDATION_ERROR",
        message=f"Failed to validate request against {model_name}",
        details={"error": str(error)},
        error_response_class=error_response_class,
    )
    return response_data, 400


def handle_api_error(
    error: Exception,
    error_response_class: type[BaseErrorResponse] = DefaultErrorResponse,
    include_traceback: bool = False,
) -> tuple[dict[str, Any], int]:
    """Handle API errors.

    This function creates a standardized error response for API errors.
    It handles both custom APIError exceptions and other exceptions.

    Args:
        error: The exception that occurred.
        error_response_class: The error response class to use for non-APIError exceptions.
        include_traceback: Whether to include the traceback in the response.
            This should only be enabled in development environments.

    Returns:
        A tuple containing the error response dictionary and the HTTP status code.

    Examples:
        >>> from flask_x_openapi_schema.core.exceptions import APIError
        >>> class CustomError(APIError):
        ...     def __init__(self, message: str):
        ...         self.message = message
        ...         super().__init__(message)
        ...
        ...     def to_response(self):
        ...         return {"error": "CUSTOM_ERROR", "message": self.message}, 400
        >>> try:
        ...     raise CustomError("Something went wrong")
        ... except Exception as e:
        ...     response = handle_api_error(e)
        >>> response[1]
        400
        >>> response[0]["error"]
        'CUSTOM_ERROR'

    """
    if isinstance(error, APIError):
        # Use the to_response method from the APIError subclass
        response_data, status_code = error.to_response()

        # Add traceback if requested
        if include_traceback and isinstance(response_data, dict):
            if "details" not in response_data:
                response_data["details"] = {}
            response_data["details"]["traceback"] = traceback.format_exc()

        return response_data, status_code

    if isinstance(error, PydanticValidationError):
        return handle_validation_error(error, error_response_class)

    # Handle unexpected exceptions
    logger.exception("Unexpected error occurred")

    # Create a default error response
    details = {"error": str(error)}

    response_data = create_error_response(
        error_code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred",
        details=details,
        error_response_class=error_response_class,
    )
    status_code = 500

    # Add traceback if requested
    if include_traceback and isinstance(response_data, dict):
        if "details" not in response_data:
            response_data["details"] = {}
        response_data["details"]["traceback"] = traceback.format_exc()

    return response_data, status_code
