"""Tests for the Flask-RESTful specific openapi_metadata decorator.

This module tests the openapi_metadata decorator for Flask-RESTful and its functionality.
"""

from __future__ import annotations

import pytest
from flask import Flask
from pydantic import BaseModel, Field

from flask_x_openapi_schema._opt_deps._flask_restful import Api, Resource
from flask_x_openapi_schema.models.base import BaseRespModel
from flask_x_openapi_schema.models.responses import (
    OpenAPIMetaResponse,
    OpenAPIMetaResponseItem,
)
from flask_x_openapi_schema.x.flask_restful import openapi_metadata


# Define test models
class SampleRequestModel(BaseModel):
    """Test request model."""

    name: str = Field(..., description="The name")
    age: int = Field(..., description="The age")
    email: str | None = Field(None, description="The email")

    model_config = {"arbitrary_types_allowed": True}


class SampleResponseModel(BaseRespModel):
    """Test response model."""

    id: str = Field(..., description="The ID")
    name: str = Field(..., description="The name")
    age: int = Field(..., description="The age")
    email: str | None = Field(None, description="The email")


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
                ),
            },
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
                ),
            },
        ),
    )
    def post(self, _x_body: SampleRequestModel):
        """Create new test data."""
        return SampleResponseModel(id="new-id", name=_x_body.name, age=_x_body.age), 201


@pytest.fixture
def app():
    """Create a Flask app for testing."""
    return Flask(__name__)


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


def test_openapi_metadata_with_flask_restful_get(client, api):
    """Test the GET method with Flask-RESTful."""
    # Test GET request
    response = client.get("/tests/123")
    assert response.status_code == 200
    data = response.get_json()
    assert data["id"] == "123"
    assert data["name"] == "Test"
    assert data["age"] == 30


class SampleResourceWithWorkingPost(Resource):
    """Test resource class with a working POST method."""

    @openapi_metadata(
        summary="Create test data",
        description="Create new test data",
        responses=OpenAPIMetaResponse(
            responses={
                "201": OpenAPIMetaResponseItem(
                    model=SampleResponseModel,
                    description="Created successfully",
                ),
            },
        ),
    )
    def post(self, test_id):
        """Create new test data."""
        from flask import request

        data = request.get_json()
        return {"id": test_id, "name": data["name"], "age": data["age"]}, 201


@pytest.fixture
def api_with_working_post(app):
    """Create a Flask-RESTful API with a working POST method."""
    api = Api(app)
    api.add_resource(SampleResourceWithWorkingPost, "/tests2/<string:test_id>")
    return api


def test_openapi_metadata_with_flask_restful_post(client, api_with_working_post):
    """Test the POST method with Flask-RESTful."""
    # Test POST request
    id_ = "new"
    response = client.post(
        f"/tests2/{id_}",
        json={"name": "New Test", "age": 25, "email": "test@example.com"},
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["id"] == id_
    assert data["name"] == "New Test"
    assert data["age"] == 25
