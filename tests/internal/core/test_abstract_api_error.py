"""Tests for abstract APIError class."""

from typing import Any

import pytest

from flask_x_openapi_schema.core.error_handlers import handle_api_error
from flask_x_openapi_schema.core.exceptions import APIError


class CustomError(APIError):
    """Custom error implementation for testing."""

    def __init__(self, message: str, code: str = "ERROR", status: int = 400):
        self.message = message
        self.code = code
        self.status = status
        super().__init__(message)

    def to_response(self) -> tuple[dict[str, Any], int]:
        """Convert the error to a response tuple."""
        return {
            "error": self.code,
            "message": self.message,
        }, self.status


class TestAbstractAPIError:
    """Tests for abstract APIError class."""

    def test_abstract_api_error(self):
        """Test that APIError is abstract and cannot be instantiated directly."""
        # APIError should not be instantiable directly
        with pytest.raises(TypeError):
            APIError("This should fail")

    def test_custom_error(self):
        """Test custom error implementation."""
        error = CustomError("Something went wrong", code="CUSTOM_ERROR", status=400)

        assert str(error) == "Something went wrong"
        assert error.code == "CUSTOM_ERROR"
        assert error.status == 400

        response_data, status_code = error.to_response()

        assert status_code == 400
        assert response_data["error"] == "CUSTOM_ERROR"
        assert response_data["message"] == "Something went wrong"

    def test_handle_api_error_with_custom_error(self):
        """Test handling custom error with handle_api_error."""
        error = CustomError("Something went wrong", code="CUSTOM_ERROR", status=400)
        response_data, status_code = handle_api_error(error)

        assert status_code == 400
        assert response_data["error"] == "CUSTOM_ERROR"
        assert response_data["message"] == "Something went wrong"

    def test_handle_api_error_with_traceback(self):
        """Test handling custom error with traceback."""
        error = CustomError("Something went wrong", code="CUSTOM_ERROR", status=400)
        response_data, status_code = handle_api_error(error, include_traceback=True)

        assert status_code == 400
        assert response_data["error"] == "CUSTOM_ERROR"
        assert response_data["message"] == "Something went wrong"
        # Traceback should be added to details
        assert "details" in response_data
        assert "traceback" in response_data["details"]

    def test_complex_custom_error(self):
        """Test a more complex custom error implementation."""

        class ValidationError(APIError):
            """Validation error implementation for testing."""

            def __init__(self, field_errors: dict[str, str]):
                self.field_errors = field_errors
                message = "Validation failed"
                super().__init__(message)

            def to_response(self) -> tuple[dict[str, Any], int]:
                """Convert the error to a response tuple."""
                return {
                    "error": "VALIDATION_ERROR",
                    "message": str(self),
                    "details": {"fields": self.field_errors},
                }, 422

        error = ValidationError({"username": "Required", "email": "Invalid format"})
        response_data, status_code = error.to_response()

        assert status_code == 422
        assert response_data["error"] == "VALIDATION_ERROR"
        assert response_data["message"] == "Validation failed"
        assert response_data["details"]["fields"] == {"username": "Required", "email": "Invalid format"}

        # Test with handle_api_error
        response_data, status_code = handle_api_error(error)

        assert status_code == 422
        assert response_data["error"] == "VALIDATION_ERROR"
        assert response_data["message"] == "Validation failed"
        assert response_data["details"]["fields"] == {"username": "Required", "email": "Invalid format"}

        # Test with traceback
        response_data, status_code = handle_api_error(error, include_traceback=True)

        assert status_code == 422
        assert response_data["error"] == "VALIDATION_ERROR"
        assert response_data["message"] == "Validation failed"
        assert response_data["details"]["fields"] == {"username": "Required", "email": "Invalid format"}
        assert "traceback" in response_data["details"]
