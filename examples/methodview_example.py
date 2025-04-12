"""
Example of how to use Flask.MethodView with the OpenAPI integration.

This example demonstrates how to:
1. Define a Flask.MethodView class with OpenAPI metadata
2. Use Pydantic models for request and response validation
3. Generate OpenAPI documentation for MethodView endpoints
"""

from flask import Flask, Blueprint
from flask.views import MethodView
from pydantic import BaseModel, Field
from typing import List, Optional

from flask_x_openapi_schema import (
    BaseRespModel,
    OpenAPIBlueprintMixin,
    OpenAPIMethodViewMixin,
    openapi_metadata,
    responses_schema,
    success_response,
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
        responses=responses_schema(
            success_responses={
                "200": success_response(
                    model=ItemResponse,
                    description="Item retrieved successfully",
                ),
            },
            errors={
                "404": "Item not found",
            },
        ),
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
        responses=responses_schema(
            success_responses={
                "201": success_response(
                    model=ItemResponse,
                    description="Item created successfully",
                ),
            },
            errors={
                "400": "Invalid request",
            },
        ),
    )
    def post(self, item_id: str, x_request_body: ItemRequest):
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


def create_app():
    """Create and configure a Flask app for the example."""
    app = Flask(__name__)

    # Create a blueprint with OpenAPI support
    api_bp = OpenAPIBlueprint("api", __name__, url_prefix="/api")

    # Register the MethodView
    ItemView.register_to_blueprint(api_bp, "/items/<string:item_id>", endpoint="item")

    # Register the blueprint with the app
    app.register_blueprint(api_bp)

    # Add a route to get the OpenAPI schema
    @app.route("/openapi.yaml")
    def get_openapi_schema():
        schema = api_bp.generate_openapi_schema(
            title="Items API",
            version="1.0.0",
            description="API for managing items",
        )
        return schema

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
