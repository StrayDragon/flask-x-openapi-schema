"""Tests for the Flask-specific openapi_metadata decorator.

This module tests the openapi_metadata decorator for Flask and its functionality.
"""

from __future__ import annotations

import inspect

import pytest
from flask import Flask
from pydantic import BaseModel, Field

from flask_x_openapi_schema.i18n.i18n_string import set_current_language
from flask_x_openapi_schema.models.base import BaseRespModel
from flask_x_openapi_schema.models.file_models import FileUploadModel
from flask_x_openapi_schema.models.responses import (
    OpenAPIMetaResponse,
    OpenAPIMetaResponseItem,
)
from flask_x_openapi_schema.x.flask import openapi_metadata


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
    email: str | None = Field(None, description="The email")

    model_config = {"arbitrary_types_allowed": True}


class SampleQueryModel(BaseModel):
    """Test query model."""

    sort: str | None = Field(None, description="Sort order")
    limit: int | None = Field(None, description="Limit results")

    model_config = {"arbitrary_types_allowed": True}


class SampleResponseModel(BaseRespModel):
    """Test response model."""

    id: str = Field(..., description="The ID")
    name: str = Field(..., description="The name")
    age: int = Field(..., description="The age")
    email: str | None = Field(None, description="The email")


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
    summary = I18nString({"en-US": "Test endpoint", "zh-Hans": "测试端点"})

    description = I18nString({"en-US": "This is a test endpoint", "zh-Hans": "这是一个测试端点"})

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
    # Clear all caches to ensure a clean test environment
    from flask_x_openapi_schema.core.cache import clear_all_caches

    clear_all_caches()

    # Define a function with path parameters
    @openapi_metadata(summary="Test endpoint")
    def example_function(user_id: str, _x_path_user_id: str):
        # Use the path parameter to avoid linter warnings
        return {"user_id": user_id, "path_param": _x_path_user_id}

    # Check metadata
    metadata = example_function._openapi_metadata

    # Print metadata for debugging
    print(f"Metadata: {metadata}")

    # Assert that parameters is in metadata
    assert "parameters" in metadata, f"parameters not found in metadata: {metadata}"

    # Find the path parameters
    path_params = [p for p in metadata["parameters"] if p["in"] == "path"]
    assert len(path_params) == 1, f"Expected 1 path parameter, got {len(path_params)}: {path_params}"

    # Check parameter details
    user_id_param = path_params[0]
    assert user_id_param["name"] == "user_id", f"Expected parameter name 'user_id', got '{user_id_param['name']}'"
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


def test_openapi_metadata_parameter_extraction():
    """Test extraction of parameters based on prefixes in openapi_metadata decorator."""
    # Clear all caches to ensure a clean test environment
    from flask_x_openapi_schema.core.cache import clear_all_caches

    clear_all_caches()

    # Import necessary modules
    import inspect

    from flask_x_openapi_schema.core.config import ConventionalPrefixConfig
    from flask_x_openapi_schema.core.decorator_base import (
        _extract_parameters_from_prefixes,
        _generate_openapi_metadata,
    )

    # Define a function with multiple parameter types
    @openapi_metadata(summary="Test endpoint")
    def example_function_mixed(
        _x_body: SampleRequestModel,
        _x_query: SampleQueryModel,
        _x_path_user_id: str,
    ):
        # Use parameters to avoid linter warnings
        return {
            "body": str(_x_body) if _x_body else None,
            "query": str(_x_query) if _x_query else None,
            "user_id": _x_path_user_id,
        }

    # Force parameter extraction
    signature = inspect.signature(example_function_mixed)
    type_hints = {}
    try:
        type_hints = inspect.get_type_hints(example_function_mixed)
    except Exception:
        # Fall back to __annotations__ if get_type_hints fails
        type_hints = getattr(example_function_mixed, "__annotations__", {})

    # Extract parameters manually
    config = ConventionalPrefixConfig()
    request_body, query_model, path_params = _extract_parameters_from_prefixes(signature, type_hints, config)

    # Print debug information
    print(f"Extracted request_body: {request_body}")
    print(f"Extracted query_model: {query_model}")
    print(f"Extracted path_params: {path_params}")

    # Check that parameters were extracted correctly
    assert request_body == SampleRequestModel, "Request body model not extracted correctly"
    assert query_model == SampleQueryModel, "Query model not extracted correctly"
    assert path_params == ["user_id"], "Path parameters not extracted correctly"

    # Generate metadata manually to verify it works correctly
    metadata = _generate_openapi_metadata(
        summary="Test endpoint",
        description=None,
        tags=None,
        operation_id=None,
        deprecated=False,
        security=None,
        external_docs=None,
        actual_request_body=request_body,
        responses=None,
        language=None,
    )

    # Print metadata for debugging
    print(f"Generated metadata: {metadata}")

    # Check request body in generated metadata
    assert "requestBody" in metadata, f"requestBody not found in metadata: {metadata}"
    assert "content" in metadata["requestBody"]
    assert "application/json" in metadata["requestBody"]["content"]
    assert "schema" in metadata["requestBody"]["content"]["application/json"]
    assert "$ref" in metadata["requestBody"]["content"]["application/json"]["schema"]
    assert (
        metadata["requestBody"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/SampleRequestModel"
    )


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


def test_openapi_metadata_wrapper_preserves_signature():
    """Test that the wrapper function preserves the original function's signature."""
    # Clear all caches to ensure a clean test environment
    from flask_x_openapi_schema.core.cache import clear_all_caches

    clear_all_caches()

    # Define a function with multiple parameters
    @openapi_metadata(summary="Test endpoint")
    def example_function(_x_body: SampleRequestModel, _x_query: SampleQueryModel):
        # Use parameters to avoid linter warnings
        return {
            "body": str(_x_body) if _x_body else None,
            "query": str(_x_query) if _x_query else None,
        }

    # Check that the wrapper has the same signature as the original function
    signature = inspect.signature(example_function)
    assert "_x_body" in signature.parameters, f"_x_body not found in signature parameters: {signature.parameters}"
    assert "_x_query" in signature.parameters, f"_x_query not found in signature parameters: {signature.parameters}"

    # Check that type annotations are preserved
    annotations = example_function.__annotations__
    assert "_x_body" in annotations, f"_x_body not found in annotations: {annotations}"
    assert annotations["_x_body"] == SampleRequestModel, (
        f"Expected _x_body annotation to be SampleRequestModel, got {annotations['_x_body']}"
    )
    assert "_x_query" in annotations, f"_x_query not found in annotations: {annotations}"
    assert annotations["_x_query"] == SampleQueryModel, (
        f"Expected _x_query annotation to be SampleQueryModel, got {annotations['_x_query']}"
    )


def test_openapi_metadata_response_conversion():
    """Test that BaseRespModel instances are converted to Flask responses."""

    @openapi_metadata(summary="Test endpoint")
    def test_function():
        return SampleResponseModel(id="123", name="Test", age=30)

    # Call the function
    response = test_function()

    # The response could be a dict or a tuple depending on the implementation
    # Check that the response contains the expected data
    if isinstance(response, tuple):
        # If it's a tuple (data, status_code)
        assert len(response) == 2
        assert isinstance(response[0], dict)
        assert response[1] == 200
        data = response[0]
    else:
        # If it's just a dict
        assert isinstance(response, dict)
        data = response

    # Check response data
    assert data["id"] == "123"
    assert data["name"] == "Test"
    assert data["age"] == 30


def test_openapi_metadata_response_with_status_code():
    """Test that BaseRespModel instances with status codes are converted correctly."""

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
