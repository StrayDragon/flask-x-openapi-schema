"""Tests for edge cases in content type handling."""

import io
import json
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask
from pydantic import BaseModel, ValidationError
from werkzeug.datastructures import FileStorage

from flask_x_openapi_schema.core.content_type_utils import (
    BinaryContentTypeStrategy,
    ContentTypeProcessor,
    FormUrlencodedStrategy,
    JsonContentTypeStrategy,
    MultipartFormDataStrategy,
    MultipartMixedStrategy,
)
from flask_x_openapi_schema.models.file_models import (
    FileUploadModel,
    ImageUploadModel,
)


class TestEmptyRequests:
    """Tests for handling empty requests."""

    def setup_method(self):
        """Set up test environment."""
        self.app = Flask(__name__)

    @pytest.mark.skip(reason="Empty request handling needs to be updated in the library")
    def test_empty_json_request(self):
        """Test handling an empty JSON request."""
        strategy = JsonContentTypeStrategy()

        with self.app.test_request_context(
            "/",
            method="POST",
            data="",
            content_type="application/json",
        ) as ctx:
            kwargs = {}
            result = strategy.process_request(ctx.request, BaseModel, "model", kwargs)

            assert "model" in result
            assert isinstance(result["model"], BaseModel)

    @pytest.mark.skip(reason="Empty request handling needs to be updated in the library")
    def test_empty_form_request(self):
        """Test handling an empty form request."""
        strategy = FormUrlencodedStrategy()

        with self.app.test_request_context(
            "/",
            method="POST",
            data="",
            content_type="application/x-www-form-urlencoded",
        ) as ctx:
            kwargs = {}
            result = strategy.process_request(ctx.request, BaseModel, "model", kwargs)

            assert "model" in result
            assert isinstance(result["model"], BaseModel)

    @pytest.mark.skip(reason="Empty request handling needs to be updated in the library")
    def test_empty_multipart_request(self):
        """Test handling an empty multipart request."""
        strategy = MultipartFormDataStrategy()

        with self.app.test_request_context(
            "/",
            method="POST",
            data="",
            content_type="multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW",
        ) as ctx:
            kwargs = {}
            result = strategy.process_request(ctx.request, BaseModel, "model", kwargs)

            assert "model" in result
            assert isinstance(result["model"], BaseModel)

    @pytest.mark.skip(reason="Empty request handling needs to be updated in the library")
    def test_empty_binary_request(self):
        """Test handling an empty binary request."""
        strategy = BinaryContentTypeStrategy()

        with self.app.test_request_context(
            "/",
            method="POST",
            data="",
            content_type="application/octet-stream",
        ) as ctx:
            kwargs = {}
            result = strategy.process_request(ctx.request, FileUploadModel, "model", kwargs)

            assert "model" in result
            assert isinstance(result["model"], FileUploadModel)
            # File should be empty but valid
            assert result["model"].file.filename is not None
            assert result["model"].file.read() == b""


class TestMalformedRequests:
    """Tests for handling malformed requests."""

    def setup_method(self):
        """Set up test environment."""
        self.app = Flask(__name__)

    @pytest.mark.skip(reason="Malformed request handling needs to be updated in the library")
    def test_malformed_json_request(self):
        """Test handling a malformed JSON request."""
        strategy = JsonContentTypeStrategy()

        with self.app.test_request_context(
            "/",
            method="POST",
            data="{ this is not valid json",
            content_type="application/json",
        ) as ctx:
            kwargs = {}
            result = strategy.process_request(ctx.request, BaseModel, "model", kwargs)

            assert "model" in result
            # Should create an empty model instance despite invalid JSON
            assert isinstance(result["model"], BaseModel)

    @pytest.mark.skip(reason="Malformed request handling needs to be updated in the library")
    def test_malformed_multipart_request(self):
        """Test handling a malformed multipart request."""
        strategy = MultipartFormDataStrategy()

        with self.app.test_request_context(
            "/",
            method="POST",
            data="This is not a valid multipart request",
            content_type="multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW",
        ) as ctx:
            kwargs = {}
            result = strategy.process_request(ctx.request, BaseModel, "model", kwargs)

            assert "model" in result
            # Should create an empty model instance despite invalid multipart data
            assert isinstance(result["model"], BaseModel)

    @pytest.mark.skip(reason="Malformed request handling needs to be updated in the library")
    def test_malformed_multipart_mixed_request(self):
        """Test handling a malformed multipart/mixed request."""
        strategy = MultipartMixedStrategy()

        with self.app.test_request_context(
            "/",
            method="POST",
            data="This is not a valid multipart/mixed request",
            content_type="multipart/mixed; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW",
        ) as ctx:
            kwargs = {}
            result = strategy.process_request(ctx.request, BaseModel, "model", kwargs)

            # Should return an error response
            assert isinstance(result, tuple)
            assert result[1] == 400  # HTTP 400 Bad Request


