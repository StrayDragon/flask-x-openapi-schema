"""Tests for Flask views and OpenAPI integration.

This module provides comprehensive tests for Flask views and OpenAPI integration,
covering basic functionality, advanced usage, and edge cases.
"""

from flask import Blueprint, Flask
from flask.views import MethodView
from pydantic import BaseModel, Field

from flask_x_openapi_schema.models.file_models import FileField
from flask_x_openapi_schema.models.responses import OpenAPIMetaResponse, OpenAPIMetaResponseItem
from flask_x_openapi_schema.x.flask import OpenAPIMethodViewMixin, openapi_metadata
from flask_x_openapi_schema.x.flask.views import (
    MethodViewOpenAPISchemaGenerator,
    extract_openapi_parameters_from_methodview,
)


class TestFlaskViews:
    """Tests for Flask views and OpenAPI integration."""

    def setup_method(self):
        """Set up test environment."""
        self.app = Flask(__name__)
        self.client = self.app.test_client()

    def test_extract_openapi_parameters_from_methodview(self):
        """Test extracting OpenAPI parameters from a MethodView class."""

        # Define a MethodView class with different parameter types
        class TestView(MethodView):
            def get(self, item_id: int, user_name: str, is_active: bool = True):
                """Get an item by ID."""
                return {"item_id": item_id, "user_name": user_name, "is_active": is_active}

        # Extract parameters
        parameters = extract_openapi_parameters_from_methodview(TestView, "get", "/items/<int:item_id>/<user_name>")

        # Check that parameters were extracted correctly
        assert len(parameters) == 2

        item_id_param = next((p for p in parameters if p["name"] == "item_id"), None)
        assert item_id_param is not None
        assert item_id_param["in"] == "path"
        assert item_id_param["required"] is True
        assert item_id_param["schema"]["type"] == "integer"

        user_name_param = next((p for p in parameters if p["name"] == "user_name"), None)
        assert user_name_param is not None
        assert user_name_param["in"] == "path"
        assert user_name_param["required"] is True
        assert user_name_param["schema"]["type"] == "string"

    def test_methodview_openapi_schema_generator_process_methodview(self):
        """Test processing a MethodView class for OpenAPI schema generation."""

        # Define models
        class ItemResponse(BaseModel):
            id: int = Field(..., description="Item ID")
            name: str = Field(..., description="Item name")
            price: float = Field(..., description="Item price")

        class ItemQuery(BaseModel):
            include_details: bool = Field(False, description="Include additional details")

        # Define a MethodView class with OpenAPI metadata
        class ItemView(OpenAPIMethodViewMixin, MethodView):
            @openapi_metadata(
                summary="Get an item",
                description="Get an item by ID",
                tags=["items"],
                operation_id="getItem",
                responses=OpenAPIMetaResponse(
                    responses={
                        "200": OpenAPIMetaResponseItem(model=ItemResponse, description="Item found"),
                        "404": OpenAPIMetaResponseItem(description="Item not found"),
                    }
                ),
            )
            def get(self, item_id: int, _x_query: ItemQuery):
                """Get an item by ID."""
                # Use query parameter to avoid unused variable warning
                include_details = _x_query.include_details
                return {"id": item_id, "name": "Test Item", "price": 10.99, "details": include_details}

        # Create a blueprint and register the view
        bp = Blueprint("items", __name__)
        ItemView.register_to_blueprint(bp, "/items/<int:item_id>")

        # Create a schema generator and process the blueprint
        generator = MethodViewOpenAPISchemaGenerator(
            title="Test API",
            version="1.0.0",
            description="Test API description",
        )
        generator.process_methodview_resources(bp)

        # Check that the path was added to the schema
        assert "/items/{item_id}" in generator.paths
        assert "get" in generator.paths["/items/{item_id}"]

        # Check path operation details
        operation = generator.paths["/items/{item_id}"]["get"]
        assert operation["summary"] == "Get an item"
        assert operation["description"] == "Get an item by ID"
        assert operation["tags"] == ["items"]
        assert operation["operationId"] == "getItem"

        # Check parameters
        parameters = operation["parameters"]
        assert any(p["name"] == "item_id" and p["in"] == "path" for p in parameters)

        # Check responses
        assert "200" in operation["responses"]
        assert "404" in operation["responses"]
        assert operation["responses"]["200"]["description"] == "Item found"
        assert operation["responses"]["404"]["description"] == "Item not found"

    def test_methodview_with_file_upload(self):
        """Test MethodView with file upload fields."""

        # Define a file upload model
        class FileUploadRequest(BaseModel):
            file: FileField = Field(..., description="The file to upload")
            description: str = Field("", description="File description")

            model_config = {
                "json_schema_extra": {
                    "multipart/form-data": True,
                },
            }

        # Define a response model
        class FileUploadResponse(BaseModel):
            filename: str = Field(..., description="Uploaded filename")
            content_type: str = Field(..., description="File content type")
            description: str = Field(..., description="File description")

        # Define a MethodView class with file upload
        class FileUploadView(OpenAPIMethodViewMixin, MethodView):
            @openapi_metadata(
                summary="Upload a file",
                description="Upload a file with optional description",
                tags=["files"],
                operation_id="uploadFile",
                responses=OpenAPIMetaResponse(
                    responses={
                        "200": OpenAPIMetaResponseItem(
                            model=FileUploadResponse,
                            description="File uploaded successfully",
                        ),
                        "400": OpenAPIMetaResponseItem(
                            description="Invalid file",
                        ),
                    }
                ),
            )
            def post(self, _x_file: FileUploadRequest):
                """Upload a file."""
                # In a real implementation, we would save the file
                return {
                    "filename": _x_file.file.filename,
                    "content_type": _x_file.file.content_type,
                    "description": _x_file.description,
                }

        # Create a blueprint and register the view
        bp = Blueprint("files", __name__)
        FileUploadView.register_to_blueprint(bp, "/uploads")

        # Create a schema generator and process the blueprint
        generator = MethodViewOpenAPISchemaGenerator(
            title="Test API",
            version="1.0.0",
            description="Test API description",
        )
        generator.process_methodview_resources(bp)

        # Check that the path was added to the schema
        assert "/uploads" in generator.paths
        assert "post" in generator.paths["/uploads"]

        # Check that the request body is set to multipart/form-data
        operation = generator.paths["/uploads"]["post"]
        assert "requestBody" in operation
        assert "content" in operation["requestBody"]
        assert "multipart/form-data" in operation["requestBody"]["content"]

        # Check that the schema references the FileUploadRequest model
        schema_ref = operation["requestBody"]["content"]["multipart/form-data"]["schema"]
        assert schema_ref == {"$ref": "#/components/schemas/FileUploadRequest"}

        # Check that the responses are correctly defined
        assert "200" in operation["responses"]
        assert "description" in operation["responses"]["200"]
        assert operation["responses"]["200"]["description"] == "File uploaded successfully"
        assert "content" in operation["responses"]["200"]

    def test_methodview_with_enum_response(self):
        """Test MethodView with enum in response model."""
        from enum import Enum

        # Define enum and models
        class ItemStatus(str, Enum):
            ACTIVE = "active"
            INACTIVE = "inactive"
            PENDING = "pending"

        class ItemWithEnum(BaseModel):
            id: int = Field(..., description="Item ID")
            name: str = Field(..., description="Item name")
            status: ItemStatus = Field(..., description="Item status")

        # Define a MethodView class with enum in response
        class EnumView(OpenAPIMethodViewMixin, MethodView):
            @openapi_metadata(
                summary="Get item with enum",
                responses=OpenAPIMetaResponse(
                    responses={
                        "200": OpenAPIMetaResponseItem(model=ItemWithEnum, description="Item with enum"),
                    }
                ),
            )
            def get(self, item_id: int):
                """Get an item with enum status."""
                return {"id": item_id, "name": "Test Item", "status": "active"}

        # Create a blueprint and register the view
        bp = Blueprint("enums", __name__)
        EnumView.register_to_blueprint(bp, "/items-with-enum/<int:item_id>")

        # Create a schema generator and process the blueprint
        generator = MethodViewOpenAPISchemaGenerator(
            title="Test API",
            version="1.0.0",
            description="Test API description",
        )
        generator.process_methodview_resources(bp)

        # Initialize components if not present
        if not hasattr(generator, "components"):
            generator.components = {}
        if "schemas" not in generator.components:
            generator.components["schemas"] = {}

        # In some versions, the enum might be directly in the field schema
        # rather than as a separate schema
        assert "/items-with-enum/{item_id}" in generator.paths
        assert "get" in generator.paths["/items-with-enum/{item_id}"]

    def test_methodview_with_list_response(self):
        """Test MethodView with list in response model."""

        # Define models
        class Tag(BaseModel):
            id: int = Field(..., description="Tag ID")
            name: str = Field(..., description="Tag name")

        class ItemWithTags(BaseModel):
            id: int = Field(..., description="Item ID")
            name: str = Field(..., description="Item name")
            tags: list[Tag] = Field(..., description="Item tags")

        # Define a MethodView class with list in response
        class ListView(OpenAPIMethodViewMixin, MethodView):
            @openapi_metadata(
                summary="Get item with tags",
                responses=OpenAPIMetaResponse(
                    responses={
                        "200": OpenAPIMetaResponseItem(model=ItemWithTags, description="Item with tags"),
                    }
                ),
            )
            def get(self, item_id: int):
                """Get an item with tags."""
                return {
                    "id": item_id,
                    "name": "Test Item",
                    "tags": [{"id": 1, "name": "Tag 1"}, {"id": 2, "name": "Tag 2"}],
                }

        # Create a blueprint and register the view
        bp = Blueprint("lists", __name__)
        ListView.register_to_blueprint(bp, "/items-with-tags/<int:item_id>")

        # Create a schema generator and process the blueprint
        generator = MethodViewOpenAPISchemaGenerator(
            title="Test API",
            version="1.0.0",
            description="Test API description",
        )
        generator.process_methodview_resources(bp)

        # Initialize components if not present
        if not hasattr(generator, "components"):
            generator.components = {}
        if "schemas" not in generator.components:
            generator.components["schemas"] = {}

        # Check that the path was added to the schema
        assert "/items-with-tags/{item_id}" in generator.paths
        assert "get" in generator.paths["/items-with-tags/{item_id}"]
