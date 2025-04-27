"""Tests for the param_binding module.

This module tests the parameter binding strategy pattern implementation.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from flask import Flask, request
from pydantic import BaseModel, Field

from flask_x_openapi_schema.core.config import ConventionalPrefixConfig
from flask_x_openapi_schema.core.param_binding import (
    FileParameterBindingStrategy,
    ParameterBindingStrategyFactory,
    ParameterProcessor,
    PathParameterBindingStrategy,
    QueryParameterBindingStrategy,
    RequestBodyBindingStrategy,
)


# Define test models
class SampleRequestModel(BaseModel):
    """Test request model."""

    name: str = Field(..., description="The name")
    age: int = Field(..., description="The age")


class SampleQueryModel(BaseModel):
    """Test query model."""

    q: str = Field(..., description="Search query")
    limit: int = Field(10, description="Result limit")


class SampleFileModel(BaseModel):
    """Test file model."""

    file: object = Field(..., description="The file")
    description: str = Field("", description="File description")

    model_config = {
        "arbitrary_types_allowed": True,
    }


@pytest.fixture
def app():
    """Create a Flask app for testing."""
    return Flask(__name__)


def test_parameter_binding_strategy_factory():
    """Test ParameterBindingStrategyFactory."""
    # Test creating body strategy
    strategy = ParameterBindingStrategyFactory.create_strategy("body")
    assert isinstance(strategy, RequestBodyBindingStrategy)

    # Test creating query strategy
    strategy = ParameterBindingStrategyFactory.create_strategy("query")
    assert isinstance(strategy, QueryParameterBindingStrategy)

    # Test creating path strategy
    strategy = ParameterBindingStrategyFactory.create_strategy("path")
    assert isinstance(strategy, PathParameterBindingStrategy)

    # Test creating file strategy
    strategy = ParameterBindingStrategyFactory.create_strategy("file")
    assert isinstance(strategy, FileParameterBindingStrategy)

    # Test with unsupported parameter type
    with pytest.raises(ValueError, match="Unsupported parameter type: unsupported"):
        ParameterBindingStrategyFactory.create_strategy("unsupported")


def test_request_body_binding_strategy():
    """Test RequestBodyBindingStrategy."""
    strategy = RequestBodyBindingStrategy()

    # Create a mock framework decorator
    mock_decorator = MagicMock()
    mock_decorator.process_request_body.return_value = {"_x_body": {"name": "Test", "age": 30}}

    # Test binding a parameter
    kwargs = {}
    result = strategy.bind_parameter("_x_body", SampleRequestModel, kwargs, mock_decorator)

    # Check that the framework decorator's process_request_body method was called
    mock_decorator.process_request_body.assert_called_once_with("_x_body", SampleRequestModel, {})

    # Check the result
    assert result == {"_x_body": {"name": "Test", "age": 30}}


def test_query_parameter_binding_strategy():
    """Test QueryParameterBindingStrategy."""
    strategy = QueryParameterBindingStrategy()

    # Create a mock framework decorator
    mock_decorator = MagicMock()
    mock_decorator.process_query_params.return_value = {"_x_query": {"q": "test", "limit": 20}}

    # Test binding a parameter
    kwargs = {}
    result = strategy.bind_parameter("_x_query", SampleQueryModel, kwargs, mock_decorator)

    # Check that the framework decorator's process_query_params method was called
    mock_decorator.process_query_params.assert_called_once_with("_x_query", SampleQueryModel, {})

    # Check the result
    assert result == {"_x_query": {"q": "test", "limit": 20}}


def test_path_parameter_binding_strategy():
    """Test PathParameterBindingStrategy."""
    strategy = PathParameterBindingStrategy()

    # Test binding a parameter
    kwargs = {"user_id": "123"}
    result = strategy.bind_parameter("_x_path_user_id", None, kwargs, None)

    # Check the result
    assert result == {"user_id": "123", "_x_path_user_id": "123"}

    # Test with custom prefix
    custom_config = ConventionalPrefixConfig(request_path_prefix="custom_path")
    strategy = PathParameterBindingStrategy(custom_config)

    # Test binding a parameter with custom prefix
    kwargs = {"user_id": "123"}
    result = strategy.bind_parameter("custom_path_user_id", None, kwargs, None)

    # Check the result
    assert result == {"user_id": "123", "custom_path_user_id": "123"}


@pytest.mark.usefixtures("app")
def test_file_parameter_binding_strategy(app):
    """Test FileParameterBindingStrategy."""
    with app.test_request_context("/", method="POST"):
        # Create a mock file
        class MockFile:
            def __init__(self, filename):
                self.filename = filename

            def close(self):
                """Close the file."""

        # Add a file to request.files
        request.files = {"file": MockFile("test.txt")}
        request.form = {"description": "Test file"}

        # Create a strategy
        strategy = FileParameterBindingStrategy()

        # Test binding a parameter
        kwargs = {}
        type_hints = {"_x_file": SampleFileModel}
        strategy = FileParameterBindingStrategy(type_hints=type_hints)
        result = strategy.bind_parameter("_x_file", None, kwargs, None)

        # Check the result
        assert "_x_file" in result
        assert isinstance(result["_x_file"], SampleFileModel)
        assert result["_x_file"].file.filename == "test.txt"
        assert result["_x_file"].description == "Test file"


@pytest.mark.usefixtures("app")
def test_parameter_processor(app):
    """Test ParameterProcessor."""
    with app.test_request_context("/", method="POST", json={"name": "Test", "age": 30}):
        # Create a mock framework decorator
        mock_decorator = MagicMock()
        mock_decorator.process_request_body.return_value = {"_x_body": {"name": "Test", "age": 30}}
        mock_decorator.process_query_params.return_value = {"_x_query": {"q": "test", "limit": 20}}

        # Make process_additional_params add the necessary parameters
        def process_additional_params(kwargs, _):  # _ is param_names, not used
            # Add path parameter
            kwargs["_x_path_user_id"] = "123"
            # Add body and query parameters
            kwargs["_x_body"] = {"name": "Test", "age": 30}
            kwargs["_x_query"] = {"q": "test", "limit": 20}
            # Add the original parameter back
            kwargs["user_id"] = "123"
            return kwargs

        mock_decorator.process_additional_params.side_effect = process_additional_params

        # Create a processor
        processor = ParameterProcessor(framework_decorator=mock_decorator)

        # Create cached data
        cached_data = {
            "param_names": ["_x_body", "_x_query", "_x_path_user_id", "normal_param"],
            "type_hints": {
                "_x_body": SampleRequestModel,
                "_x_query": SampleQueryModel,
                "_x_path_user_id": str,
                "normal_param": str,
            },
            "actual_request_body": SampleRequestModel,
            "actual_query_model": SampleQueryModel,
            "actual_path_params": ["user_id"],
        }

        # Test processing parameters
        kwargs = {"user_id": "123"}
        result = processor.process_parameters(lambda: None, cached_data, (), kwargs)

        # Check that the framework decorator's methods were called
        mock_decorator.process_additional_params.assert_called_once()

        # Check the result contains the expected keys
        assert "user_id" in result
        assert "_x_path_user_id" in result
        assert "_x_body" in result
        assert "_x_query" in result

        # Check the values
        assert result["user_id"] == "123"
        assert result["_x_path_user_id"] == "123"
        assert result["_x_body"] == {"name": "Test", "age": 30}
        assert result["_x_query"] == {"q": "test", "limit": 20}
