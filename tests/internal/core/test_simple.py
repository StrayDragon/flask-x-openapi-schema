"""Simple test for the flask-x-openapi-schema library.

This module tests the basic functionality without using the openapi_metadata decorator.
"""

from __future__ import annotations

import json

import pytest
from flask import Flask
from pydantic import BaseModel, Field

from flask_x_openapi_schema import (
    BaseRespModel,
)
from flask_x_openapi_schema._opt_deps._flask_restful import Api, Resource


# Define Pydantic models for request and response
class ItemRequest(BaseModel):
    """Request model for creating an item."""

    name: str = Field(..., description="The name of the item")
    description: str | None = Field(None, description="The description of the item")
    price: float = Field(..., description="The price of the item")
    tags: list[str] = Field(default_factory=list, description="Tags for the item")


class ItemResponse(BaseRespModel):
    """Response model for an item."""

    id: str = Field(..., description="The ID of the item")
    name: str = Field(..., description="The name of the item")
    description: str | None = Field(None, description="The description of the item")
    price: float = Field(..., description="The price of the item")
    tags: list[str] = Field(default_factory=list, description="Tags for the item")


# Define a Flask-RESTful resource without OpenAPI metadata
class ItemResource(Resource):
    """Resource for managing items."""

    def get(self, item_id):
        """Get an item by ID."""
        # In a real app, this would fetch from a database
        response = ItemResponse(
            id=item_id,
            name="Test Item",
            description="This is a test item",
            price=10.99,
            tags=["test", "example"],
        )
        return response.to_response()

    def post(self, item_id):
        """Create a new item."""
        # In a real app, this would save to a database
        from flask import request

        # Get the request data
        data = request.get_json()

        # Create a request model
        request_model = ItemRequest(**data)

        # Create a response
        response = ItemResponse(
            id=item_id,
            name=request_model.name,
            description=request_model.description,
            price=request_model.price,
            tags=request_model.tags,
        )

        return response.to_response(201)


@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    # Create a Flask app
    flask_app = Flask(__name__)

    # Create an API
    api = Api(flask_app)

    # Register the resources
    api.add_resource(ItemResource, "/items/<string:item_id>")

    return flask_app


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()


def test_get_item(client):
    """Test getting an item by ID."""
    response = client.get("/items/test-item-id")
    assert response.status_code == 200

    data = json.loads(response.data)
    assert data["id"] == "test-item-id"
    assert data["name"] == "Test Item"
    assert data["price"] == 10.99


def test_create_item(client):
    """Test creating a new item."""
    response = client.post(
        "/items/new-item-id",
        json={
            "name": "New Item",
            "description": "This is a new item",
            "price": 15.99,
            "tags": ["new", "test"],
        },
    )
    assert response.status_code == 201

    data = json.loads(response.data)
    assert data["id"] == "new-item-id"
    assert data["name"] == "New Item"
    assert data["description"] == "This is a new item"
    assert data["price"] == 15.99
    assert data["tags"] == ["new", "test"]
