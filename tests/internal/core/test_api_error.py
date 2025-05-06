"""Tests for custom error implementations."""

from flask_x_openapi_schema.core.error_handlers import handle_api_error
from flask_x_openapi_schema.core.exceptions import APIError
from flask_x_openapi_schema.models.base import BaseErrorResponse
from tests.internal.core.test_errors import DefaultAPIError


class TestCustomErrors:
    """Tests for custom error implementations."""

    def test_default_api_error(self):
        """Test DefaultAPIError class."""
        error = DefaultAPIError(
            error_code="TEST_ERROR",
            message="Test error message",
            status_code=400,
            details={"field": "test"},
        )

        assert error.error_code == "TEST_ERROR"
        assert error.message == "Test error message"
        assert error.status_code == 400
        assert error.details == {"field": "test"}
        assert str(error) == "Test error message"

    def test_default_api_error_with_custom_response_class(self):
        """Test DefaultAPIError with custom response class."""

        class CustomErrorResponse(BaseErrorResponse):
            """Custom error response class."""

        error = DefaultAPIError(
            error_code="TEST_ERROR",
            message="Test error message",
            status_code=400,
            details={"field": "test"},
            error_response_class=CustomErrorResponse,
        )

        assert error.error_response_class == CustomErrorResponse

    def test_handle_default_api_error(self):
        """Test handling DefaultAPIError."""
        error = DefaultAPIError(
            error_code="TEST_ERROR",
            message="Test error message",
            status_code=400,
            details={"field": "test"},
        )
        response, status_code = handle_api_error(error)

        assert status_code == 400
        assert response["error"] == "TEST_ERROR"
        assert response["message"] == "Test error message"
        assert response["details"] == {"field": "test"}

    def test_custom_error_type(self):
        """Test creating a custom error type."""

        class NotFoundError(APIError):
            """Exception raised when a requested resource is not found."""

            def __init__(
                self,
                resource_type: str,
                resource_id: str,
                message: str | None = None,
                details: dict | None = None,
            ):
                if message is None:
                    message = f"{resource_type} with ID {resource_id} not found"

                self.resource_type = resource_type
                self.resource_id = resource_id
                self.status_code = 404
                self.details = details or {"resource_type": resource_type, "resource_id": resource_id}
                super().__init__(message)

            def to_response(self) -> tuple[dict[str, object], int]:
                """Convert the error to a response tuple."""
                return {
                    "error": "NOT_FOUND",
                    "message": str(self),
                    "details": self.details,
                }, self.status_code

        error = NotFoundError("User", "123")
        response_data, status_code = error.to_response()

        assert status_code == 404
        assert response_data["error"] == "NOT_FOUND"
        assert response_data["message"] == "User with ID 123 not found"
        assert response_data["details"] == {"resource_type": "User", "resource_id": "123"}

        # Test with custom message
        error = NotFoundError("User", "123", message="Custom not found message")
        response_data, status_code = error.to_response()

        assert status_code == 404
        assert response_data["error"] == "NOT_FOUND"
        assert response_data["message"] == "Custom not found message"

        # Test with custom details
        error = NotFoundError("User", "123", details={"custom": "details"})
        response_data, status_code = error.to_response()

        assert status_code == 404
        assert response_data["details"] == {"custom": "details"}

    def test_handle_custom_error_type(self):
        """Test handling custom error types."""

        class ValidationError(APIError):
            """Exception raised for validation errors."""

            def __init__(
                self,
                message: str = "Validation error",
                details: dict | None = None,
            ):
                self.message = message
                self.details = details or {}
                super().__init__(message)

            def to_response(self) -> tuple[dict[str, object], int]:
                """Convert the error to a response tuple."""
                return {
                    "error": "VALIDATION_ERROR",
                    "message": self.message,
                    "details": self.details,
                }, 422

        error = ValidationError(
            message="Invalid input data",
            details={"field": "username", "reason": "Required"},
        )
        response, status_code = handle_api_error(error)

        assert status_code == 422
        assert response["error"] == "VALIDATION_ERROR"
        assert response["message"] == "Invalid input data"
        assert response["details"] == {"field": "username", "reason": "Required"}
