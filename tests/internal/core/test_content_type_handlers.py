"""Tests for content type handlers and strategies."""

import io
from unittest.mock import MagicMock, patch

from flask import Flask
from pydantic import BaseModel, Field
from werkzeug.datastructures import FileStorage

from flask_x_openapi_schema.core.content_type_utils import (
    MultipartFormDataStrategy,
    MultipartMixedStrategy,
    check_for_file_fields,
    detect_content_type,
)
from flask_x_openapi_schema.models.content_types import (
    detect_content_type_from_model,
)
from flask_x_openapi_schema.models.file_models import (
    AudioField,
    FileField,
    ImageField,
    PDFField,
    VideoField,
)


class SampleFileModel(BaseModel):
    """Test model for file upload tests."""

    file: FileField
    description: str = ""


class SampleImageModel(BaseModel):
    """Test model for image upload tests."""

    image: ImageField
    title: str = ""
    is_primary: bool = False


class SampleAudioModel(BaseModel):
    """Test model for audio upload tests."""

    audio: AudioField
    title: str = ""
    duration_seconds: int = 0


class SampleVideoModel(BaseModel):
    """Test model for video upload tests."""

    video: VideoField
    title: str = ""
    duration_seconds: int = 0
    resolution: str = ""


class SampleDocumentModel(BaseModel):
    """Test model for document upload tests."""

    document: PDFField
    title: str = ""
    page_count: int = 0


class SampleMultipleFilesModel(BaseModel):
    """Test model for multiple file uploads."""

    files: list[FileField] = Field(default_factory=list)
    description: str = ""


class TestMultipartFormDataStrategy:
    """Tests for MultipartFormDataStrategy class."""

    def setup_method(self):
        """Set up test environment."""
        self.app = Flask(__name__)
        self.strategy = MultipartFormDataStrategy()

    def test_can_handle(self):
        """Test can_handle method."""
        assert self.strategy.can_handle("multipart/form-data")
        assert self.strategy.can_handle("multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW")
        assert not self.strategy.can_handle("application/json")

    def test_process_request_with_file(self):
        """Test processing a request with a file."""
        # Create a test file
        test_file = FileStorage(
            stream=io.BytesIO(b"Test file content"),
            filename="test.txt",
            content_type="text/plain",
        )

        with self.app.test_request_context(
            "/",
            method="POST",
            data={"file": test_file, "description": "Test description"},
            content_type="multipart/form-data",
        ) as ctx:
            # Mock the files attribute
            ctx.request.files = {"file": test_file}
            ctx.request.form = {"description": "Test description"}

            kwargs = {}
            result = self.strategy.process_request(ctx.request, SampleFileModel, "model", kwargs)
            assert "model" in result
            assert isinstance(result["model"], SampleFileModel)
            assert result["model"].description == "Test description"
            assert result["model"].file.filename == "test.txt"

    def test_process_request_with_image(self):
        """Test processing a request with an image file."""
        # Create a test image
        test_image = FileStorage(
            stream=io.BytesIO(b"Test image content"),
            filename="test.jpg",
            content_type="image/jpeg",
        )

        with self.app.test_request_context(
            "/",
            method="POST",
            data={"image": test_image, "title": "Test image", "is_primary": "true"},
            content_type="multipart/form-data",
        ) as ctx:
            # Mock the files attribute
            ctx.request.files = {"image": test_image}
            ctx.request.form = {"title": "Test image", "is_primary": "true"}

            kwargs = {}
            result = self.strategy.process_request(ctx.request, SampleImageModel, "model", kwargs)
            assert "model" in result
            assert isinstance(result["model"], SampleImageModel)
            assert result["model"].title == "Test image"
            assert result["model"].is_primary is True
            assert result["model"].image.filename == "test.jpg"

    def test_process_request_with_multiple_files(self):
        """Test processing a request with multiple files."""
        # Create test files
        test_file1 = FileStorage(
            stream=io.BytesIO(b"Test file 1 content"),
            filename="test1.txt",
            content_type="text/plain",
        )
        test_file2 = FileStorage(
            stream=io.BytesIO(b"Test file 2 content"),
            filename="test2.txt",
            content_type="text/plain",
        )

        with self.app.test_request_context(
            "/",
            method="POST",
            data={"description": "Multiple files"},
            content_type="multipart/form-data",
        ) as ctx:
            # Mock the files attribute
            ctx.request.files = MagicMock()
            ctx.request.files.getlist = MagicMock(return_value=[test_file1, test_file2])
            # Mock the files dictionary-like behavior
            ctx.request.files.__contains__ = MagicMock(return_value=True)
            ctx.request.files.__getitem__ = MagicMock(return_value=test_file1)
            ctx.request.form = {"description": "Multiple files"}

            # Create a model instance manually for testing
            model_instance = SampleMultipleFilesModel(files=[test_file1, test_file2], description="Multiple files")

            # Mock process_file_upload_model to return our model instance
            with patch(
                "flask_x_openapi_schema.core.content_type_utils.process_file_upload_model", return_value=model_instance
            ):
                kwargs = {}
                result = self.strategy.process_request(ctx.request, SampleMultipleFilesModel, "model", kwargs)
                assert "model" in result
                assert isinstance(result["model"], SampleMultipleFilesModel)
                assert result["model"].description == "Multiple files"
                assert len(result["model"].files) == 2
                assert result["model"].files[0].filename == "test1.txt"
                assert result["model"].files[1].filename == "test2.txt"


