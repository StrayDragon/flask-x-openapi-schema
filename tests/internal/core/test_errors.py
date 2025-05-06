"""Test error implementations for testing purposes.

These error implementations are used for testing the APIError abstract base class.
They should not be used in production code.
"""

from typing import Any

from flask_x_openapi_schema.core.exceptions import APIError
from flask_x_openapi_schema.models.base import BaseErrorResponse


class DefaultAPIError(APIError):
    """Default implementation of APIError for testing.

    This class provides a standard implementation of APIError that is used for testing.
    It includes attributes for error code, message, status code, and details.

    Attributes:
        error_code: Error identifier or code.
        message: Human-readable error message.
        status_code: HTTP status code for the response.
        details: Optional additional error details.
        error_response_class: The error response class to use.
    """

    def __init__(
        self,
        error_code: str,
        message: str,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
        error_response_class: type[BaseErrorResponse] | None = None,
    ) -> None:
        """Initialize the API error.

        Args:
            error_code: Error identifier or code.
            message: Human-readable error message.
            status_code: HTTP status code for the response.
            details: Optional additional error details.
            error_response_class: The error response class to use.
        """
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.error_response_class = error_response_class
        super().__init__(message)

    def __str__(self) -> str:
        """Return the error message."""
        return self.message

    def to_response(self) -> tuple[dict[str, Any], int]:
        """Convert the error to a response tuple.

        Returns:
            A tuple containing the response data and HTTP status code.
        """
        from flask_x_openapi_schema.core.error_handlers import (
            DefaultErrorResponse,
            create_error_response,
        )

        response_class = self.error_response_class or DefaultErrorResponse

        response_data = create_error_response(
            error_code=self.error_code,
            message=self.message,
            details=self.details,
            error_response_class=response_class,
        )
        return response_data, self.status_code


class ValidationError(DefaultAPIError):
    """Exception raised for validation errors.

    This exception is raised when request data fails validation against
    a model schema. It includes details about the validation errors.
    """

    def __init__(
        self,
        message: str = "Validation error",
        details: dict[str, Any] | None = None,
        error_response_class: type[BaseErrorResponse] | None = None,
    ) -> None:
        """Initialize the validation error.

        Args:
            message: Human-readable error message.
            details: Optional additional error details.
            error_response_class: The error response class to use.
        """
        super().__init__(
            error_code="VALIDATION_ERROR",
            message=message,
            status_code=422,
            details=details,
            error_response_class=error_response_class,
        )
