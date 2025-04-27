"""Tests for the file_models module to improve coverage."""

import io

import pytest
from werkzeug.datastructures import FileStorage

from flask_x_openapi_schema.models.file_models import (
    DocumentUploadModel,
    FileUploadModel,
    ImageUploadModel,
    MultipleFileUploadModel,
)


class TestFileModelsCoverage:
    """Tests for file_models to improve coverage."""

    def test_file_upload_model_validation(self):
        """Test FileUploadModel validation."""
        # Create a test file
        test_file = FileStorage(
            stream=io.BytesIO(b"Test file content"),
            filename="test.txt",
            content_type="text/plain",
        )

        # Create a model instance
        model = FileUploadModel(file=test_file)

        # Check that the model was created correctly
        assert model.file.filename == "test.txt"
        assert model.file.content_type == "text/plain"

        # Test validation with a non-file
        with pytest.raises(ValueError):
            FileUploadModel(file="not a file")

    def test_image_upload_model_validation(self):
        """Test ImageUploadModel validation."""
        # Create a test image file
        test_image = FileStorage(
            stream=io.BytesIO(b"Test image content"),
            filename="test.jpg",
            content_type="image/jpeg",
        )

        # Create a model instance
        model = ImageUploadModel(file=test_image)

        # Check that the model was created correctly
        assert model.file.filename == "test.jpg"
        assert model.file.content_type == "image/jpeg"

        # Test validation with a non-image file
        test_file = FileStorage(
            stream=io.BytesIO(b"Test file content"),
            filename="test.txt",
            content_type="text/plain",
        )

        with pytest.raises(ValueError):
            ImageUploadModel(file=test_file)

    def test_document_upload_model_validation(self):
        """Test DocumentUploadModel validation."""
        # Create a test document file
        test_document = FileStorage(
            stream=io.BytesIO(b"Test document content"),
            filename="test.pdf",
            content_type="application/pdf",
        )

        # Create a model instance
        model = DocumentUploadModel(file=test_document)

        # Check that the model was created correctly
        assert model.file.filename == "test.pdf"
        assert model.file.content_type == "application/pdf"

        # Test validation with a non-document file
        test_file = FileStorage(
            stream=io.BytesIO(b"Test file content"),
            filename="test.jpg",
            content_type="image/jpeg",
        )

        with pytest.raises(ValueError):
            DocumentUploadModel(file=test_file)

    def test_multiple_file_upload_model_validation(self):
        """Test MultipleFileUploadModel validation."""
        # Create test files
        test_file1 = FileStorage(
            stream=io.BytesIO(b"Test file content 1"),
            filename="test1.txt",
            content_type="text/plain",
        )
        test_file2 = FileStorage(
            stream=io.BytesIO(b"Test file content 2"),
            filename="test2.txt",
            content_type="text/plain",
        )

        # Create a model instance
        model = MultipleFileUploadModel(files=[test_file1, test_file2])

        # Check that the model was created correctly
        assert len(model.files) == 2
        assert model.files[0].filename == "test1.txt"
        assert model.files[1].filename == "test2.txt"

        # Test validation with a non-list
        with pytest.raises(ValueError):
            MultipleFileUploadModel(files="not a list")

        # Test validation with a list containing non-files
        with pytest.raises(ValueError):
            MultipleFileUploadModel(files=[test_file1, "not a file"])

        # Test validation with an empty list
        with pytest.raises(ValueError):
            MultipleFileUploadModel(files=[])
