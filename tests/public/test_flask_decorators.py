"""Tests for the Flask-specific openapi_metadata decorator.

This module tests the public API of the openapi_metadata decorator for Flask.
"""

from __future__ import annotations

import pytest
from flask import Flask
from pydantic import BaseModel, Field

from flask_x_openapi_schema.i18n.i18n_string import I18nStr, set_current_language
from flask_x_openapi_schema.models.base import BaseRespModel
from flask_x_openapi_schema.models.file_models import FileUploadModel
from flask_x_openapi_schema.models.responses import (
    OpenAPIMetaResponse,
    OpenAPIMetaResponseItem,
)
from flask_x_openapi_schema.x.flask import openapi_metadata


# Define test models
class SampleRequestModel(BaseModel):
    """Test request model."""

    name: str = Field(..., description="The name")
    age: int = Field(..., description="The age")
    email: str | None = Field(None, description="The email")


class SampleQueryModel(BaseModel):
    """Test query model."""

    sort: str | None = Field(None, description="Sort order")
    limit: int | None = Field(None, description="Limit results")


class SampleResponseModel(BaseRespModel):
    """Test response model."""

    id: str = Field(..., description="The ID")
    name: str = Field(..., description="The name")
    age: int = Field(..., description="The age")


@pytest.fixture
def app():
    """Create a Flask app for testing."""
    return Flask(__name__)


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()


def test_openapi_metadata_basic():
    """Test basic functionality of openapi_metadata decorator."""

    @openapi_metadata(
        summary="Test endpoint",
        description="This is a test endpoint",
        tags=["test"],
        operation_id="testEndpoint",
        deprecated=False,
    )
    def test_function():
        return {"message": "Hello, world!"}

    # Check that metadata was attached to the function
    assert hasattr(test_function, "_openapi_metadata")
    metadata = test_function._openapi_metadata

    # Check metadata values
    assert metadata["summary"] == "Test endpoint"
    assert metadata["description"] == "This is a test endpoint"
    assert metadata["tags"] == ["test"]
    assert metadata["operationId"] == "testEndpoint"
    assert "deprecated" not in metadata  # False values are not included


def test_openapi_metadata_with_i18n():
    """Test openapi_metadata decorator with I18nString objects."""
    # Set up I18nString objects
    summary = I18nStr({"en-US": "Test endpoint", "zh-Hans": "测试端点"})
    description = I18nStr({"en-US": "This is a test endpoint", "zh-Hans": "这是一个测试端点"})

    # Set language to English
    set_current_language("en-US")

    # Apply the decorator
    @openapi_metadata(summary=summary, description=description, tags=["test"])
    def test_function():
        return {"message": "Hello, world!"}

    # Check metadata in English
    metadata = test_function._openapi_metadata
    assert str(metadata["summary"]) == "Test endpoint"
    assert str(metadata["description"]) == "This is a test endpoint"

    # Change language to Chinese
    set_current_language("zh-Hans")

    # Apply the decorator with Chinese text
    @openapi_metadata(summary="测试端点", description="这是一个测试端点", tags=["test"])
    def test_function_zh():
        return {"message": "你好,世界！"}

    # Check metadata in Chinese
    metadata = test_function_zh._openapi_metadata
    assert metadata["summary"] == "测试端点"
    assert metadata["description"] == "这是一个测试端点"

    # Reset language to English for other tests
    set_current_language("en-US")


def test_openapi_metadata_with_path_params():
    """Test openapi_metadata decorator with path parameters."""

    # Define a function with path parameters
    @openapi_metadata(summary="Test endpoint")
    def example_function(user_id: str, _x_path_user_id: str):
        # Use the path parameter to avoid linter warnings
        return {"user_id": user_id, "path_param": _x_path_user_id}

    # Check metadata
    metadata = example_function._openapi_metadata

    # Assert that parameters is in metadata
    assert "parameters" in metadata

    # Find the path parameters
    path_params = [p for p in metadata["parameters"] if p["in"] == "path"]
    assert len(path_params) == 1

    # Check parameter details
    user_id_param = path_params[0]
    assert user_id_param["name"] == "user_id"
    assert user_id_param["required"] is True


def test_openapi_metadata_with_responses():
    """Test openapi_metadata decorator with responses."""

    @openapi_metadata(
        summary="Test endpoint",
        responses=OpenAPIMetaResponse(
            responses={
                "200": OpenAPIMetaResponseItem(
                    model=SampleResponseModel,
                    description="Successful response",
                ),
                "404": OpenAPIMetaResponseItem(
                    description="Not found",
                ),
            },
        ),
    )
    def test_function():
        return SampleResponseModel(id="123", name="Test", age=30)

    # Check metadata
    metadata = test_function._openapi_metadata
    assert "responses" in metadata
    assert "200" in metadata["responses"]
    assert "404" in metadata["responses"]
    assert metadata["responses"]["200"]["description"] == "Successful response"
    assert metadata["responses"]["404"]["description"] == "Not found"


def test_openapi_metadata_with_file_upload():
    """Test openapi_metadata decorator with file upload."""

    @openapi_metadata(summary="Test file upload")
    def example_function(_x_file: FileUploadModel):
        return {"filename": _x_file.file.filename}

    # Check metadata
    metadata = example_function._openapi_metadata

    # Check parameters
    assert "parameters" in metadata

    # Find file parameters
    file_params = [p for p in metadata["parameters"] if p.get("type") == "file"]
    assert len(file_params) == 1
    assert file_params[0]["name"] == "file"
    assert file_params[0]["in"] == "formData"
    assert file_params[0]["required"] is True

    # Check consumes property
    assert "consumes" in metadata
    assert metadata["consumes"] == ["multipart/form-data"]


def test_openapi_metadata_response_conversion():
    """Test that BaseRespModel instances are converted to Flask responses."""
    # Create a mock BaseRespModel.to_response method
    original_to_response = BaseRespModel.to_response

    def mock_to_response(self, status_code=200):
        return self.model_dump(), status_code

    # Monkey patch the to_response method
    BaseRespModel.to_response = mock_to_response

    try:

        @openapi_metadata(summary="Test endpoint")
        def test_function():
            return SampleResponseModel(id="123", name="Test", age=30)

        # Call the function
        response = test_function()

        # Check that the response is a tuple (data, status_code)
        assert isinstance(response, tuple)
        assert len(response) == 2
        assert isinstance(response[0], dict)
        assert response[1] == 200

        # Check response data
        assert response[0]["id"] == "123"
        assert response[0]["name"] == "Test"
        assert response[0]["age"] == 30
    finally:
        # Restore the original method
        BaseRespModel.to_response = original_to_response
