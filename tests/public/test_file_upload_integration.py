"""Integration tests for file upload functionality."""

import io
import json

import pytest
from flask import Blueprint, Flask, jsonify
from flask.views import MethodView
from flask_restful import Resource
from pydantic import BaseModel, Field
from werkzeug.datastructures import FileStorage

from flask_x_openapi_schema import (
    FileUploadModel,
    OpenAPIMetaResponse,
    OpenAPIMetaResponseItem,
)
from flask_x_openapi_schema.models.file_models import (
    AudioField,
    FileField,
    ImageField,
    PDFField,
    VideoField,
)
from flask_x_openapi_schema.x.flask import OpenAPIMethodViewMixin, openapi_metadata
from flask_x_openapi_schema.x.flask_restful import (
    OpenAPIIntegrationMixin,
)
from flask_x_openapi_schema.x.flask_restful import (
    openapi_metadata as flask_restful_openapi_metadata,
)


# 自定义上传模型
class AudioUploadModel(BaseModel):
    """Audio upload model."""

    file: AudioField


class DocumentUploadModel(BaseModel):
    """Document upload model."""

    file: PDFField


class ImageUploadModel(BaseModel):
    """Image upload model."""

    file: ImageField


class VideoUploadModel(BaseModel):
    """Video upload model."""

    file: VideoField


class MultipleFileUploadModel(BaseModel):
    """Multiple file upload model."""

    files: list[FileField] = Field(default_factory=list)


# Test response models
class FileResponse(BaseModel):
    """File upload response model."""

    filename: str
    content_type: str
    size: int


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str
    message: str


# Custom file upload models
class CustomImageUpload(ImageUploadModel):
    """Custom image upload model with additional fields."""

    title: str = Field(..., description="Image title")
    is_primary: bool = Field(False, description="Whether this is the primary image")


class CustomAudioUpload(AudioUploadModel):
    """Custom audio upload model with additional fields."""

    title: str = Field(..., description="Audio title")
    artist: str = Field("", description="Artist name")
    duration_seconds: int = Field(0, description="Duration in seconds")


class CustomVideoUpload(VideoUploadModel):
    """Custom video upload model with additional fields."""

    title: str = Field(..., description="Video title")
    description: str = Field("", description="Video description")
    resolution: str = Field("", description="Video resolution")


class CustomDocumentUpload(DocumentUploadModel):
    """Custom document upload model with additional fields."""

    title: str = Field(..., description="Document title")
    author: str = Field("", description="Document author")
    page_count: int = Field(0, description="Number of pages")


class CustomMultipleFileUpload(MultipleFileUploadModel):
    """Custom multiple file upload model with additional fields."""

    description: str = Field(..., description="Files description")
    category: str = Field("", description="Files category")


# Flask MethodView implementation
class FileUploadView(OpenAPIMethodViewMixin, MethodView):
    """File upload view for testing."""

    @openapi_metadata(
        summary="Upload a file",
        description="Upload a generic file",
        tags=["files"],
        responses=OpenAPIMetaResponse(
            responses={
                "200": OpenAPIMetaResponseItem(
                    model=FileResponse,
                    description="File uploaded successfully",
                ),
                "400": OpenAPIMetaResponseItem(
                    model=ErrorResponse,
                    description="Invalid file",
                ),
            }
        ),
    )
    def post(self, _x_file: FileUploadModel):
        """Upload a file."""
        file = _x_file.file
        return jsonify(
            {
                "filename": file.filename,
                "content_type": file.content_type,
                "size": len(file.read()),
            }
        )


class ImageUploadView(OpenAPIMethodViewMixin, MethodView):
    """Image upload view for testing."""

    @openapi_metadata(
        summary="Upload an image",
        description="Upload an image file",
        tags=["files"],
        responses=OpenAPIMetaResponse(
            responses={
                "200": OpenAPIMetaResponseItem(
                    model=FileResponse,
                    description="Image uploaded successfully",
                ),
                "400": OpenAPIMetaResponseItem(
                    model=ErrorResponse,
                    description="Invalid image",
                ),
            }
        ),
    )
    def post(self, _x_file: CustomImageUpload):
        """Upload an image."""
        file = _x_file.file
        return jsonify(
            {
                "filename": file.filename,
                "content_type": file.content_type,
                "size": len(file.read()),
                "title": _x_file.title,
                "is_primary": _x_file.is_primary,
            }
        )


