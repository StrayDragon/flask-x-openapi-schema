"""
Basic tests for the file upload features of flask-x-openapi-schema.

This module tests the file upload functionality of the library without using the openapi_metadata decorator.
"""

import io
import json
import pytest

from flask import Flask
from flask_restful import Api, Resource
from werkzeug.datastructures import FileStorage

from flask_x_openapi_schema import (
    FileUploadModel,
    ImageUploadModel,
    DocumentUploadModel,
)


@pytest.fixture
def test_file():
    """Create a test file for testing."""
    return FileStorage(
        stream=io.BytesIO(b"Test file content"),
        filename="test.txt",
        content_type="text/plain",
    )


@pytest.fixture
def test_image():
    """Create a test image file for testing."""
    return FileStorage(
        stream=io.BytesIO(b"Fake image content"),
        filename="test.jpg",
        content_type="image/jpeg",
    )


@pytest.fixture
def test_document():
    """Create a test document file for testing."""
    return FileStorage(
        stream=io.BytesIO(b"Fake document content"),
        filename="test.pdf",
        content_type="application/pdf",
    )


def test_file_upload_model(test_file):
    """Test the FileUploadModel class."""
    # Create a FileUploadModel instance
    file_model = FileUploadModel(file=test_file)

    # Test basic properties
    assert file_model.file == test_file
    assert file_model.file.filename == "test.txt"
    assert file_model.file.content_type == "text/plain"

    # Test that the model was created successfully
    assert isinstance(file_model, FileUploadModel)


def test_image_upload_model(test_image):
    """Test the ImageUploadModel class."""
    # Create an ImageUploadModel instance
    image_model = ImageUploadModel(file=test_image)

    # Test basic properties
    assert image_model.file == test_image
    assert image_model.file.filename == "test.jpg"
    assert image_model.file.content_type == "image/jpeg"

    # Test that the model was created successfully
    assert isinstance(image_model, ImageUploadModel)

    # Test with invalid extension
    # In a real application, this would be caught by the validator
    invalid_image = FileStorage(
        stream=io.BytesIO(b"Fake image content"),
        filename="test.txt",  # Not an image extension
        content_type="text/plain",
    )

    # Validation happens during creation in Pydantic
    # so we expect an exception
    with pytest.raises(Exception):
        ImageUploadModel(file=invalid_image)


def test_document_upload_model(test_document):
    """Test the DocumentUploadModel class."""
    # Create a DocumentUploadModel instance
    doc_model = DocumentUploadModel(file=test_document)

    # Test basic properties
    assert doc_model.file == test_document
    assert doc_model.file.filename == "test.pdf"
    assert doc_model.file.content_type == "application/pdf"

    # Test that the model was created successfully
    assert isinstance(doc_model, DocumentUploadModel)

    # Test with invalid extension
    # In a real application, this would be caught by the validator
    invalid_doc = FileStorage(
        stream=io.BytesIO(b"Fake document content"),
        filename="test.jpg",  # Not a document extension
        content_type="image/jpeg",
    )

    # Validation happens during creation in Pydantic
    # so we expect an exception
    with pytest.raises(Exception):
        DocumentUploadModel(file=invalid_doc)


class FileUploadResource(Resource):
    """Resource for handling file uploads."""

    def post(self):
        """Upload a file."""
        from flask import request

        # Get the file from the request
        if "file" not in request.files:
            return {"error": "No file provided"}, 400

        file = request.files["file"]

        # Process the file
        return {
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(file.read()),
        }, 201


@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    # Create a Flask app
    flask_app = Flask(__name__)

    # Create an API
    api = Api(flask_app)

    # Register the resources
    api.add_resource(FileUploadResource, "/upload")

    return flask_app


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()


def test_file_upload(client):
    """Test uploading a file."""
    # Upload a test file
    response = client.post(
        "/upload",
        data={"file": (io.BytesIO(b"Test file content"), "test.txt")},
        content_type="multipart/form-data",
    )

    # Check the response
    assert response.status_code == 201

    # Parse the response data
    data = json.loads(response.data)

    # Check the file info
    assert data["filename"] == "test.txt"
    assert data["content_type"] == "text/plain"
    assert data["size"] == 17  # Length of "Test file content"
