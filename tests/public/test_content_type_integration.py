"""Integration tests for content type handling across different frameworks."""

import io
import json

import pytest
from flask import Blueprint, Flask, jsonify, request
from flask.views import MethodView
from flask_restful import Resource
from pydantic import BaseModel
from werkzeug.datastructures import FileStorage

from flask_x_openapi_schema import (
    ContentTypeHandler,
    OpenAPIMetaResponse,
    OpenAPIMetaResponseItem,
    RequestContentTypes,
    ResponseContentTypes,
)
from flask_x_openapi_schema.models.content_types import ContentTypeCategory
from flask_x_openapi_schema.models.file_models import FileField
from flask_x_openapi_schema.x.flask import OpenAPIMethodViewMixin, openapi_metadata
from flask_x_openapi_schema.x.flask_restful import (
    OpenAPIIntegrationMixin,
)
from flask_x_openapi_schema.x.flask_restful import (
    openapi_metadata as flask_restful_openapi_metadata,
)


# Test models
class JsonRequest(BaseModel):
    """JSON request model."""

    name: str
    age: int
    email: str = ""


class XmlRequest(BaseModel):
    """XML request model."""

    name: str
    age: int
    email: str = ""


class FileRequest(BaseModel):
    """File request model."""

    file: FileField
    description: str = ""


class JsonResponse(BaseModel):
    """JSON response model."""

    id: str
    name: str
    age: int
    email: str = ""


class XmlResponse(BaseModel):
    """XML response model."""

    id: str
    name: str
    age: int
    email: str = ""


class FileResponse(BaseModel):
    """File response model."""

    filename: str
    content_type: str
    size: int


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str
    message: str


# Custom content type handlers
xml_content_type = ContentTypeHandler(
    content_type="application/xml",
    category=ContentTypeCategory.TEXT,
    description="XML data",
)

csv_content_type = ContentTypeHandler(
    content_type="text/csv",
    category=ContentTypeCategory.TEXT,
    description="CSV data",
)


# Content type resolver function
def resolve_content_type(request):
    """Resolve content type based on request parameters."""
    if request.args.get("format") == "xml":
        return "application/xml"
    if request.args.get("format") == "csv":
        return "text/csv"
    return None


# Flask MethodView implementation
class ContentTypeView(OpenAPIMethodViewMixin, MethodView):
    """Content type view for testing."""

    @openapi_metadata(
        summary="Process different content types",
        description="Process requests with different content types",
        tags=["content-types"],
        request_content_types=RequestContentTypes(
            content_types={
                "application/json": JsonRequest,
                "application/xml": XmlRequest,
            },
            content_type_resolver=resolve_content_type,
        ),
        responses=OpenAPIMetaResponse(
            responses={
                "200": OpenAPIMetaResponseItem(
                    model=JsonResponse,
                    description="Successful response",
                    content_types=ResponseContentTypes(
                        content_types={
                            "application/json": JsonResponse,
                            "application/xml": XmlResponse,
                        }
                    ),
                ),
                "400": OpenAPIMetaResponseItem(
                    model=ErrorResponse,
                    description="Invalid request",
                ),
            }
        ),
    )
    def post(self, _x_body=None):
        """Process a request with different content types."""
        if not _x_body:
            return jsonify({"error": "Invalid request", "message": "No body provided"}), 400

        # Determine response content type
        response_format = request.args.get("format", "json")

        if response_format == "xml":
            # In a real implementation, this would return XML
            # For testing, we'll just return JSON with a different content type
            response = {
                "id": "123",
                "name": _x_body.name,
                "age": _x_body.age,
                "email": _x_body.email,
            }
            return jsonify(response), 200, {"Content-Type": "application/xml"}

        # Default to JSON
        response = {
            "id": "123",
            "name": _x_body.name,
            "age": _x_body.age,
            "email": _x_body.email,
        }
        return jsonify(response)


