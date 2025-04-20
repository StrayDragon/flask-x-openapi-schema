"""
Tests for the Flask-specific openapi_metadata decorator.

This module tests the openapi_metadata decorator for Flask and its functionality.
"""

import inspect
import pytest
from flask import Flask
from pydantic import BaseModel, Field
from typing import Optional

from flask_x_openapi_schema.x.flask import openapi_metadata
from flask_x_openapi_schema.models.base import BaseRespModel
from flask_x_openapi_schema.i18n.i18n_string import set_current_language
from flask_x_openapi_schema.models.file_models import FileUploadModel


# Create a mock I18nString class that works with Pydantic v2
class I18nString:
    """Mock I18nString class for testing."""

    def __init__(self, value, default_language="en-US"):
        if isinstance(value, dict):
            self.value = value
        else:
            self.value = {default_language: str(value)}
        self.default_language = default_language

    def get(self, language=None):
        """Get the string for the specified language."""
        language = language or self.default_language
        return self.value.get(language, self.value.get(self.default_language, ""))

    def __str__(self):
        """Get the string for the current language."""
        return self.get()

    # Make the class JSON serializable
    def __iter__(self):
        yield self.get()

    # For JSON serialization in json.dumps
    def __json__(self):
        return self.get()


# Define test models
class SampleRequestModel(BaseModel):
    """Test request model."""

    name: str = Field(..., description="The name")
    age: int = Field(..., description="The age")
    email: Optional[str] = Field(None, description="The email")

    model_config = {"arbitrary_types_allowed": True}


class SampleQueryModel(BaseModel):
    """Test query model."""

    sort: Optional[str] = Field(None, description="Sort order")
    limit: Optional[int] = Field(None, description="Limit results")

    model_config = {"arbitrary_types_allowed": True}


class SampleResponseModel(BaseRespModel):
    """Test response model."""

    id: str = Field(..., description="The ID")
    name: str = Field(..., description="The name")
    age: int = Field(..., description="The age")
    email: Optional[str] = Field(None, description="The email")

    model_config = {"arbitrary_types_allowed": True}


@pytest.fixture
def app():
    """Create a Flask app for testing."""
    app = Flask(__name__)
    return app


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
    summary = I18nString({"en-US": "Test endpoint", "zh-Hans": "测试端点"})

    description = I18nString(
        {"en-US": "This is a test endpoint", "zh-Hans": "这是一个测试端点"}
    )

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
        return {"message": "你好，世界！"}

    # Check metadata in Chinese
    metadata = test_function_zh._openapi_metadata
    assert metadata["summary"] == "测试端点"
    assert metadata["description"] == "这是一个测试端点"

    # Reset language to English for other tests
    set_current_language("en-US")


def test_openapi_metadata_with_request_body():
    """Test openapi_metadata decorator with request body."""

    @openapi_metadata(summary="Test endpoint")
    def test_function(x_request_body: SampleRequestModel):
        return {"name": x_request_body.name, "age": x_request_body.age}

    # Check metadata
    metadata = test_function._openapi_metadata
    assert "requestBody" in metadata
    assert (
        metadata["requestBody"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/SampleRequestModel"
    )
    assert metadata["requestBody"]["required"] is True


def test_openapi_metadata_with_query_model():
    """Test openapi_metadata decorator with query model."""

    @openapi_metadata(summary="Test endpoint")
    def test_function(x_request_query: SampleQueryModel):
        return {"sort": x_request_query.sort, "limit": x_request_query.limit}

    # Check metadata
    metadata = test_function._openapi_metadata
    assert "parameters" in metadata

    # Find the query parameters
    query_params = [p for p in metadata["parameters"] if p["in"] == "query"]
    assert len(query_params) == 2

    # Check parameter details
    sort_param = next((p for p in query_params if p["name"] == "sort"), None)
    assert sort_param is not None
    assert sort_param["description"] == "Sort order"
    assert sort_param["required"] is False

    limit_param = next((p for p in query_params if p["name"] == "limit"), None)
    assert limit_param is not None
    assert limit_param["description"] == "Limit results"
    assert limit_param["required"] is False


def test_openapi_metadata_with_path_params():
    """Test openapi_metadata decorator with path parameters."""

    @openapi_metadata(summary="Test endpoint")
    def test_function(user_id: str, x_request_path_user_id: str):
        return {"user_id": user_id}

    # Check metadata
    metadata = test_function._openapi_metadata
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
        responses={
            "200": {
                "description": "Successful response",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/TestResponseModel"}
                    }
                },
            },
            "404": {"description": "Not found"},
        },
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


def test_openapi_metadata_parameter_extraction():
    """Test extraction of parameters based on prefixes in openapi_metadata decorator."""

    @openapi_metadata(summary="Test endpoint")
    def test_function(
        x_request_body: SampleRequestModel,
        x_request_query: SampleQueryModel,
        x_request_path_user_id: str,
    ):
        return {"message": "Success"}

    # Check metadata
    metadata = test_function._openapi_metadata

    # Check request body
    assert "requestBody" in metadata
    assert (
        metadata["requestBody"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/SampleRequestModel"
    )

    # Check parameters
    assert "parameters" in metadata

    # Find query parameters
    query_params = [p for p in metadata["parameters"] if p["in"] == "query"]
    assert len(query_params) == 2

    # Find path parameters
    path_params = [p for p in metadata["parameters"] if p["in"] == "path"]
    assert len(path_params) == 1
    assert path_params[0]["name"] == "user_id"


def test_openapi_metadata_with_file_upload():
    """Test openapi_metadata decorator with file upload."""

    @openapi_metadata(summary="Test file upload")
    def test_function(x_request_file: FileUploadModel):
        return {"filename": x_request_file.file.filename}

    # Check metadata
    metadata = test_function._openapi_metadata

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


def test_openapi_metadata_wrapper_preserves_signature():
    """Test that the wrapper function preserves the original function's signature."""

    @openapi_metadata(summary="Test endpoint")
    def test_function(
        x_request_body: SampleRequestModel, x_request_query: SampleQueryModel
    ):
        return {"message": "Success"}

    # Check that the wrapper has the same signature as the original function
    signature = inspect.signature(test_function)
    assert "x_request_body" in signature.parameters
    assert "x_request_query" in signature.parameters

    # Check that type annotations are preserved
    annotations = test_function.__annotations__
    assert "x_request_body" in annotations
    assert annotations["x_request_body"] == SampleRequestModel
    assert "x_request_query" in annotations
    assert annotations["x_request_query"] == SampleQueryModel


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


def test_openapi_metadata_response_with_status_code():
    """Test that BaseRespModel instances with status codes are converted correctly."""
    # Create a mock BaseRespModel.to_response method
    original_to_response = BaseRespModel.to_response

    def mock_to_response(self, status_code=200):
        return self.model_dump(), status_code

    # Monkey patch the to_response method
    BaseRespModel.to_response = mock_to_response

    try:

        @openapi_metadata(summary="Test endpoint")
        def test_function():
            return SampleResponseModel(id="123", name="Test", age=30), 201

        # Call the function
        response = test_function()

        # Check that the response is a tuple (data, status_code)
        assert isinstance(response, tuple)
        assert len(response) == 2
        assert isinstance(response[0], dict)
        assert response[1] == 201

        # Check response data
        assert response[0]["id"] == "123"
        assert response[0]["name"] == "Test"
        assert response[0]["age"] == 30
    finally:
        # Restore the original method
        BaseRespModel.to_response = original_to_response