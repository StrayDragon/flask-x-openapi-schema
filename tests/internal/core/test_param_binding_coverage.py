"""Tests for parameter binding strategies with focus on coverage."""

from unittest.mock import MagicMock

import pytest
from flask import Flask, request
from pydantic import BaseModel

from flask_x_openapi_schema.core.config import ConventionalPrefixConfig
from flask_x_openapi_schema.core.param_binding import (
    FileParameterBindingStrategy,
    ParameterBindingStrategyFactory,
    ParameterProcessor,
    PathParameterBindingStrategy,
    QueryParameterBindingStrategy,
    RequestBodyBindingStrategy,
    preprocess_request_data,
)
from flask_x_openapi_schema.models.file_models import FileField


class TestPreprocessRequestData:
    """Tests for preprocess_request_data function."""

    def test_non_pydantic_model(self):
        """Test preprocessing with a non-Pydantic model."""

        class NonPydanticModel:
            pass

        data = {"name": "John", "age": 30}
        result = preprocess_request_data(data, NonPydanticModel)

        # Should return data unchanged
        assert result == data

    def test_list_field_with_string_json(self):
        """Test preprocessing list field with string JSON."""

        class TestModel(BaseModel):
            tags: list[str]

        data = {"tags": '["tag1", "tag2"]'}
        result = preprocess_request_data(data, TestModel)

        assert result["tags"] == ["tag1", "tag2"]

    def test_list_field_with_invalid_json(self):
        """Test preprocessing list field with invalid JSON."""

        class TestModel(BaseModel):
            tags: list[str]

        data = {"tags": "not-json"}
        result = preprocess_request_data(data, TestModel)

        assert result["tags"] == ["not-json"]

    def test_list_field_with_single_value(self):
        """Test preprocessing list field with a single value."""

        class TestModel(BaseModel):
            tags: list[str]

        data = {"tags": "tag1"}
        result = preprocess_request_data(data, TestModel)

        assert result["tags"] == ["tag1"]

    def test_list_field_with_none_value(self):
        """Test preprocessing list field with None value."""

        class TestModel(BaseModel):
            tags: list[str] = None

        data = {"tags": None}
        result = preprocess_request_data(data, TestModel)

        assert result["tags"] is None

    def test_unknown_field(self):
        """Test preprocessing with unknown field."""

        class TestModel(BaseModel):
            name: str

        data = {"name": "John", "unknown": "value"}
        result = preprocess_request_data(data, TestModel)

        assert result == data


class TestRequestBodyBindingStrategy:
    """Tests for RequestBodyBindingStrategy."""

    def test_bind_parameter(self):
        """Test binding a request body parameter."""
        # Create a mock framework decorator
        framework_decorator = MagicMock()
        framework_decorator.process_request_body.return_value = {"param": "value"}

        # Create a strategy
        strategy = RequestBodyBindingStrategy()

        # Create a test model
        class TestModel(BaseModel):
            name: str

        # Bind parameter
        kwargs = {}
        result = strategy.bind_parameter("param", TestModel, kwargs, framework_decorator)

        # Check that framework_decorator.process_request_body was called
        framework_decorator.process_request_body.assert_called_once_with("param", TestModel, kwargs)

        # Check result
        assert result == {"param": "value"}


class TestQueryParameterBindingStrategy:
    """Tests for QueryParameterBindingStrategy."""

    def test_bind_parameter(self):
        """Test binding query parameters."""
        # Create a mock framework decorator
        framework_decorator = MagicMock()
        framework_decorator.process_query_params.return_value = {"param": "value"}

        # Create a strategy
        strategy = QueryParameterBindingStrategy()

        # Create a test model
        class TestModel(BaseModel):
            name: str

        # Bind parameter
        kwargs = {}
        result = strategy.bind_parameter("param", TestModel, kwargs, framework_decorator)

        # Check that framework_decorator.process_query_params was called
        framework_decorator.process_query_params.assert_called_once_with("param", TestModel, kwargs)

        # Check result
        assert result == {"param": "value"}


