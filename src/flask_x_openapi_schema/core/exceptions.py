"""Exceptions for Flask-X-OpenAPI-Schema.

This module defines the abstract base exception class for API errors.
This exception is designed to be extended by users to create custom error types
with complete freedom to define their own error structure and behavior.

Users MUST extend this class to create their own error types. Direct instantiation
of APIError is not allowed and will raise a TypeError.
"""

from abc import ABC, abstractmethod
from typing import Any, Self, TypeVar

T = TypeVar("T", bound="APIError")


class APIError(Exception, ABC):
    """Abstract base exception for all API errors.

    This exception serves as the abstract base class for all API-related exceptions.
    Users MUST extend this class to create custom error types with their own
    structure and behavior. Direct instantiation of APIError is not allowed.

    The only required method to implement is `to_response()`, which should return
    a tuple containing the response data and HTTP status code.

    Examples:
        Creating a custom error type:
        >>> class CustomError(APIError):
        ...     def __init__(self, message: str, code: str = "ERROR", status: int = 400):
        ...         self.message = message
        ...         self.code = code
        ...         self.status = status
        ...         super().__init__(message)
        ...
        ...     def to_response(self) -> tuple[dict[str, Any], int]:
        ...         return {
        ...             "error": self.code,
        ...             "message": self.message,
        ...             "timestamp": "2023-05-05T12:00:00Z",  # You could use real timestamp
        ...         }, self.status
        >>> try:
        ...     raise CustomError("Something went wrong", code="CUSTOM_ERROR", status=400)
        ... except CustomError as e:
        ...     response_data, status_code = e.to_response()
        ...     print(f"Status: {status_code}, Error: {response_data['error']}")
        Status: 400, Error: CUSTOM_ERROR

        Creating a more complex error type:
        >>> class ValidationError(APIError):
        ...     def __init__(self, field_errors: dict[str, str]):
        ...         self.field_errors = field_errors
        ...         message = "Validation failed"
        ...         super().__init__(message)
        ...
        ...     def to_response(self) -> tuple[dict[str, Any], int]:
        ...         return {
        ...             "error": "VALIDATION_ERROR",
        ...             "message": str(self),
        ...             "details": {"fields": self.field_errors},
        ...         }, 422

    """

    def __new__(cls, *args: Any, **kwargs: Any) -> Self:  # noqa: ARG004
        """Create a new instance of APIError.

        This method checks if the class being instantiated is APIError itself.
        If it is, it raises a TypeError. This ensures that users must extend
        APIError to create their own error types.

        Raises:
            TypeError: If attempting to instantiate APIError directly.

        Returns:
            A new instance of the subclass.

        """
        if cls is APIError:
            msg = (
                "APIError is an abstract base class and cannot be instantiated directly. "
                "You must create a subclass that implements the to_response() method."
            )
            raise TypeError(msg)
        return super().__new__(cls)

    def __init__(self, message: str) -> None:
        """Initialize the API error.

        Args:
            message: Human-readable error message.

        """
        self.message = message
        super().__init__(message)

    def __str__(self) -> str:
        """Return the error message."""
        return self.message

    @abstractmethod
    def to_response(self) -> tuple[dict[str, Any], int]:
        """Convert the error to a response tuple.

        This method should be implemented by subclasses to define how the error
        is converted to a response. The response should be a tuple containing
        the response data (as a dictionary) and the HTTP status code.

        Returns:
            A tuple containing the response data and HTTP status code.

        """
        error_message = "Subclasses must implement to_response()"
        raise NotImplementedError(error_message)
