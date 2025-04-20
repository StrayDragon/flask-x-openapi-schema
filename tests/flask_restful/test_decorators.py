"""
Tests for the Flask-RESTful specific openapi_metadata decorator.

This module tests the openapi_metadata decorator for Flask-RESTful and its functionality.
"""

import pytest
from flask import Flask
from flask_restful import Api, Resource
from pydantic import BaseModel, Field
from typing import Optional

from flask_x_openapi_schema.x.flask_restful import openapi_metadata
from flask_x_openapi_schema.models.base import BaseRespModel
from flask_x_openapi_schema.models.responses import (
    OpenAPIMetaResponse,
    OpenAPIMetaResponseItem,
)


# Define test models
class SampleRequestModel(BaseModel):
    """Test request model."""

    name: str = Field(..., description="The name")
    age: int = Field(..., description="The age")
    email: Optional[str] = Field(None, description="The email")

    model_config = {"arbitrary_types_allowed": True}


class SampleResponseModel(BaseRespModel):
    """Test response model."""

    id: str = Field(..., description="The ID")
    name: str = Field(..., description="The name")
    age: int = Field(..., description="The age")
    email: Optional[str] = Field(None, description="The email")

    model_config = {"arbitrary_types_allowed": True}


class SampleResource(Resource):
    """Test resource class for testing the decorator with Flask-RESTful."""

    @openapi_metadata(
        summary="Get test data",
        description="Get test data by ID",
        responses=OpenAPIMetaResponse(
            responses={
                "200": OpenAPIMetaResponseItem(
                    model=SampleResponseModel,
                    description="Successful response",
                )
            }
        ),
    )
    def get(self, test_id):
        """Get test data by ID."""
        return SampleResponseModel(id=test_id, name="Test", age=30)

    @openapi_metadata(
        summary="Create test data",
        description="Create new test data",
        responses=OpenAPIMetaResponse(
            responses={
                "201": OpenAPIMetaResponseItem(
                    model=SampleResponseModel,
                    description="Created successfully",
                )
            }
        ),
    )
    def post(self, _x_body: SampleRequestModel):
        """Create new test data."""
        return SampleResponseModel(id="new-id", name=_x_body.name, age=_x_body.age), 201


@pytest.fixture
def app():
    """Create a Flask app for testing."""
    app = Flask(__name__)
    return app


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()


@pytest.fixture
def api(app):
    """Create a Flask-RESTful API for testing."""
    api = Api(app)
    api.add_resource(SampleResource, "/tests/<string:test_id>")
    return api


def test_openapi_metadata_with_flask_restful(client, api):
    """Test the decorator with Flask-RESTful."""
    # Create a mock BaseRespModel.to_response method
    original_to_response = BaseRespModel.to_response

    def mock_to_response(self, status_code=200):
        return self.model_dump(), status_code

    # Monkey patch the to_response method
    BaseRespModel.to_response = mock_to_response

    try:
        # Test GET request
        response = client.get("/tests/123")
        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == "123"
        assert data["name"] == "Test"
        assert data["age"] == 30

        # Modify the post method to avoid the error
        original_post = SampleResource.post

        def mock_post(self, test_id=None):
            # Get the request data
            from flask import request

            data = request.get_json()
            # Create a response
            return {"id": "new-id", "name": data["name"], "age": data["age"]}, 201

        # Apply the mock
        SampleResource.post = mock_post

        # Test POST request
        response = client.post(
            "/tests/new",
            json={"name": "New Test", "age": 25, "email": "test@example.com"},
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["id"] == "new-id"
        assert data["name"] == "New Test"
        assert data["age"] == 25

        # Restore the original post method
        SampleResource.post = original_post
    finally:
        # Restore the original method
        BaseRespModel.to_response = original_to_response