class AudioUploadView(OpenAPIMethodViewMixin, MethodView):
    """Audio upload view for testing."""

    @openapi_metadata(
        summary="Upload an audio file",
        description="Upload an audio file",
        tags=["files"],
        responses=OpenAPIMetaResponse(
            responses={
                "200": OpenAPIMetaResponseItem(
                    model=FileResponse,
                    description="Audio uploaded successfully",
                ),
                "400": OpenAPIMetaResponseItem(
                    model=ErrorResponse,
                    description="Invalid audio file",
                ),
            }
        ),
    )
    def post(self, _x_file: CustomAudioUpload):
        """Upload an audio file."""
        file = _x_file.file
        return jsonify(
            {
                "filename": file.filename,
                "content_type": file.content_type,
                "size": len(file.read()),
                "title": _x_file.title,
                "artist": _x_file.artist,
                "duration_seconds": _x_file.duration_seconds,
            }
        )


class VideoUploadView(OpenAPIMethodViewMixin, MethodView):
    """Video upload view for testing."""

    @openapi_metadata(
        summary="Upload a video file",
        description="Upload a video file",
        tags=["files"],
        responses=OpenAPIMetaResponse(
            responses={
                "200": OpenAPIMetaResponseItem(
                    model=FileResponse,
                    description="Video uploaded successfully",
                ),
                "400": OpenAPIMetaResponseItem(
                    model=ErrorResponse,
                    description="Invalid video file",
                ),
            }
        ),
    )
    def post(self, _x_file: CustomVideoUpload):
        """Upload a video file."""
        file = _x_file.file
        return jsonify(
            {
                "filename": file.filename,
                "content_type": file.content_type,
                "size": len(file.read()),
                "title": _x_file.title,
                "description": _x_file.description,
                "resolution": _x_file.resolution,
            }
        )


class DocumentUploadView(OpenAPIMethodViewMixin, MethodView):
    """Document upload view for testing."""

    @openapi_metadata(
        summary="Upload a document",
        description="Upload a document file",
        tags=["files"],
        responses=OpenAPIMetaResponse(
            responses={
                "200": OpenAPIMetaResponseItem(
                    model=FileResponse,
                    description="Document uploaded successfully",
                ),
                "400": OpenAPIMetaResponseItem(
                    model=ErrorResponse,
                    description="Invalid document",
                ),
            }
        ),
    )
    def post(self, _x_file: CustomDocumentUpload):
        """Upload a document."""
        file = _x_file.file
        return jsonify(
            {
                "filename": file.filename,
                "content_type": file.content_type,
                "size": len(file.read()),
                "title": _x_file.title,
                "author": _x_file.author,
                "page_count": _x_file.page_count,
            }
        )


class MultipleFileUploadView(OpenAPIMethodViewMixin, MethodView):
    """Multiple file upload view for testing."""

    @openapi_metadata(
        summary="Upload multiple files",
        description="Upload multiple files at once",
        tags=["files"],
        responses=OpenAPIMetaResponse(
            responses={
                "200": OpenAPIMetaResponseItem(
                    model=FileResponse,
                    description="Files uploaded successfully",
                ),
                "400": OpenAPIMetaResponseItem(
                    model=ErrorResponse,
                    description="Invalid files",
                ),
            }
        ),
    )
    def post(self, _x_files: CustomMultipleFileUpload):
        """Upload multiple files."""
        files = _x_files.files
        return jsonify(
            {
                "file_count": len(files),
                "filenames": [f.filename for f in files],
                "content_types": [f.content_type for f in files],
                "sizes": [len(f.read()) for f in files],
                "description": _x_files.description,
                "category": _x_files.category,
            }
        )


# Flask-RESTful implementation
class FileUploadResource(Resource):
    """File upload resource for testing."""

    @flask_restful_openapi_metadata(
        summary="Upload a file",
        description="Upload a generic file",
        tags=["files"],
        responses=OpenAPIMetaResponse(
            responses={
                "200": OpenAPIMetaResponseItem(
                    model=FileResponse,
                    description="File uploaded successfully",
                ),
                "400": OpenAPIMetaResponseItem(
                    model=ErrorResponse,
                    description="Invalid file",
                ),
            }
        ),
    )
    def post(self, _x_file: FileUploadModel):
        """Upload a file."""
        file = _x_file.file
        return {
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(file.read()),
        }


