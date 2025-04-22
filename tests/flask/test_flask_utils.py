"""
Tests for Flask utility functions.
"""

import yaml
from unittest.mock import MagicMock, patch

import pytest
from flask import Blueprint, Flask
from pydantic import BaseModel, Field

from flask_x_openapi_schema.core.schema_generator import OpenAPISchemaGenerator
from flask_x_openapi_schema.i18n.i18n_string import I18nStr
from flask_x_openapi_schema.x.flask.utils import (
    generate_openapi_schema,
    register_model_schema,
)
from flask_x_openapi_schema.x.flask.views import MethodViewOpenAPISchemaGenerator


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


def test_generate_openapi_schema_yaml_with_mock(blueprint):
    """Test generate_openapi_schema with YAML output using mock."""
    # Mock the MethodViewOpenAPISchemaGenerator
    mock_generator = MagicMock()
    mock_generator.generate_schema.return_value = {
        "openapi": "3.0.0",
        "info": {
            "title": "Test API",
            "version": "1.0.0",
            "description": "Test API Description",
        },
        "paths": {},
    }

    # Patch the MethodViewOpenAPISchemaGenerator class
    with patch(
        "flask_x_openapi_schema.x.flask.utils.MethodViewOpenAPISchemaGenerator",
        return_value=mock_generator,
    ):
        # Generate schema
        schema = generate_openapi_schema(
            blueprint=blueprint,
            title="Test API",
            version="1.0.0",
            description="Test API Description",
            output_format="yaml",
        )

        # Check that the schema is a string (YAML)
        assert isinstance(schema, str)
        assert "openapi: 3.0.0" in schema
        assert "title: Test API" in schema
        assert "version: 1.0.0" in schema
        assert "description: Test API Description" in schema

        # Check that the generator was called with the correct parameters
        mock_generator.process_methodview_resources.assert_called_once_with(blueprint)
        mock_generator.generate_schema.assert_called_once()


def test_generate_openapi_schema_yaml_with_unicode():
    """Test generate_openapi_schema with YAML output and Unicode characters."""
    # Create a blueprint
    blueprint = Blueprint("test_api", __name__)

    # Mock the MethodViewOpenAPISchemaGenerator
    mock_generator = MagicMock()
    mock_generator.generate_schema.return_value = {
        "openapi": "3.0.0",
        "info": {
            "title": "测试 API",
            "version": "1.0.0",
            "description": "这是一个测试 API",
        },
        "paths": {},
    }

    # Patch the MethodViewOpenAPISchemaGenerator class
    with patch(
        "flask_x_openapi_schema.x.flask.utils.MethodViewOpenAPISchemaGenerator",
        return_value=mock_generator,
    ):
        # Generate schema with Unicode characters
        schema = generate_openapi_schema(
            blueprint=blueprint,
            title="测试 API",
            version="1.0.0",
            description="这是一个测试 API",
            output_format="yaml",
        )

        # Check that the schema is a string (YAML)
        assert isinstance(schema, str)

        # Parse the YAML to verify it's valid
        parsed_yaml = yaml.safe_load(schema)
        assert parsed_yaml["info"]["title"] == "测试 API"
        assert parsed_yaml["info"]["description"] == "这是一个测试 API"

        # Check that Unicode characters are preserved (not escaped as \uXXXX)
        assert "\\u" not in schema
        assert "测试 API" in schema
        assert "这是一个测试 API" in schema


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


def test_generate_openapi_schema_json_with_mock(blueprint):
    """Test generate_openapi_schema with JSON output using mock."""
    # Mock the MethodViewOpenAPISchemaGenerator
    mock_generator = MagicMock()
    mock_generator.generate_schema.return_value = {
        "openapi": "3.0.0",
        "info": {
            "title": "Test API",
            "version": "1.0.0",
            "description": "Test API Description",
        },
        "paths": {},
    }

    # Patch the MethodViewOpenAPISchemaGenerator class
    with patch(
        "flask_x_openapi_schema.x.flask.utils.MethodViewOpenAPISchemaGenerator",
        return_value=mock_generator,
    ):
        # Generate schema
        schema = generate_openapi_schema(
            blueprint=blueprint,
            title="Test API",
            version="1.0.0",
            description="Test API Description",
            output_format="json",
        )

        # Check that the schema is a dictionary (JSON)
        assert isinstance(schema, dict)
        assert schema["openapi"] == "3.0.0"
        assert schema["info"]["title"] == "Test API"
        assert schema["info"]["version"] == "1.0.0"
        assert schema["info"]["description"] == "Test API Description"

        # Check that the generator was called with the correct parameters
        mock_generator.process_methodview_resources.assert_called_once_with(blueprint)
        mock_generator.generate_schema.assert_called_once()


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


