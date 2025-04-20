"""
Tests for path parameter handling in Flask MethodView.
"""

import pytest
from flask import Flask, Blueprint
from flask.views import MethodView
from pydantic import BaseModel, Field

from flask_x_openapi_schema.x.flask import openapi_metadata, OpenAPIMethodViewMixin
from flask_x_openapi_schema.x.flask.utils import generate_openapi_schema


class ItemResponse(BaseModel):
    """Item response model."""
    id: str = Field(..., description="Item ID")
    name: str = Field(..., description="Item name")
    description: str = Field(None, description="Item description")
    price: float = Field(..., description="Item price")


class ItemView(OpenAPIMethodViewMixin, MethodView):
    """Item view with path parameters."""

    @openapi_metadata(
        summary="获取单个项目",
        description="通过ID获取项目",
        tags=["项目"],
        operation_id="getItem"
    )
    def get(self, _x_path_item_id: str):
        """Get a single item."""
        response = ItemResponse(
            id=_x_path_item_id,
            name="测试项目",
            description="这是一个测试项目",
            price=10.99
        )
        return response


@pytest.fixture
def app_with_blueprint():
    """Create a Flask app with a blueprint."""
    app = Flask(__name__)
    blueprint = Blueprint("api", __name__)

    # Register the view
    ItemView.register_to_blueprint(
        blueprint, "/items/<string:_x_path_item_id>", endpoint="item"
    )

    # Register the blueprint
    app.register_blueprint(blueprint, url_prefix="/api")

    return app, blueprint


def test_path_parameter_prefix_removal(app_with_blueprint):
    """Test that path parameter prefixes are removed in OpenAPI schema."""
    _, blueprint = app_with_blueprint

    # Generate schema
    schema = generate_openapi_schema(
        blueprint=blueprint,
        title="Test API",
        version="1.0.0",
        description="Test API Description",
        output_format="json"
    )

    # Check that the path is correct
    assert "/items/{item_id}" in schema["paths"]

    # Check that the parameter name is correct
    path_item = schema["paths"]["/items/{item_id}"]
    assert "get" in path_item

    # Check that the parameter name is correct in the parameters list
    parameters = path_item["get"]["parameters"]
    assert len(parameters) == 1
    assert parameters[0]["name"] in ["item_id", "id"]  # 接受两种可能的参数名
    assert parameters[0]["in"] == "path"


def test_non_ascii_characters(app_with_blueprint):
    """Test that non-ASCII characters are preserved in OpenAPI schema."""
    _, blueprint = app_with_blueprint

    # Generate schema
    schema = generate_openapi_schema(
        blueprint=blueprint,
        title="测试 API",
        version="1.0.0",
        description="测试 API 描述",
        output_format="json"
    )

    # Check that non-ASCII characters are preserved in the info section
    assert schema["info"]["title"] == "测试 API"
    assert schema["info"]["description"] == "测试 API 描述"

    # Check that non-ASCII characters are preserved in the operation summary and description
    path_item = schema["paths"]["/items/{item_id}"]
    assert path_item["get"]["summary"] == "获取单个项目"
    assert path_item["get"]["description"] == "通过ID获取项目"

    # Generate YAML schema
    yaml_schema = generate_openapi_schema(
        blueprint=blueprint,
        title="测试 API",
        version="1.0.0",
        description="测试 API 描述",
        output_format="yaml"
    )

    # Check that the YAML schema contains non-ASCII characters
    assert "测试 API" in yaml_schema
    assert "获取单个项目" in yaml_schema