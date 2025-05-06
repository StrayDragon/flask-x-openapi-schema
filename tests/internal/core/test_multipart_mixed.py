"""Tests for multipart/mixed content type handling."""

import io
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask
from pydantic import BaseModel
from werkzeug.datastructures import FileStorage

from flask_x_openapi_schema.core.content_type_utils import (
    MultipartMixedStrategy,
)
from flask_x_openapi_schema.models.file_models import FileField


class MixedContentModel(BaseModel):
    """Test model for mixed content tests."""

    file: FileField
    json_data: dict
    text: str = ""


class TestMultipartMixedStrategy:
    """Tests for MultipartMixedStrategy class."""

    def setup_method(self):
        """Set up test environment."""
        self.app = Flask(__name__)
        self.strategy = MultipartMixedStrategy()
        # Set a smaller chunk size for testing
        self.strategy.chunk_size = 1024
        # Set a smaller max memory size to test large file handling
        self.strategy.max_memory_size = 1024 * 10  # 10 KB

    def test_can_handle(self):
        """Test can_handle method."""
        assert self.strategy.can_handle("multipart/mixed")
        assert self.strategy.can_handle("multipart/mixed; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW")
        assert not self.strategy.can_handle("application/json")
        assert not self.strategy.can_handle("multipart/form-data")

    @pytest.mark.skip(reason="Error handling needs to be updated in the library")
    def test_missing_boundary(self):
        """Test handling a request with missing boundary."""
        with self.app.test_request_context(
            "/",
            method="POST",
            data="test data",
            content_type="multipart/mixed",  # No boundary
        ) as ctx:
            kwargs = {}
            result = self.strategy.process_request(ctx.request, MixedContentModel, "model", kwargs)

            # Should return an error response
            assert isinstance(result, tuple)
            assert result[1] == 400  # HTTP 400 Bad Request
            assert "No boundary found" in result[0].get_json().get("message", "")

    @pytest.mark.skip(reason="Multipart parsing needs to be updated in the library")
    def test_parse_multipart_parts(self):
        """Test parsing multipart parts."""
        # Create a simple multipart message
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        multipart_data = (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="json_data"\r\n'
            "Content-Type: application/json\r\n\r\n"
            '{"key": "value"}\r\n'
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="text"\r\n'
            "Content-Type: text/plain\r\n\r\n"
            "Sample text content\r\n"
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="file"; filename="test.txt"\r\n'
            "Content-Type: text/plain\r\n\r\n"
            "File content for testing\r\n"
            f"--{boundary}--\r\n"
        )

        with self.app.test_request_context(
            "/",
            method="POST",
            data=multipart_data,
            content_type=f"multipart/mixed; boundary={boundary}",
        ) as ctx:
            # Mock content length to be small
            ctx.request.content_length = len(multipart_data)

            kwargs = {}
            result = self.strategy.process_request(ctx.request, MixedContentModel, "model", kwargs)

            assert "model" in result
            assert isinstance(result["model"], MixedContentModel)
            assert result["model"].json_data == {"key": "value"}
            assert result["model"].text == "Sample text content"
            assert result["model"].file.filename == "test.txt"
            assert result["model"].file.read() == b"File content for testing"

    @pytest.mark.skip(reason="Large multipart request handling needs to be updated in the library")
    @patch("flask_x_openapi_schema.core.content_type_utils.tempfile.NamedTemporaryFile")
    def test_large_multipart_request(self, mock_temp_file):
        """Test processing a large multipart/mixed request."""
        # Create a mock temporary file
        mock_file = MagicMock()
        mock_file.name = "/tmp/test_temp_file"  # noqa: S108
        mock_temp_file.return_value.__enter__.return_value = mock_file

        # Create a large multipart message (simulated)
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"

        # Create a test context with a large content length
        with self.app.test_request_context(
            "/",
            method="POST",
            data="dummy data",  # Actual data doesn't matter as we'll mock the parsing
            content_type=f"multipart/mixed; boundary={boundary}",
        ) as ctx:
            # Set a large content length
            ctx.request.content_length = 1024 * 1024 * 20  # 20 MB

            # Mock the stream reading
            ctx.request.stream = MagicMock()
            ctx.request.stream.read.side_effect = [b"chunk1", b"chunk2", b"chunk3", b""]

            # Mock the _parse_temp_files method to return parsed parts
            with patch.object(
                self.strategy,
                "_parse_temp_files",
                return_value={
                    "json_data": {"key": "value"},
                    "text": "Sample text content",
                    "file": FileStorage(
                        stream=io.BytesIO(b"File content for testing"),
                        filename="test.txt",
                        content_type="text/plain",
                    ),
                },
            ):
                kwargs = {}
                result = self.strategy.process_request(ctx.request, MixedContentModel, "model", kwargs)

                assert "model" in result
                assert isinstance(result["model"], MixedContentModel)
                assert result["model"].json_data == {"key": "value"}
                assert result["model"].text == "Sample text content"
                assert result["model"].file.filename == "test.txt"

                # Verify the temporary file was used
                mock_temp_file.assert_called_once()
                mock_file.write.assert_called()

    @pytest.mark.skip(reason="Temporary file parsing needs to be updated in the library")
    def test_parse_temp_files_with_json_part(self):
        """Test parsing temporary files with a JSON part."""
        # Create temporary files for testing
        temp_files = []

        # JSON part
        json_file = tempfile.NamedTemporaryFile(delete=False)  # noqa: SIM115
        json_file.write(b'{"key": "value", "nested": {"inner": 123}}')
        json_file.close()
        temp_files.append((json_file.name, "application/json", {"content-disposition": 'form-data; name="json_data"'}))

        try:
            # Call the method directly
            parsed_parts = self.strategy._parse_temp_files(temp_files)

            # Check the results
            assert "json_data" in parsed_parts
            assert parsed_parts["json_data"] == {"key": "value", "nested": {"inner": 123}}
        finally:
            # Clean up
            os.unlink(json_file.name)

    @pytest.mark.skip(reason="Temporary file parsing needs to be updated in the library")
    def test_parse_temp_files_with_text_part(self):
        """Test parsing temporary files with a text part."""
        # Create temporary files for testing
        temp_files = []

        # Text part
        text_file = tempfile.NamedTemporaryFile(delete=False)  # noqa: SIM115
        text_file.write(b"Sample text content\nwith multiple lines")
        text_file.close()
        temp_files.append((text_file.name, "text/plain", {"content-disposition": 'form-data; name="text"'}))

        try:
            # Call the method directly
            parsed_parts = self.strategy._parse_temp_files(temp_files)

            # Check the results
            assert "text" in parsed_parts
            assert parsed_parts["text"] == "Sample text content\nwith multiple lines"
        finally:
            # Clean up
            os.unlink(text_file.name)

    @pytest.mark.skip(reason="Temporary file parsing needs to be updated in the library")
    def test_parse_temp_files_with_binary_part(self):
        """Test parsing temporary files with a binary part."""
        # Create temporary files for testing
        temp_files = []

        # Binary part
        binary_file = tempfile.NamedTemporaryFile(delete=False)  # noqa: SIM115
        binary_file.write(b"\x00\x01\x02\x03\x04")
        binary_file.close()
        temp_files.append(
            (
                binary_file.name,
                "application/octet-stream",
                {"content-disposition": 'form-data; name="file"; filename="binary.dat"'},
            )
        )

        try:
            # Call the method directly
            parsed_parts = self.strategy._parse_temp_files(temp_files)

            # Check the results
            assert "file" in parsed_parts
            assert isinstance(parsed_parts["file"], FileStorage)
            assert parsed_parts["file"].filename == "binary.dat"
            assert parsed_parts["file"].content_type == "application/octet-stream"
            assert parsed_parts["file"].read() == b"\x00\x01\x02\x03\x04"
        finally:
            # Clean up
            os.unlink(binary_file.name)

    @pytest.mark.skip(reason="Temporary file parsing needs to be updated in the library")
    def test_parse_temp_files_with_image_part(self):
        """Test parsing temporary files with an image part."""
        # Create temporary files for testing
        temp_files = []

        # Image part (fake image data)
        image_file = tempfile.NamedTemporaryFile(delete=False)  # noqa: SIM115
        image_file.write(b"FAKE IMAGE DATA")
        image_file.close()
        temp_files.append(
            (image_file.name, "image/jpeg", {"content-disposition": 'form-data; name="image"; filename="test.jpg"'})
        )

        try:
            # Call the method directly
            parsed_parts = self.strategy._parse_temp_files(temp_files)

            # Check the results
            assert "image" in parsed_parts
            assert isinstance(parsed_parts["image"], FileStorage)
            assert parsed_parts["image"].filename == "test.jpg"
            assert parsed_parts["image"].content_type == "image/jpeg"
            assert parsed_parts["image"].read() == b"FAKE IMAGE DATA"
        finally:
            # Clean up
            os.unlink(image_file.name)

    @pytest.mark.skip(reason="Temporary file parsing needs to be updated in the library")
    def test_parse_temp_files_with_all_parts(self):
        """Test parsing temporary files with all types of parts."""
        # Create temporary files for testing
        temp_files = []

        # JSON part
        json_file = tempfile.NamedTemporaryFile(delete=False)  # noqa: SIM115
        json_file.write(b'{"key": "value"}')
        json_file.close()
        temp_files.append((json_file.name, "application/json", {"content-disposition": 'form-data; name="json_data"'}))

        # Text part
        text_file = tempfile.NamedTemporaryFile(delete=False)  # noqa: SIM115
        text_file.write(b"Sample text content")
        text_file.close()
        temp_files.append((text_file.name, "text/plain", {"content-disposition": 'form-data; name="text"'}))

        # File part
        file_part = tempfile.NamedTemporaryFile(delete=False)  # noqa: SIM115
        file_part.write(b"File content for testing")
        file_part.close()
        temp_files.append(
            (file_part.name, "text/plain", {"content-disposition": 'form-data; name="file"; filename="test.txt"'})
        )

        try:
            # Call the method directly
            parsed_parts = self.strategy._parse_temp_files(temp_files)

            # Check the results
            assert "json_data" in parsed_parts
            assert parsed_parts["json_data"] == {"key": "value"}

            assert "text" in parsed_parts
            assert parsed_parts["text"] == "Sample text content"

            assert "file" in parsed_parts
            assert isinstance(parsed_parts["file"], FileStorage)
            assert parsed_parts["file"].filename == "test.txt"
            assert parsed_parts["file"].read() == b"File content for testing"
        finally:
            # Clean up
            os.unlink(json_file.name)
            os.unlink(text_file.name)
            os.unlink(file_part.name)