def test_generate_openapi_schema_with_i18n_and_mock(blueprint):
    """Test generate_openapi_schema with internationalized strings using mock."""
    # Mock the MethodViewOpenAPISchemaGenerator
    mock_generator = MagicMock()
    mock_generator.generate_schema.return_value = {
        "openapi": "3.0.0",
        "info": {
            "title": "测试 API",
            "version": "1.0.0",
            "description": "测试 API 描述",
        },
        "paths": {},
    }

    # Create I18nStr instances
    title = I18nStr({"en": "Test API", "zh": "测试 API"})
    description = I18nStr({"en": "Test API Description", "zh": "测试 API 描述"})

    # Patch the MethodViewOpenAPISchemaGenerator class
    with patch(
        "flask_x_openapi_schema.x.flask.utils.MethodViewOpenAPISchemaGenerator",
        return_value=mock_generator,
    ):
        # Generate schema with Chinese language
        schema = generate_openapi_schema(
            blueprint=blueprint,
            title=title,
            version="1.0.0",
            description=description,
            output_format="json",
            language="zh",
        )

        # Check that the schema is a dictionary (JSON)
        assert isinstance(schema, dict)
        assert schema["openapi"] == "3.0.0"
        assert schema["info"]["title"] == "测试 API"
        assert schema["info"]["version"] == "1.0.0"
        assert schema["info"]["description"] == "测试 API 描述"

        # Check that the generator was called with the correct parameters
        mock_generator.process_methodview_resources.assert_called_once_with(blueprint)
        mock_generator.generate_schema.assert_called_once()


def test_generate_openapi_schema_with_default_language(blueprint):
    """Test generate_openapi_schema with default language."""
    # Mock the MethodViewOpenAPISchemaGenerator
    mock_generator = MagicMock()
    mock_generator.generate_schema.return_value = {
        "openapi": "3.0.0",
        "info": {
            "title": "API de test",
            "version": "1.0.0",
            "description": "Description de l'API de test",
        },
        "paths": {},
    }

    # Patch the MethodViewOpenAPISchemaGenerator class
    with patch(
        "flask_x_openapi_schema.x.flask.utils.MethodViewOpenAPISchemaGenerator",
        return_value=mock_generator,
    ):
        # Generate schema without specifying a language (should use default language)
        schema = generate_openapi_schema(
            blueprint=blueprint,
            title="Test API",
            version="1.0.0",
            description="Test API Description",
            output_format="json",
        )

        # Check that the schema is a dictionary (JSON)
        assert isinstance(schema, dict)
        assert schema["openapi"] == "3.0.0"
        assert schema["info"]["title"] == "API de test"
        assert schema["info"]["version"] == "1.0.0"
        assert schema["info"]["description"] == "Description de l'API de test"

        # Check that the generator was called with the correct parameters
        mock_generator.process_methodview_resources.assert_called_once_with(blueprint)
        mock_generator.generate_schema.assert_called_once()


@pytest.fixture
def app():
    """Create a Flask app for testing."""
    app = Flask(__name__)
    return app


@pytest.fixture
def blueprint():
    """Create a Flask blueprint for testing."""
    bp = Blueprint("test_api", __name__)
    return bp


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


def test_register_model_schema_with_mock():
    """Test register_model_schema function with mock."""
    # Create a mock schema generator
    mock_generator = MagicMock(spec=OpenAPISchemaGenerator)

    # Register a model
    register_model_schema(mock_generator, SampleModel)

    # Check that the model was registered
    mock_generator._register_model.assert_called_once_with(SampleModel)


def test_register_model_schema_with_nested_models():
    """Test register_model_schema with nested models."""

    # Create nested models
    class NestedModel(BaseModel):
        """Nested model for testing."""

        value: str = Field(..., description="A value")

    class ParentModel(BaseModel):
        """Parent model with nested model."""

        name: str = Field(..., description="The name")
        nested: NestedModel = Field(..., description="Nested model")

    # Create a mock schema generator
    mock_generator = MagicMock(spec=OpenAPISchemaGenerator)

    # Register the parent model
    register_model_schema(mock_generator, ParentModel)

    # Check that the model was registered
    mock_generator._register_model.assert_called_once_with(ParentModel)