class ImageUploadResource(Resource):
    """Image upload resource for testing."""

    @flask_restful_openapi_metadata(
        summary="Upload an image",
        description="Upload an image file",
        tags=["files"],
        responses=OpenAPIMetaResponse(
            responses={
                "200": OpenAPIMetaResponseItem(
                    model=FileResponse,
                    description="Image uploaded successfully",
                ),
                "400": OpenAPIMetaResponseItem(
                    model=ErrorResponse,
                    description="Invalid image",
                ),
            }
        ),
    )
    def post(self, _x_file: CustomImageUpload):
        """Upload an image."""
        file = _x_file.file
        return {
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(file.read()),
            "title": _x_file.title,
            "is_primary": _x_file.is_primary,
        }


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
def test_audio():
    """Create a test audio file for testing."""
    return FileStorage(
        stream=io.BytesIO(b"Test audio content"),
        filename="test.mp3",
        content_type="audio/mp3",
    )


@pytest.fixture
def test_video():
    """Create a test video file for testing."""
    return FileStorage(
        stream=io.BytesIO(b"Test video content"),
        filename="test.mp4",
        content_type="video/mp4",
    )


@pytest.fixture
def test_document():
    """Create a test document for testing."""
    return FileStorage(
        stream=io.BytesIO(b"Test document content"),
        filename="test.pdf",
        content_type="application/pdf",
    )


@pytest.fixture
def flask_app():
    """Create a Flask app for testing."""
    app = Flask(__name__)
    bp = Blueprint("api", __name__, url_prefix="/api")

    # Register views
    FileUploadView.register_to_blueprint(bp, "/files", "file_upload")
    ImageUploadView.register_to_blueprint(bp, "/images", "image_upload")
    AudioUploadView.register_to_blueprint(bp, "/audio", "audio_upload")
    VideoUploadView.register_to_blueprint(bp, "/videos", "video_upload")
    DocumentUploadView.register_to_blueprint(bp, "/documents", "document_upload")
    MultipleFileUploadView.register_to_blueprint(bp, "/multiple-files", "multiple_file_upload")

    app.register_blueprint(bp)
    return app


@pytest.fixture
def flask_restful_app():
    """Create a Flask-RESTful app for testing."""
    app = Flask(__name__)
    api = OpenAPIIntegrationMixin()
    api.init_app(app)

    # Register resources
    api.add_resource(FileUploadResource, "/api/files")
    api.add_resource(ImageUploadResource, "/api/images")

    return app


@pytest.fixture
def flask_client(flask_app):
    """Create a test client for the Flask app."""
    return flask_app.test_client()


@pytest.fixture
def flask_restful_client(flask_restful_app):
    """Create a test client for the Flask-RESTful app."""
    return flask_restful_app.test_client()


class TestFlaskFileUpload:
    """Integration tests for file uploads with Flask."""

    def test_file_upload(self, flask_client, test_file):
        """Test uploading a file."""
        response = flask_client.post(
            "/api/files",
            data={"file": test_file},
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["filename"] == "test.txt"
        assert data["content_type"] == "text/plain"
        assert data["size"] == len(b"Test file content")

    def test_image_upload(self, flask_client, test_image):
        """Test uploading an image."""
        response = flask_client.post(
            "/api/images",
            data={"file": test_image, "title": "Test Image", "is_primary": "true"},
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["filename"] == "test.jpg"
        assert data["content_type"] == "image/jpeg"
        assert data["size"] == len(b"Test image content")
        assert data["title"] == "Test Image"
        assert data["is_primary"] is True

    def test_audio_upload(self, flask_client, test_audio):
        """Test uploading an audio file."""
        response = flask_client.post(
            "/api/audio",
            data={
                "file": test_audio,
                "title": "Test Audio",
                "artist": "Test Artist",
                "duration_seconds": "180",
            },
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["filename"] == "test.mp3"
        assert data["content_type"] == "audio/mp3"
        assert data["size"] == len(b"Test audio content")
        assert data["title"] == "Test Audio"
        assert data["artist"] == "Test Artist"
        assert data["duration_seconds"] == 180


@pytest.mark.skip(reason="Flask-RESTful integration needs to be updated in the library")
class TestFlaskRestfulFileUpload:
    """Integration tests for file uploads with Flask-RESTful."""

    def test_file_upload(self, flask_restful_client, test_file):
        """Test uploading a file."""
        response = flask_restful_client.post(
            "/api/files",
            data={"file": test_file},
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["filename"] == "test.txt"
        assert data["content_type"] == "text/plain"
        assert data["size"] == len(b"Test file content")

    def test_image_upload(self, flask_restful_client, test_image):
        """Test uploading an image."""
        response = flask_restful_client.post(
            "/api/images",
            data={"file": test_image, "title": "Test Image", "is_primary": "true"},
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["filename"] == "test.jpg"
        assert data["content_type"] == "image/jpeg"
        assert data["size"] == len(b"Test image content")
        assert data["title"] == "Test Image"
        assert data["is_primary"] is True