class TestMultipartMixedStrategy:
    """Tests for MultipartMixedStrategy class."""

    def setup_method(self):
        """Set up test environment."""
        self.app = Flask(__name__)
        self.strategy = MultipartMixedStrategy()

    def test_can_handle(self):
        """Test can_handle method."""
        assert self.strategy.can_handle("multipart/mixed")
        assert self.strategy.can_handle("multipart/mixed; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW")
        assert not self.strategy.can_handle("application/json")

    @patch("flask_x_openapi_schema.core.content_type_utils.MultipartMixedStrategy._process_small_multipart_request")
    def test_process_request_small_multipart(self, mock_process_small):
        """Test processing a small multipart/mixed request."""
        # Mock the _process_small_multipart_request method
        mock_process_small.return_value = {"model": SampleFileModel(file=MagicMock(), description="Test")}

        with self.app.test_request_context(
            "/",
            method="POST",
            data="--boundary\r\nContent-Type: application/json\r\n\r\n{}\r\n--boundary--",
            content_type="multipart/mixed; boundary=boundary",
        ) as ctx:
            # Set a small content length
            ctx.request.content_length = 100

            kwargs = {}
            result = self.strategy.process_request(ctx.request, SampleFileModel, "model", kwargs)
            assert "model" in result
            assert isinstance(result["model"], SampleFileModel)

            # Verify the mock was called
            mock_process_small.assert_called_once()

    @patch("flask_x_openapi_schema.core.content_type_utils.MultipartMixedStrategy._process_large_multipart_request")
    def test_process_request_large_multipart(self, mock_process_large):
        """Test processing a large multipart/mixed request."""
        # Mock the _process_large_multipart_request method
        mock_process_large.return_value = {"model": SampleFileModel(file=MagicMock(), description="Test")}

        with self.app.test_request_context(
            "/",
            method="POST",
            data="--boundary\r\nContent-Type: application/json\r\n\r\n{}\r\n--boundary--",
            content_type="multipart/mixed; boundary=boundary",
        ) as ctx:
            # Set a large content length
            ctx.request.content_length = 10 * 1024 * 1024  # 10 MB

            # Set a small max_memory_size for the strategy
            self.strategy.max_memory_size = 1 * 1024 * 1024  # 1 MB

            kwargs = {}
            result = self.strategy.process_request(ctx.request, SampleFileModel, "model", kwargs)
            assert "model" in result
            assert isinstance(result["model"], SampleFileModel)

            # Verify the mock was called
            mock_process_large.assert_called_once()


class TestContentTypeDetection:
    """Tests for content type detection functions."""

    def test_detect_content_type(self):
        """Test detect_content_type function."""
        # Create a mock request
        mock_request = MagicMock()

        # Test JSON content type
        mock_request.content_type = "application/json"
        assert detect_content_type(mock_request) == "application/json"

        # Test multipart/form-data content type
        mock_request.content_type = "multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW"
        assert detect_content_type(mock_request) == "multipart/form-data"

        # Test application/x-www-form-urlencoded content type
        mock_request.content_type = "application/x-www-form-urlencoded"
        assert detect_content_type(mock_request) == "application/x-www-form-urlencoded"

        # Test multipart/mixed content type
        mock_request.content_type = "multipart/mixed; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW"
        assert detect_content_type(mock_request) == "multipart/mixed"

        # Test binary content types
        mock_request.content_type = "image/jpeg"
        assert detect_content_type(mock_request) == "image/jpeg"

        mock_request.content_type = "audio/mp3"
        assert detect_content_type(mock_request) == "audio/mp3"

        mock_request.content_type = "video/mp4"
        assert detect_content_type(mock_request) == "video/mp4"

        mock_request.content_type = "application/octet-stream"
        assert detect_content_type(mock_request) == "application/octet-stream"

    def test_detect_content_type_from_model(self):
        """Test detect_content_type_from_model function."""
        # Test model with file field
        assert detect_content_type_from_model(SampleFileModel) == "multipart/form-data"

        # Test model with image field
        assert detect_content_type_from_model(SampleImageModel) == "multipart/form-data"

        # Test model with audio field
        assert detect_content_type_from_model(SampleAudioModel) == "multipart/form-data"

        # Test model with video field
        assert detect_content_type_from_model(SampleVideoModel) == "multipart/form-data"

        # Test model with document field
        assert detect_content_type_from_model(SampleDocumentModel) == "multipart/form-data"

        # Test model with multiple file fields
        assert detect_content_type_from_model(SampleMultipleFilesModel) == "multipart/form-data"

        # Test model without file fields
        class SimpleModel(BaseModel):
            name: str
            age: int

        assert detect_content_type_from_model(SimpleModel) == "application/json"

    def test_check_for_file_fields(self):
        """Test check_for_file_fields function."""
        # Test model with file field
        assert check_for_file_fields(SampleFileModel) is True

        # Test model with image field
        assert check_for_file_fields(SampleImageModel) is True

        # Test model with audio field
        assert check_for_file_fields(SampleAudioModel) is True

        # Test model with video field
        assert check_for_file_fields(SampleVideoModel) is True

        # Test model with document field
        assert check_for_file_fields(SampleDocumentModel) is True

        # Test model with multiple file fields
        assert check_for_file_fields(SampleMultipleFilesModel) is True

        # Test model without file fields
        class SimpleModel(BaseModel):
            name: str
            age: int

        assert check_for_file_fields(SimpleModel) is False
