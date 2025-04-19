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
    """Create a test image for testing."""
    return FileStorage(
        stream=io.BytesIO(b"Test image content"),
        filename="test.jpg",
        content_type="image/jpeg",
    )


@pytest.fixture
def test_document():
    """Create a test document for testing."""
    return FileStorage(
        stream=io.BytesIO(b"Test document content"),
        filename="test.pdf",
        content_type="application/pdf",
    )


class FileResource(Resource):
    """Resource for testing file uploads."""

    def post(self):
        """Handle file upload."""
        from flask import request

        # Get the file from the request
        file = request.files.get("file")
        if not file:
            return {"error": "No file provided"}, 400

        # Create a FileUploadModel
        try:
            model = FileUploadModel(file=file)
            return {
                "filename": model.file.filename,
                "content_type": model.file.content_type,
            }
        except ValueError as e:
            return {"error": str(e)}, 400


class ImageResource(Resource):
    """Resource for testing image uploads."""

    def post(self):
        """Handle image upload."""
        from flask import request

        # Get the file from the request
        file = request.files.get("image")
        if not file:
            return {"error": "No image provided"}, 400

        # Create an ImageUploadModel
        try:
            model = ImageUploadModel(file=file)
            return {
                "filename": model.file.filename,
                "content_type": model.file.content_type,
            }
        except ValueError as e:
            return {"error": str(e)}, 400


class DocumentResource(Resource):
    """Resource for testing document uploads."""

    def post(self):
        """Handle document upload."""
        from flask import request

        # Get the file from the request
        file = request.files.get("document")
        if not file:
            return {"error": "No document provided"}, 400

        # Create a DocumentUploadModel
        try:
            model = DocumentUploadModel(file=file)
            return {
                "filename": model.file.filename,
                "content_type": model.file.content_type,
            }
        except ValueError as e:
            return {"error": str(e)}, 400


@pytest.fixture
def app():
    """Create a Flask app for testing."""
    app = Flask(__name__)
    api = Api(app)

    # Register resources
    api.add_resource(FileResource, "/upload/file")
    api.add_resource(ImageResource, "/upload/image")
    api.add_resource(DocumentResource, "/upload/document")

    return app


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()


def test_file_upload(client, test_file):
    """Test uploading a file."""
    response = client.post(
        "/upload/file",
        data={"file": test_file},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["filename"] == "test.txt"
    assert data["content_type"] == "text/plain"


def test_image_upload(client, test_image):
    """Test uploading an image."""
    response = client.post(
        "/upload/image",
        data={"image": test_image},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["filename"] == "test.jpg"
    assert data["content_type"] == "image/jpeg"


def test_document_upload(client, test_document):
    """Test uploading a document."""
    response = client.post(
        "/upload/document",
        data={"document": test_document},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["filename"] == "test.pdf"
    assert data["content_type"] == "application/pdf"


def test_invalid_file_upload(client, test_document):
    """Test uploading an invalid file type."""
    # Create a fresh test document for each request to avoid closed file issues
    from werkzeug.datastructures import FileStorage
    import io

    # Try to upload a document to the file endpoint
    test_doc1 = FileStorage(
        stream=io.BytesIO(b"Test document content"),
        filename="test.pdf",
        content_type="application/pdf",
    )
    response = client.post(
        "/upload/file",
        data={"file": test_doc1},
        content_type="multipart/form-data",
    )
    # This should still work because FileUploadModel accepts any file
    assert response.status_code == 200

    # Try to upload a document to the image endpoint
    test_doc2 = FileStorage(
        stream=io.BytesIO(b"Test document content"),
        filename="test.pdf",
        content_type="application/pdf",
    )
    response = client.post(
        "/upload/image",
        data={"image": test_doc2},
        content_type="multipart/form-data",
    )
    # This should fail because ImageUploadModel only accepts images
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data