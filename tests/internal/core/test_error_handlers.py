"""Tests for error handling utilities."""

import pytest
from pydantic import BaseModel, Field
from pydantic import ValidationError as PydanticValidationError

from flask_x_openapi_schema.core.error_handlers import (
    create_error_response,
    create_status_error_response,
    handle_api_error,
    handle_request_validation_error,
    handle_validation_error,
)
from flask_x_openapi_schema.models.base import BaseErrorResponse
from tests.internal.core.test_errors import DefaultAPIError


class TestErrorHandlers:
    """Tests for error handling utilities."""

    def test_create_error_response(self):
        """Test creating an error response."""
        response_data = create_error_response(
            error_code="TEST_ERROR",
            message="Test error message",
            details={"field": "test", "reason": "Invalid value"},
        )

        assert isinstance(response_data, dict)
        assert response_data["error"] == "TEST_ERROR"
        assert response_data["message"] == "Test error message"
        assert response_data["details"] == {"field": "test", "reason": "Invalid value"}

    def test_create_status_error_response(self):
        """Test creating an error response based on status code."""
        response, status_code = create_status_error_response(404, "Resource not found")

        assert status_code == 404
        assert response["error"] == "NOT_FOUND"
        assert response["message"] == "Resource not found"

    def test_create_status_error_response_default_message(self):
        """Test creating an error response with default message."""
        response, status_code = create_status_error_response(400)

        assert status_code == 400
        assert response["error"] == "BAD_REQUEST"
        assert response["message"] == "Bad Request"

    def test_handle_validation_error(self):
        """Test handling a Pydantic validation error."""

        class User(BaseModel):
            username: str = Field(..., min_length=3)

        try:
            User(username="a")
            pytest.fail("ValidationError not raised")
        except PydanticValidationError as e:
            response, status_code = handle_validation_error(e)

            assert status_code == 422
            assert response["error"] == "VALIDATION_ERROR"
            assert "validation error" in response["message"].lower()
            assert "username" in response["details"]
            assert "string_too_short" in response["details"]["username"]["type"].lower()

    def test_handle_request_validation_error_pydantic(self):
        """Test handling a request validation error with Pydantic error."""

        class User(BaseModel):
            username: str = Field(..., min_length=3)

        try:
            User(username="a")
            pytest.fail("ValidationError not raised")
        except PydanticValidationError as e:
            response, status_code = handle_request_validation_error("User", e)

            assert status_code == 422
            assert response["error"] == "VALIDATION_ERROR"
            assert "username" in response["details"]

    def test_handle_request_validation_error_other(self):
        """Test handling a request validation error with other exception."""
        error = ValueError("Invalid value")
        response, status_code = handle_request_validation_error("User", error)

        assert status_code == 400
        assert response["error"] == "VALIDATION_ERROR"
        assert "Failed to validate request against User" in response["message"]
        assert response["details"]["error"] == "Invalid value"

    def test_handle_api_error(self):
        """Test handling API errors."""
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

    def test_handle_api_error_with_custom_response_class(self):
        """Test handling API errors with custom response class."""

        class CustomErrorResponse(BaseErrorResponse):
            """Custom error response class."""

        error = DefaultAPIError(
            error_code="TEST_ERROR",
            message="Test error message",
            status_code=400,
            details={"field": "test"},
            error_response_class=CustomErrorResponse,
        )
        response, status_code = handle_api_error(error)

        assert status_code == 400
        assert response["error"] == "TEST_ERROR"
        assert response["message"] == "Test error message"
        assert response["details"] == {"field": "test"}

    def test_handle_api_error_with_pydantic_validation_error(self):
        """Test handling Pydantic validation errors."""

        class User(BaseModel):
            username: str = Field(..., min_length=3)

        try:
            User(username="a")
            pytest.fail("ValidationError not raised")
        except PydanticValidationError as e:
            response, status_code = handle_api_error(e)

            assert status_code == 422
            assert response["error"] == "VALIDATION_ERROR"
            assert "username" in response["details"]

    def test_handle_api_error_with_unexpected_error(self):
        """Test handling unexpected errors."""
        error = Exception("Unexpected error")
        result = handle_api_error(error)

        # Result is a tuple (response_data, status_code)
        assert isinstance(result, tuple)
        assert len(result) == 2

        response_data, status_code = result

        assert status_code == 500
        assert isinstance(response_data, dict)
        assert response_data["error"] == "INTERNAL_SERVER_ERROR"
        assert "unexpected error" in response_data["message"].lower()
        assert response_data["details"]["error"] == "Unexpected error"

    def test_handle_api_error_with_traceback(self):
        """Test handling API errors with traceback."""
        error = DefaultAPIError(
            error_code="TEST_ERROR",
            message="Test error message",
            status_code=400,
        )
        response, status_code = handle_api_error(error, include_traceback=True)

        assert status_code == 400
        assert response["error"] == "TEST_ERROR"
        assert "traceback" in response["details"]
        assert isinstance(response["details"]["traceback"], str)
