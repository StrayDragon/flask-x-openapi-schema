"""
Tests for Flask utility functions.
"""

from flask import Blueprint
from pydantic import BaseModel, Field

from flask_x_openapi_schema.x.flask.utils import (
    generate_openapi_schema,
    register_model_schema,
)
from flask_x_openapi_schema.x.flask.views import MethodViewOpenAPISchemaGenerator
from flask_x_openapi_schema.i18n.i18n_string import I18nStr


# Renamed to avoid pytest collection warning
class SampleModel(BaseModel):
    """Test model for schema generation."""

    name: str = Field(..., description="The name")
    age: int = Field(..., description="The age")


def test_generate_openapi_schema_yaml():
    """Test generating an OpenAPI schema in YAML format."""
    # Create a blueprint
    bp = Blueprint("test", __name__, url_prefix="/api")

    # Generate the schema
    schema = generate_openapi_schema(
        blueprint=bp,
        title="Test API",
        version="1.0.0",
        description="Test API Description",
        output_format="yaml",
    )

    # Check that the schema is a string (YAML)
    assert isinstance(schema, str)
    assert "title: Test API" in schema
    assert "version: 1.0.0" in schema
    assert "description: Test API Description" in schema


def test_generate_openapi_schema_json():
    """Test generating an OpenAPI schema in JSON format."""
    # Create a blueprint
    bp = Blueprint("test", __name__, url_prefix="/api")

    # Generate the schema
    schema = generate_openapi_schema(
        blueprint=bp,
        title="Test API",
        version="1.0.0",
        description="Test API Description",
        output_format="json",
    )

    # Check that the schema is a dictionary (JSON)
    assert isinstance(schema, dict)
    assert schema["info"]["title"] == "Test API"
    assert schema["info"]["version"] == "1.0.0"
    assert schema["info"]["description"] == "Test API Description"


def test_generate_openapi_schema_with_i18n():
    """Test generating an OpenAPI schema with internationalized strings."""
    # Create a blueprint
    bp = Blueprint("test", __name__, url_prefix="/api")

    # Create internationalized strings
    title = I18nStr({"en-US": "Test API", "zh-CN": "测试 API"})
    description = I18nStr({"en-US": "Test API Description", "zh-CN": "测试 API 描述"})

    # Generate the schema with English language
    schema = generate_openapi_schema(
        blueprint=bp,
        title=title,
        version="1.0.0",
        description=description,
        output_format="json",
        language="en-US",
    )

    # Check that the schema uses English strings
    assert schema["info"]["title"] == "Test API"
    assert schema["info"]["description"] == "Test API Description"

    # Generate the schema with Chinese language
    schema = generate_openapi_schema(
        blueprint=bp,
        title=title,
        version="1.0.0",
        description=description,
        output_format="json",
        language="zh-CN",
    )

    # Check that the schema uses Chinese strings
    assert schema["info"]["title"] == "测试 API"
    assert schema["info"]["description"] == "测试 API 描述"


def test_register_model_schema():
    """Test registering a model schema with a generator."""
    # Create a schema generator
    generator = MethodViewOpenAPISchemaGenerator(
        title="Test API", version="1.0.0", description="Test API Description"
    )

    # Register a model
    register_model_schema(generator, SampleModel)

    # Generate the schema
    schema = generator.generate_schema()

    # Check that the model was registered
    assert "SampleModel" in schema["components"]["schemas"]
    assert (
        schema["components"]["schemas"]["SampleModel"]["properties"]["name"][
            "description"
        ]
        == "The name"
    )
    assert (
        schema["components"]["schemas"]["SampleModel"]["properties"]["age"][
            "description"
        ]
        == "The age"
    )