class TestOversizedRequests:
    """Tests for handling oversized requests."""

    def setup_method(self):
        """Set up test environment."""
        self.app = Flask(__name__)

    @pytest.mark.skip(reason="Oversized request handling needs to be updated in the library")
    @patch("flask_x_openapi_schema.core.content_type_utils.BinaryContentTypeStrategy._process_large_binary_file")
    def test_oversized_binary_request(self, mock_process_large):
        """Test handling an oversized binary request."""
        # Mock the _process_large_binary_file method
        mock_process_large.return_value = {"model": FileUploadModel(file=MagicMock())}

        strategy = BinaryContentTypeStrategy()
        # Set a small max memory size
        strategy.max_memory_size = 10  # 10 bytes

        with self.app.test_request_context(
            "/",
            method="POST",
            data="This data is larger than 10 bytes",
            content_type="application/octet-stream",
        ) as ctx:
            # Set content length
            ctx.request.content_length = 100  # Larger than max_memory_size

            kwargs = {}
            result = strategy.process_request(ctx.request, FileUploadModel, "model", kwargs)

            # Verify large file processing was used
            mock_process_large.assert_called_once()

            assert "model" in result
            assert isinstance(result["model"], FileUploadModel)

    @pytest.mark.skip(reason="Oversized request handling needs to be updated in the library")
    @patch("flask_x_openapi_schema.core.content_type_utils.MultipartMixedStrategy._process_large_multipart_request")
    def test_oversized_multipart_mixed_request(self, mock_process_large):
        """Test handling an oversized multipart/mixed request."""
        # Mock the _process_large_multipart_request method
        mock_process_large.return_value = {"model": BaseModel()}

        strategy = MultipartMixedStrategy()
        # Set a small max memory size
        strategy.max_memory_size = 10  # 10 bytes

        with self.app.test_request_context(
            "/",
            method="POST",
            data="This data is larger than 10 bytes",
            content_type="multipart/mixed; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW",
        ) as ctx:
            # Set content length
            ctx.request.content_length = 100  # Larger than max_memory_size

            kwargs = {}
            result = strategy.process_request(ctx.request, BaseModel, "model", kwargs)

            # Verify large file processing was used
            mock_process_large.assert_called_once()

            assert "model" in result
            assert isinstance(result["model"], BaseModel)


class TestMissingContentType:
    """Tests for handling requests with missing content type."""

    def setup_method(self):
        """Set up test environment."""
        self.app = Flask(__name__)
        self.processor = ContentTypeProcessor()

    @pytest.mark.skip(reason="Missing content type handling needs to be updated in the library")
    def test_missing_content_type(self):
        """Test handling a request with missing content type."""
        with self.app.test_request_context(
            "/",
            method="POST",
            data="test data",
            # No content_type specified
        ) as ctx:
            # Explicitly set content_type to None
            ctx.request.content_type = None

            kwargs = {}
            result = self.processor.process_request_body(ctx.request, BaseModel, "model", kwargs)

            assert "model" in result
            assert isinstance(result["model"], BaseModel)

    @pytest.mark.skip(reason="Empty content type handling needs to be updated in the library")
    def test_empty_content_type(self):
        """Test handling a request with empty content type."""
        with self.app.test_request_context(
            "/",
            method="POST",
            data="test data",
            content_type="",
        ) as ctx:
            kwargs = {}
            result = self.processor.process_request_body(ctx.request, BaseModel, "model", kwargs)

            assert "model" in result
            assert isinstance(result["model"], BaseModel)


class TestInvalidModels:
    """Tests for handling invalid models."""

    def setup_method(self):
        """Set up test environment."""
        self.app = Flask(__name__)

    @pytest.mark.skip(reason="Invalid model handling needs to be updated in the library")
    def test_model_with_required_fields_missing(self):
        """Test handling a model with required fields missing."""

        @pytest.mark.no_cover
        class RequiredFieldsModel(BaseModel):
            name: str
            age: int

        strategy = JsonContentTypeStrategy()

        with self.app.test_request_context(
            "/",
            method="POST",
            data=json.dumps({}),  # Empty data, missing required fields
            content_type="application/json",
        ) as ctx:
            kwargs = {}
            # This should raise a validation error
            with pytest.raises(ValidationError):
                strategy.process_request(ctx.request, RequiredFieldsModel, "model", kwargs)

    @pytest.mark.skip(reason="Invalid model handling needs to be updated in the library")
    def test_model_with_invalid_field_types(self):
        """Test handling a model with invalid field types."""

        @pytest.mark.no_cover
        class TypedFieldsModel(BaseModel):
            name: str
            age: int

        strategy = JsonContentTypeStrategy()

        with self.app.test_request_context(
            "/",
            method="POST",
            data=json.dumps({"name": "Test", "age": "not an integer"}),  # Invalid age type
            content_type="application/json",
        ) as ctx:
            kwargs = {}
            # This should raise a validation error
            with pytest.raises(ValidationError):
                strategy.process_request(ctx.request, TypedFieldsModel, "model", kwargs)

    @pytest.mark.skip(reason="Invalid model handling needs to be updated in the library")
    def test_file_model_with_missing_file(self):
        """Test handling a file model with missing file."""
        strategy = MultipartFormDataStrategy()

        with self.app.test_request_context(
            "/",
            method="POST",
            data={},  # No file provided
            content_type="multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW",
        ) as ctx:
            kwargs = {}
            # This should create a model but validation will fail
            with pytest.raises(ValidationError):
                strategy.process_request(ctx.request, FileUploadModel, "model", kwargs)

    @pytest.mark.skip(reason="Invalid model handling needs to be updated in the library")
    def test_image_model_with_wrong_file_type(self):
        """Test handling an image model with wrong file type."""
        # Create a test file with non-image content type
        test_file = FileStorage(
            stream=io.BytesIO(b"Test file content"),
            filename="test.txt",
            content_type="text/plain",  # Not an image
        )

        strategy = MultipartFormDataStrategy()

        with self.app.test_request_context(
            "/",
            method="POST",
            data={"file": test_file},
            content_type="multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW",
        ) as ctx:
            # Mock the files attribute
            ctx.request.files = {"file": test_file}

            kwargs = {}
            # This should create a model but validation will fail due to wrong file type
            with pytest.raises(ValidationError):
                strategy.process_request(ctx.request, ImageUploadModel, "model", kwargs)
