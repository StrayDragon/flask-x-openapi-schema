"""
Test for the OpenAPIIntegrationMixin class.

This module tests the OpenAPIIntegrationMixin class without using the openapi_metadata decorator.
"""

import pytest
from typing import List, Optional

from flask import Flask
from flask_restful import Api, Resource
from pydantic import BaseModel, Field

from flask_x_openapi_schema import (
    BaseRespModel,
    OpenAPIIntegrationMixin,
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


# Define a Flask-RESTful resource without OpenAPI metadata
class ItemResource(Resource):
    """Resource for managing items."""

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
        return response.to_response()


@pytest.fixture
def app_with_api():
    """Create a Flask app with OpenAPI integration."""
    # Create a Flask app
    flask_app = Flask(__name__)

    # Create an OpenAPI-enabled API
    class OpenAPIApi(OpenAPIIntegrationMixin, Api):
        pass

    api = OpenAPIApi(flask_app)

    # Register the resources
    api.add_resource(
        ItemResource, "/api/items/<string:item_id>", endpoint="item_resource"
    )

    return flask_app, api


@pytest.fixture
def client(app_with_api):
    """Create a test client for the app."""
    app, _ = app_with_api
    return app.test_client()


def test_generate_openapi_schema(app_with_api):
    """Test generating an OpenAPI schema."""
    # Unpack the fixture
    app, api = app_with_api

    # Generate schema in YAML format (default)
    schema_yaml = api.generate_openapi_schema(
        title="Test API",
        version="1.0.0",
        description="API for testing OpenAPIIntegrationMixin",
    )

    # Verify it's a string (YAML)
    assert isinstance(schema_yaml, str)

    # Verify it contains some expected content
    assert "Test API" in schema_yaml
    assert "1.0.0" in schema_yaml

    # Generate schema in JSON format
    schema_json = api.generate_openapi_schema(
        title="Test API",
        version="1.0.0",
        description="API for testing OpenAPIIntegrationMixin",
        output_format="json",
    )

    # Verify it's a dictionary
    assert isinstance(schema_json, dict)

    # Check basic structure
    assert schema_json["info"]["title"] == "Test API"
    assert schema_json["info"]["version"] == "1.0.0"
    assert (
        schema_json["info"]["description"] == "API for testing OpenAPIIntegrationMixin"
    )