class TestPathParameterBindingStrategy:
    """Tests for PathParameterBindingStrategy."""

    def test_bind_parameter_with_default_prefix(self):
        """Test binding path parameters with default prefix."""
        # Create a strategy with default prefix
        strategy = PathParameterBindingStrategy()

        # Bind parameter
        kwargs = {"item_id": "123"}
        result = strategy.bind_parameter("_x_path_item_id", None, kwargs, None)

        # Check result
        assert result["_x_path_item_id"] == "123"

    def test_bind_parameter_with_custom_prefix(self):
        """Test binding path parameters with custom prefix."""
        # Create a strategy with custom prefix
        prefix_config = ConventionalPrefixConfig(request_path_prefix="path")
        strategy = PathParameterBindingStrategy(prefix_config)

        # Bind parameter
        kwargs = {"item_id": "123"}
        result = strategy.bind_parameter("path_item_id", None, kwargs, None)

        # Check result
        assert result["path_item_id"] == "123"

    def test_bind_parameter_missing_path_param(self):
        """Test binding path parameters when the path parameter is missing."""
        # Create a strategy
        strategy = PathParameterBindingStrategy()

        # Bind parameter
        kwargs = {}
        result = strategy.bind_parameter("_x_path_item_id", None, kwargs, None)

        # Check result (should not add the parameter)
        assert "_x_path_item_id" not in result


class TestFileParameterBindingStrategy:
    """Tests for FileParameterBindingStrategy."""

    def test_bind_parameter_with_file(self):
        """Test binding file parameters with a file in request.files."""
        # Create a Flask app and request context
        app = Flask(__name__)

        # Create a mock file
        mock_file = MagicMock()
        mock_file.filename = "test.txt"

        # Create a strategy
        strategy = FileParameterBindingStrategy()

        # Create a test context with a file
        with app.test_request_context(
            "/",
            method="POST",
            data={"field": "value"},
            content_type="multipart/form-data",
        ):
            # Mock request.files
            request.files = {"upload": mock_file}

            # Bind parameter
            kwargs = {}
            result = strategy.bind_parameter("_x_file_upload", None, kwargs, None)

            # Check result
            assert result["_x_file_upload"] == mock_file

    def test_bind_parameter_with_default_file(self):
        """Test binding file parameters with a default 'file' in request.files."""
        # Create a Flask app and request context
        app = Flask(__name__)

        # Create a mock file
        mock_file = MagicMock()
        mock_file.filename = "test.txt"

        # Create a strategy
        strategy = FileParameterBindingStrategy()

        # Create a test context with a file
        with app.test_request_context(
            "/",
            method="POST",
            data={"field": "value"},
            content_type="multipart/form-data",
        ):
            # Mock request.files
            request.files = {"file": mock_file}

            # Bind parameter
            kwargs = {}
            result = strategy.bind_parameter("_x_file_upload", None, kwargs, None)

            # Check result
            assert result["_x_file_upload"] == mock_file

    def test_bind_parameter_with_single_file(self):
        """Test binding file parameters with a single file in request.files."""
        # Create a Flask app and request context
        app = Flask(__name__)

        # Create a mock file
        mock_file = MagicMock()
        mock_file.filename = "test.txt"

        # Create a strategy
        strategy = FileParameterBindingStrategy()

        # Create a test context with a file
        with app.test_request_context(
            "/",
            method="POST",
            data={"field": "value"},
            content_type="multipart/form-data",
        ):
            # Mock request.files
            request.files = {"some_file": mock_file}

            # Bind parameter
            kwargs = {}
            result = strategy.bind_parameter("_x_file", None, kwargs, None)

            # Check result
            assert result["_x_file"] == mock_file

    def test_bind_parameter_with_pydantic_model(self):
        """Test binding file parameters with a Pydantic model."""
        # Create a Flask app and request context
        app = Flask(__name__)

        # Create a mock file
        mock_file = MagicMock()
        mock_file.filename = "test.txt"

        # Create a file model
        class FileUploadModel(BaseModel):
            file: FileField
            description: str = ""

        # Create a strategy with type hints
        type_hints = {"_x_file_upload": FileUploadModel}
        strategy = FileParameterBindingStrategy(type_hints=type_hints)

        # Create a test context with a file and form data
        with app.test_request_context(
            "/",
            method="POST",
            data={"description": "Test file"},
            content_type="multipart/form-data",
        ):
            # Mock request.files
            request.files = {"file": mock_file}

            # Bind parameter
            kwargs = {}
            result = strategy.bind_parameter("_x_file_upload", None, kwargs, None)

            # Check result
            assert "_x_file_upload" in result
            assert isinstance(result["_x_file_upload"], FileUploadModel)
            assert result["_x_file_upload"].file == mock_file
            assert result["_x_file_upload"].description == "Test file"