class FileUploadView(OpenAPIMethodViewMixin, MethodView):
    """File upload view for testing."""

    @openapi_metadata(
        summary="Upload a file",
        description="Upload a file with different content types",
        tags=["content-types"],
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
    def post(self, _x_file: FileRequest):
        """Upload a file."""
        file = _x_file.file
        return jsonify(
            {
                "filename": file.filename,
                "content_type": file.content_type,
                "size": len(file.read()),
                "description": _x_file.description,
            }
        )


# Flask-RESTful implementation
class ContentTypeResource(Resource):
    """Content type resource for testing."""

    @flask_restful_openapi_metadata(
        summary="Process different content types",
        description="Process requests with different content types",
        tags=["content-types"],
        request_content_types=RequestContentTypes(
            content_types={
                "application/json": JsonRequest,
                "application/xml": XmlRequest,
            },
            content_type_resolver=resolve_content_type,
        ),
        responses=OpenAPIMetaResponse(
            responses={
                "200": OpenAPIMetaResponseItem(
                    model=JsonResponse,
                    description="Successful response",
                    content_types=ResponseContentTypes(
                        content_types={
                            "application/json": JsonResponse,
                            "application/xml": XmlResponse,
                        }
                    ),
                ),
                "400": OpenAPIMetaResponseItem(
                    model=ErrorResponse,
                    description="Invalid request",
                ),
            }
        ),
    )
    def post(self, _x_body=None):
        """Process a request with different content types."""
        if not _x_body:
            return {"error": "Invalid request", "message": "No body provided"}, 400

        # Determine response content type
        response_format = request.args.get("format", "json")

        if response_format == "xml":
            # In a real implementation, this would return XML
            # For testing, we'll just return JSON with a different content type
            response = {
                "id": "123",
                "name": _x_body.name,
                "age": _x_body.age,
                "email": _x_body.email,
            }
            return response, 200, {"Content-Type": "application/xml"}

        # Default to JSON
        return {
            "id": "123",
            "name": _x_body.name,
            "age": _x_body.age,
            "email": _x_body.email,
        }


class FileUploadResource(Resource):
    """File upload resource for testing."""

    @flask_restful_openapi_metadata(
        summary="Upload a file",
        description="Upload a file with different content types",
        tags=["content-types"],
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
    def post(self, _x_file: FileRequest):
        """Upload a file."""
        file = _x_file.file
        return {
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(file.read()),
            "description": _x_file.description,
        }


@pytest.fixture
def json_data():
    """Create JSON test data."""
    return json.dumps({"name": "Test User", "age": 30, "email": "test@example.com"})


@pytest.fixture
def xml_data():
    """Create XML test data."""
    return """
    <root>
        <name>Test User</name>
        <age>30</age>
        <email>test@example.com</email>
    </root>
    """


@pytest.fixture
def test_file():
    """Create a test file for testing."""
    return FileStorage(
        stream=io.BytesIO(b"Test file content"),
        filename="test.txt",
        content_type="text/plain",
    )


@pytest.fixture
def flask_app():
    """Create a Flask app for testing."""
    app = Flask(__name__)
    bp = Blueprint("api", __name__, url_prefix="/api")

    # Register views
    ContentTypeView.register_to_blueprint(bp, "/content-types", "content_types")
    FileUploadView.register_to_blueprint(bp, "/files", "file_upload")

    app.register_blueprint(bp)
    return app


@pytest.fixture
def flask_restful_app():
    """Create a Flask-RESTful app for testing."""
    app = Flask(__name__)
    api = OpenAPIIntegrationMixin()
    api.init_app(app)

    # Register resources
    api.add_resource(ContentTypeResource, "/api/content-types")
    api.add_resource(FileUploadResource, "/api/files")

    return app


@pytest.fixture
def flask_client(flask_app):
    """Create a test client for the Flask app."""
    return flask_app.test_client()


@pytest.fixture
def flask_restful_client(flask_restful_app):
    """Create a test client for the Flask-RESTful app."""
    return flask_restful_app.test_client()


@pytest.mark.skip(reason="Content type integration needs to be updated in the library")
class TestFlaskContentTypes:
    """Integration tests for content types with Flask."""

    def test_json_request(self, flask_client, json_data):
        """Test processing a JSON request."""
        response = flask_client.post(
            "/api/content-types",
            data=json_data,
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["name"] == "Test User"
        assert data["age"] == 30
        assert data["email"] == "test@example.com"
        assert response.content_type == "application/json"

    def test_xml_request_with_format_param(self, flask_client, xml_data):
        """Test processing an XML request with format parameter."""
        # Use the format parameter to specify XML
        response = flask_client.post(
            "/api/content-types?format=xml",
            data=xml_data,
            content_type="application/xml",
        )
        assert response.status_code == 200
        # The response should have XML content type
        assert response.content_type == "application/xml"

    def test_file_upload(self, flask_client, test_file):
        """Test uploading a file."""
        response = flask_client.post(
            "/api/files",
            data={"file": test_file, "description": "Test file description"},
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["filename"] == "test.txt"
        assert data["content_type"] == "text/plain"
        assert data["size"] == len(b"Test file content")
        assert data["description"] == "Test file description"


@pytest.mark.skip(reason="Flask-RESTful content type integration needs to be updated in the library")
class TestFlaskRestfulContentTypes:
    """Integration tests for content types with Flask-RESTful."""

    def test_json_request(self, flask_restful_client, json_data):
        """Test processing a JSON request."""
        response = flask_restful_client.post(
            "/api/content-types",
            data=json_data,
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["name"] == "Test User"
        assert data["age"] == 30
        assert data["email"] == "test@example.com"
        assert response.content_type == "application/json"

    def test_xml_request_with_format_param(self, flask_restful_client, xml_data):
        """Test processing an XML request with format parameter."""
        # Use the format parameter to specify XML
        response = flask_restful_client.post(
            "/api/content-types?format=xml",
            data=xml_data,
            content_type="application/xml",
        )
        assert response.status_code == 200
        # The response should have XML content type
        assert response.content_type == "application/xml"

    def test_file_upload(self, flask_restful_client, test_file):
        """Test uploading a file."""
        response = flask_restful_client.post(
            "/api/files",
            data={"file": test_file, "description": "Test file description"},
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["filename"] == "test.txt"
        assert data["content_type"] == "text/plain"
        assert data["size"] == len(b"Test file content")
        assert data["description"] == "Test file description"
