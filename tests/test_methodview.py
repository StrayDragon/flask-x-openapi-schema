"""
Test for the OpenAPIMethodViewMixin class.

This module tests the OpenAPIMethodViewMixin class with the openapi_metadata decorator.
"""

import json
import pytest
from typing import List, Optional

from flask import Flask, Blueprint
from flask.views import MethodView
from pydantic import BaseModel, Field

from flask_x_openapi_schema import (
    BaseRespModel,
    OpenAPIBlueprintMixin,
    OpenAPIMethodViewMixin,
    openapi_metadata,
)


# Define Pydantic models for request and response
class ItemRequest(BaseModel):
    """Request model for creating an item."""

    name: str = Field(..., description="The name of the item")
    description: Optional[str] = Field(None, description="The description of the item")
    price: float = Field(..., description="The price of the item")
    tags: List[str] = Field(default_factory=list, description="Tags for the item")


class ItemResponse(BaseRespModel):
    """Response model for an item."""

    id: str = Field(..., description="The ID of the item")
    name: str = Field(..., description="The name of the item")
    description: Optional[str] = Field(None, description="The description of the item")
    price: float = Field(..., description="The price of the item")
    tags: List[str] = Field(default_factory=list, description="Tags for the item")


# Create a custom Blueprint class with OpenAPI support
class OpenAPIBlueprint(OpenAPIBlueprintMixin, Blueprint):
    pass


# Define a MethodView class with OpenAPI metadata
class ItemView(OpenAPIMethodViewMixin, MethodView):
    @openapi_metadata(
        summary="Get an item",
        description="Get an item by ID",
        tags=["Items"],
        operation_id="getItem",
    )
    def get(self, item_id: str):
        """Get an item by ID."""
        # In a real app, this would fetch from a database
        response = ItemResponse(
            id=item_id,
            name="Test Item",
            description="This is a test item",
            price=10.99,
            tags=["test", "example"],
        )
        return response

    @openapi_metadata(
        summary="Create an item",
        description="Create a new item",
        tags=["Items"],
        operation_id="createItem",
        request_body=ItemRequest,
    )
    def post(self, item_id: str, x_request_body: ItemRequest = None):
        """Create a new item."""
        # In a real app, this would save to a database
        response = ItemResponse(
            id=item_id,
            name=x_request_body.name,
            description=x_request_body.description,
            price=x_request_body.price,
            tags=x_request_body.tags,
        )
        return response, 201


@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    flask_app = Flask(__name__)

    # Create a blueprint with OpenAPI support
    api_bp = OpenAPIBlueprint("api", __name__, url_prefix="/api")

    # Register the MethodView
    ItemView.register_to_blueprint(api_bp, "/items/<string:item_id>", endpoint="item")

    # Register the blueprint with the app
    flask_app.register_blueprint(api_bp)

    # Add a route to get the OpenAPI schema
    @flask_app.route("/openapi.yaml")
    def get_openapi_schema():
        schema = api_bp.generate_openapi_schema(
            title="Items API",
            version="1.0.0",
            description="API for managing items",
        )
        return schema

    return flask_app


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()


def test_get_item(client):
    """Test getting an item by ID."""
    response = client.get("/api/items/test-item-id")
    assert response.status_code == 200

    data = json.loads(response.data)
    assert data["id"] == "test-item-id"
    assert data["name"] == "Test Item"
    assert data["price"] == 10.99


def test_create_item(client):
    """Test creating a new item."""
    request_data = {
        "name": "New Item",
        "description": "This is a new item",
        "price": 15.99,
        "tags": ["new", "test"],
    }

    response = client.post(
        "/api/items/new-item-id", json=request_data, content_type="application/json"
    )
    assert response.status_code == 201

    data = json.loads(response.data)
    assert data["id"] == "new-item-id"
    assert data["name"] == "New Item"
    assert data["description"] == "This is a new item"
    assert data["price"] == 15.99
    assert data["tags"] == ["new", "test"]


def test_generate_openapi_schema(client):
    """Test generating an OpenAPI schema."""
    response = client.get("/openapi.yaml")
    assert response.status_code == 200

    # Verify it's a string (YAML)
    assert isinstance(response.data.decode(), str)

    # Verify it contains some expected content
    content = response.data.decode()
    assert "Items API" in content
    assert "1.0.0" in content
    assert "/api/items/{item_id}" in content