class TestParameterBindingStrategyFactory:
    """Tests for ParameterBindingStrategyFactory."""

    def test_create_body_strategy(self):
        """Test creating a request body binding strategy."""
        strategy = ParameterBindingStrategyFactory.create_strategy("body")
        assert isinstance(strategy, RequestBodyBindingStrategy)

    def test_create_query_strategy(self):
        """Test creating a query parameter binding strategy."""
        strategy = ParameterBindingStrategyFactory.create_strategy("query")
        assert isinstance(strategy, QueryParameterBindingStrategy)

    def test_create_path_strategy(self):
        """Test creating a path parameter binding strategy."""
        strategy = ParameterBindingStrategyFactory.create_strategy("path")
        assert isinstance(strategy, PathParameterBindingStrategy)

        # With prefix config
        prefix_config = ConventionalPrefixConfig(request_path_prefix="path")
        strategy = ParameterBindingStrategyFactory.create_strategy("path", prefix_config)
        assert isinstance(strategy, PathParameterBindingStrategy)

    def test_create_file_strategy(self):
        """Test creating a file parameter binding strategy."""
        strategy = ParameterBindingStrategyFactory.create_strategy("file")
        assert isinstance(strategy, FileParameterBindingStrategy)

        # With prefix config and type hints
        prefix_config = ConventionalPrefixConfig(request_file_prefix="file")
        type_hints = {"file_upload": FileField}
        strategy = ParameterBindingStrategyFactory.create_strategy("file", prefix_config, type_hints)
        assert isinstance(strategy, FileParameterBindingStrategy)

    def test_create_unsupported_strategy(self):
        """Test creating an unsupported strategy."""
        with pytest.raises(ValueError):
            ParameterBindingStrategyFactory.create_strategy("unsupported")


class TestParameterProcessor:
    """Tests for ParameterProcessor."""

    def test_init(self):
        """Test initialization of ParameterProcessor."""
        # With default prefix config
        processor = ParameterProcessor()
        # Get the actual prefixes from the processor
        actual_prefixes = processor.prefixes
        # Check that we have 4 prefixes
        assert len(actual_prefixes) == 4

        # With custom prefix config
        prefix_config = ConventionalPrefixConfig(
            request_body_prefix="body",
            request_query_prefix="query",
            request_path_prefix="path",
            request_file_prefix="file",
        )
        processor = ParameterProcessor(prefix_config)
        assert processor.prefixes == ("body", "query", "path", "file")

    def test_process_parameters_no_request_context(self):
        """Test processing parameters without a request context."""
        # Create a processor
        processor = ParameterProcessor()

        # Create cached data
        cached_data = {
            "param_names": ["_x_body", "_x_query", "_x_path_id", "_x_file"],
            "type_hints": {},
            "actual_request_body": None,
            "actual_query_model": None,
            "actual_path_params": None,
        }

        # Process parameters
        kwargs = {"id": "123"}
        result = processor.process_parameters(None, cached_data, (), kwargs)

        # Should return kwargs unchanged
        assert result == kwargs

    def test_process_parameters_with_request_context(self):
        """Test processing parameters with a request context."""
        # Create a Flask app and request context
        app = Flask(__name__)

        with app.test_request_context("/"):
            # Create a mock framework decorator
            framework_decorator = MagicMock()
            framework_decorator.process_additional_params.return_value = {"_x_path_id": "123", "id": "123"}

            # Create a processor with the mock framework decorator
            processor = ParameterProcessor(framework_decorator=framework_decorator)

            # Create cached data
            cached_data = {
                "param_names": ["_x_path_id"],
                "type_hints": {},
                "actual_request_body": None,
                "actual_query_model": None,
                "actual_path_params": ["id"],
            }

            # Process parameters
            kwargs = {"id": "123"}
            result = processor.process_parameters(None, cached_data, (), kwargs)

            # Check that the path parameter was processed
            assert "_x_path_id" in result
            assert result["_x_path_id"] == "123"

            # Check that framework_decorator.process_additional_params was called
            framework_decorator.process_additional_params.assert_called_once()
