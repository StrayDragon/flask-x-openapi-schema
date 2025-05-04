"""Tests for request extractors."""

from unittest.mock import MagicMock, patch

import pytest
from flask import Flask
from pydantic import BaseModel

from flask_x_openapi_schema.core.request_extractors import (
    ContentTypeJsonExtractor,
    FormRequestExtractor,
    JsonRequestExtractor,
    ModelFactory,
    RawDataJsonExtractor,
    RequestCachedJsonExtractor,
    RequestJsonAttributeExtractor,
    RequestProcessor,
    log_operation,
    safe_operation,
)


class TestRequestExtractors:
    """Tests for request extractors."""

    def setup_method(self):
        """Set up test environment."""
        self.app = Flask(__name__)
        self.client = self.app.test_client()

    def test_log_operation_decorator(self):
        """Test the log_operation decorator."""

        # Define a function with the decorator
        @log_operation
        def test_func(x):
            return x * 2

        # Call the function
        result = test_func(5)

        # Check that the function works correctly
        assert result == 10

        # Test with exception
        @log_operation
        def error_func():
            raise ValueError("Test error")

        # Call the function that raises an exception
        with pytest.raises(ValueError):
            error_func()

    def test_safe_operation(self):
        """Test the safe_operation function."""
        # Test with successful operation
        result = safe_operation(lambda: 42, fallback=0)
        assert result == 42

        # Patch the get_logger function to avoid issues with missing arguments
        with patch("flask_x_openapi_schema.core.request_extractors.get_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            # Test with failing operation
            result = safe_operation(lambda: 1 / 0, fallback=0)
            assert result == 0
            mock_logger.warning.assert_called_once()
            mock_logger.reset_mock()

            # Test with callable fallback
            result = safe_operation(lambda: 1 / 0, fallback=lambda: 99)
            assert result == 99
            mock_logger.warning.assert_called_once()
            mock_logger.reset_mock()

            # Test with log_error=False
            result = safe_operation(lambda: 1 / 0, fallback=0, log_error=False)
            assert result == 0
            mock_logger.warning.assert_not_called()

    def test_json_request_extractor(self):
        """Test the JsonRequestExtractor."""
        extractor = JsonRequestExtractor()

        # Test with JSON request
        with self.app.test_request_context(
            "/",
            method="POST",
            json={"name": "test", "age": 25},
            content_type="application/json",
        ):
            # Import flask request
            from flask import request

            # Check can_extract
            assert extractor.can_extract(request) is True

            # Extract data
            data = extractor.extract(request)
            assert data == {"name": "test", "age": 25}

        # Test with non-JSON request
        with self.app.test_request_context(
            "/",
            method="POST",
            data="not json",
            content_type="text/plain",
        ):
            # Import flask request
            from flask import request

            # Check can_extract
            assert extractor.can_extract(request) is False

    def test_form_request_extractor(self):
        """Test the FormRequestExtractor."""
        extractor = FormRequestExtractor()

        # Test with form data
        with self.app.test_request_context(
            "/",
            method="POST",
            data={"name": "test", "age": "25"},
            content_type="application/x-www-form-urlencoded",
        ):
            # Import flask request
            from flask import request

            # Check can_extract
            assert extractor.can_extract(request) is True

            # Extract data
            data = extractor.extract(request)
            assert data == {"name": "test", "age": "25"}

        # Test with empty request
        with self.app.test_request_context(
            "/",
            method="GET",
        ):
            # Import flask request
            from flask import request

            # Check can_extract
            assert extractor.can_extract(request) is False

    def test_content_type_json_extractor(self):
        """Test the ContentTypeJsonExtractor."""
        extractor = ContentTypeJsonExtractor()

        # Test with JSON content type but not parsed as JSON
        # We need to mock the request object since we can't set is_json directly
        mock_request = MagicMock()
        mock_request.is_json = False
        mock_request.content_type = "application/json"
        mock_request.get_data.return_value = '{"name": "test", "age": 25}'

        # Check can_extract
        assert extractor.can_extract(mock_request) is True

        # Extract data
        data = extractor.extract(mock_request)
        assert data == {"name": "test", "age": 25}

        # Test with invalid JSON
        mock_request = MagicMock()
        mock_request.is_json = False
        mock_request.content_type = "application/json"
        mock_request.get_data.return_value = "not json"

        # Check can_extract
        assert extractor.can_extract(mock_request) is True

        # Extract data (should return empty dict for invalid JSON)
        data = extractor.extract(mock_request)
        assert data == {}

        # Test with non-JSON content type
        mock_request = MagicMock()
        mock_request.is_json = False
        mock_request.content_type = "text/plain"
        mock_request.get_data.return_value = "not json"

        # Check can_extract
        assert extractor.can_extract(mock_request) is False

    def test_raw_data_json_extractor(self):
        """Test the RawDataJsonExtractor."""
        extractor = RawDataJsonExtractor()

        # Test with valid JSON data
        mock_request = MagicMock()
        mock_request.get_data.return_value = '{"name": "test", "age": 25}'

        # Check can_extract (always returns True)
        assert extractor.can_extract(mock_request) is True

        # Extract data
        data = extractor.extract(mock_request)
        assert data == {"name": "test", "age": 25}

        # Test with invalid JSON
        mock_request = MagicMock()
        mock_request.get_data.return_value = "not json"

        # Check can_extract (always returns True)
        assert extractor.can_extract(mock_request) is True

        # Extract data (should return empty dict for invalid JSON)
        data = extractor.extract(mock_request)
        assert data == {}

        # Test with empty request
        mock_request = MagicMock()
        mock_request.get_data.return_value = ""

        # Check can_extract (always returns True)
        assert extractor.can_extract(mock_request) is True

        # Extract data (should return empty dict for empty request)
        data = extractor.extract(mock_request)
        assert data == {}

    def test_request_json_attribute_extractor(self):
        """Test the RequestJsonAttributeExtractor."""
        extractor = RequestJsonAttributeExtractor()

        # Test with request.json attribute
        mock_request = MagicMock()
        mock_request.json = {"name": "test", "age": 25}

        # Check can_extract
        assert extractor.can_extract(mock_request) is True

        # Extract data
        data = extractor.extract(mock_request)
        assert data == {"name": "test", "age": 25}

        # Test without request.json attribute
        mock_request = MagicMock()
        mock_request.json = None

        # Check can_extract
        assert extractor.can_extract(mock_request) is False

        # Test with no json attribute
        mock_request = MagicMock()
        # Remove the json attribute
        del mock_request.json

        # Check can_extract
        assert extractor.can_extract(mock_request) is False

    def test_request_cached_json_extractor(self):
        """Test the RequestCachedJsonExtractor."""
        extractor = RequestCachedJsonExtractor()

        # Test with request._cached_json attribute
        mock_request = MagicMock()
        mock_request._cached_json = {"name": "test", "age": 25}

        # Check can_extract
        assert extractor.can_extract(mock_request) is True

        # Extract data
        data = extractor.extract(mock_request)
        assert data == {"name": "test", "age": 25}

        # Test without request._cached_json attribute (None)
        mock_request = MagicMock()
        mock_request._cached_json = None

        # Check can_extract
        assert extractor.can_extract(mock_request) is False

        # Test with no _cached_json attribute
        mock_request = MagicMock()
        # Remove the _cached_json attribute
        del mock_request._cached_json

        # Check can_extract
        assert extractor.can_extract(mock_request) is False

    def test_model_factory(self):
        """Test the ModelFactory."""

        # Define a model
        class TestModel(BaseModel):
            name: str
            age: int

        # Test with valid data
        data = {"name": "test", "age": 25}
        model = ModelFactory.create_from_data(TestModel, data)
        assert isinstance(model, TestModel)
        assert model.name == "test"
        assert model.age == 25

        # Test with extra fields
        data = {"name": "test", "age": 25, "extra": "ignored"}
        model = ModelFactory.create_from_data(TestModel, data)
        assert isinstance(model, TestModel)
        assert model.name == "test"
        assert model.age == 25
        assert not hasattr(model, "extra")

        # Test with invalid data
        data = {"name": "test"}  # Missing required field 'age'
        with pytest.raises(ValueError):
            ModelFactory.create_from_data(TestModel, data)

        # Test with type conversion
        data = {"name": "test", "age": "25"}  # age as string
        model = ModelFactory.create_from_data(TestModel, data)
        assert isinstance(model, TestModel)
        assert model.name == "test"
        assert model.age == 25
        assert isinstance(model.age, int)

    def test_request_processor(self):
        """Test the RequestProcessor."""
        processor = RequestProcessor()

        # Define a model
        class TestModel(BaseModel):
            name: str
            age: int

        # Test with JSON request
        # Create a mock extractor that always returns JSON data
        json_extractor = MagicMock()
        json_extractor.can_extract.return_value = True
        json_extractor.extract.return_value = {"name": "test", "age": 25}

        # Replace the processor's extractors with our mock
        original_extractors = processor.extractors
        processor.extractors = [json_extractor]

        # Create a mock request
        mock_request = MagicMock()

        # Extract data
        data = processor.extract_data(mock_request)
        assert data == {"name": "test", "age": 25}

        # Process request data
        with patch(
            "flask_x_openapi_schema.core.request_processing.preprocess_request_data",
            return_value={"name": "test", "age": 25},
        ):
            model = processor.process_request_data(mock_request, TestModel, "test_model")
            assert isinstance(model, TestModel)
            assert model.name == "test"
            assert model.age == 25

        # Test with form data
        form_extractor = MagicMock()
        form_extractor.can_extract.return_value = True
        form_extractor.extract.return_value = {"name": "test", "age": "25"}

        # Replace the processor's extractors with our mock
        processor.extractors = [form_extractor]

        # Extract data
        data = processor.extract_data(mock_request)
        assert data == {"name": "test", "age": "25"}

        # Process request data
        with patch(
            "flask_x_openapi_schema.core.request_processing.preprocess_request_data",
            return_value={"name": "test", "age": "25"},
        ):
            model = processor.process_request_data(mock_request, TestModel, "test_model")
            assert isinstance(model, TestModel)
            assert model.name == "test"
            assert model.age == 25

        # Test with empty request
        empty_extractor = MagicMock()
        empty_extractor.can_extract.return_value = True
        empty_extractor.extract.return_value = {}

        # Replace the processor's extractors with our mock
        processor.extractors = [empty_extractor]

        # Extract data (should return empty dict)
        data = processor.extract_data(mock_request)
        assert data == {}

        # Process request data (should return None)
        with patch("flask_x_openapi_schema.core.request_processing.preprocess_request_data", return_value={}):
            model = processor.process_request_data(mock_request, TestModel, "test_model")
            assert model is None

        # Restore original extractors
        processor.extractors = original_extractors

    def test_request_processor_with_extractors(self):
        """Test the RequestProcessor with custom extractors."""
        # Create a custom extractor
        custom_extractor = MagicMock()
        custom_extractor.can_extract.return_value = True
        custom_extractor.extract.return_value = {"name": "custom", "age": 99}

        # Create a processor with the custom extractor
        processor = RequestProcessor()
        processor.extractors = [custom_extractor]

        # Define a model
        class TestModel(BaseModel):
            name: str
            age: int

        # Create a mock request
        mock_request = MagicMock()

        # Extract data
        data = processor.extract_data(mock_request)
        assert data == {"name": "custom", "age": 99}

        # Process request data
        with patch(
            "flask_x_openapi_schema.core.request_processing.preprocess_request_data",
            return_value={"name": "custom", "age": 99},
        ):
            model = processor.process_request_data(mock_request, TestModel, "test_model")
            assert isinstance(model, TestModel)
            assert model.name == "custom"
            assert model.age == 99

        # Verify that the custom extractor was called
        # The extractor is called twice: once in extract_data and once in process_request_data
        assert custom_extractor.can_extract.call_count == 2
        assert custom_extractor.extract.call_count == 2
        custom_extractor.can_extract.assert_any_call(mock_request)
        custom_extractor.extract.assert_any_call(mock_request)

    def test_request_processor_with_failing_extractors(self):
        """Test the RequestProcessor with extractors that fail."""
        # Create extractors that fail
        failing_extractor1 = MagicMock()
        failing_extractor1.can_extract.return_value = True
        failing_extractor1.extract.side_effect = Exception("Test error")

        failing_extractor2 = MagicMock()
        failing_extractor2.can_extract.return_value = True
        failing_extractor2.extract.return_value = {}  # Empty result

        # Create a working extractor
        working_extractor = MagicMock()
        working_extractor.can_extract.return_value = True
        working_extractor.extract.return_value = {"name": "working", "age": 42}

        # Create a processor with the extractors
        processor = RequestProcessor()
        processor.extractors = [failing_extractor1, failing_extractor2, working_extractor]

        # Define a model
        class TestModel(BaseModel):
            name: str
            age: int

        # Create a mock request
        mock_request = MagicMock()

        # Extract data
        data = processor.extract_data(mock_request)
        assert data == {"name": "working", "age": 42}

        # Process request data
        with patch(
            "flask_x_openapi_schema.core.request_processing.preprocess_request_data",
            return_value={"name": "working", "age": 42},
        ):
            model = processor.process_request_data(mock_request, TestModel, "test_model")
            assert isinstance(model, TestModel)
            assert model.name == "working"
            assert model.age == 42

        # Verify that all extractors were called
        # Each extractor is called twice: once in extract_data and once in process_request_data
        assert failing_extractor1.can_extract.call_count == 2
        assert failing_extractor1.extract.call_count == 2
        assert failing_extractor2.can_extract.call_count == 2
        assert failing_extractor2.extract.call_count == 2
        assert working_extractor.can_extract.call_count == 2
        assert working_extractor.extract.call_count == 2

        failing_extractor1.can_extract.assert_any_call(mock_request)
        failing_extractor1.extract.assert_any_call(mock_request)
        failing_extractor2.can_extract.assert_any_call(mock_request)
        failing_extractor2.extract.assert_any_call(mock_request)
        working_extractor.can_extract.assert_any_call(mock_request)
        working_extractor.extract.assert_any_call(mock_request)
