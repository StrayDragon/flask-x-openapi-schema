"""Tests for Flask utility functions."""

import pytest
import yaml
from flask import Blueprint, Flask, jsonify
from flask.views import MethodView
from pydantic import BaseModel, Field

from flask_x_openapi_schema.i18n.i18n_string import I18nStr, set_current_language
from flask_x_openapi_schema.models.responses import OpenAPIMetaResponse, OpenAPIMetaResponseItem
from flask_x_openapi_schema.x.flask.decorators import openapi_metadata
from flask_x_openapi_schema.x.flask.utils import (
    generate_openapi_schema,
    register_model_schema,
)
from flask_x_openapi_schema.x.flask.views import MethodViewOpenAPISchemaGenerator, OpenAPIMethodViewMixin


class SampleModel(BaseModel):
    """Test model for schema generation."""

    name: str = Field(..., description="The name")
    age: int = Field(..., description="The age")


class SampleResponse(BaseModel):
    """Sample response model."""

    id: str = Field(..., description="The ID")
    message: str = Field(..., description="The message")


class SampleItemModel(BaseModel):
    """Sample item model for testing."""

    item_id: str = Field(..., description="The item ID")
    name: str = Field(..., description="The item name")
    price: float = Field(..., description="The item price")


class SampleItemView(OpenAPIMethodViewMixin, MethodView):
    """Sample MethodView for testing."""

    @openapi_metadata(
        summary="Get an item",
        description="Get an item by ID",
        responses=OpenAPIMetaResponse(
            responses={
                "200": OpenAPIMetaResponseItem(
                    model=SampleResponse,
                    description="Successful response",
                ),
            },
        ),
    )
    def get(self, item_id: str):
        """Get an item by ID."""
        return jsonify({"id": item_id, "message": "Item found"})

    @openapi_metadata(
        summary="Create an item",
        description="Create a new item",
        responses=OpenAPIMetaResponse(
            responses={
                "201": OpenAPIMetaResponseItem(
                    model=SampleResponse,
                    description="Item created",
                ),
            },
        ),
    )
    def post(self, _x_body: SampleItemModel = None):
        """Create a new item."""
        # Process request data (not actually used in test)
        return jsonify({"id": "new-id", "message": "Item created"}), 201


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


def test_generate_openapi_schema_yaml_with_real_view(blueprint):
    """Test generate_openapi_schema with YAML output using a real MethodView."""
    # Register the view to the blueprint
    SampleItemView.register_to_blueprint(blueprint, "/items/<item_id>", "items")

    # Create a schema generator directly to register models
    generator = MethodViewOpenAPISchemaGenerator(
        title="Test API",
        version="1.0.0",
        description="Test API Description",
    )

    # Manually register models
    register_model_schema(generator, SampleResponse)
    register_model_schema(generator, SampleItemModel)

    # Process MethodView resources
    generator.process_methodview_resources(blueprint=blueprint)

    # Generate schema
    schema_dict = generator.generate_schema()

    # Convert to YAML
    schema = yaml.dump(schema_dict, sort_keys=False, default_flow_style=False, allow_unicode=True)

    # Check that the schema is a string (YAML)
    assert isinstance(schema, str)
    assert "openapi: 3.0.3" in schema
    assert "title: Test API" in schema
    assert "version: 1.0.0" in schema
    assert "description: Test API Description" in schema

    # Parse the YAML to verify it's valid
    parsed_yaml = yaml.safe_load(schema)

    # Check that the paths were processed correctly
    assert "/items/{item_id}" in parsed_yaml["paths"]
    assert "get" in parsed_yaml["paths"]["/items/{item_id}"]
    assert "post" in parsed_yaml["paths"]["/items/{item_id}"]

    # Check that the models were registered
    assert "SampleResponse" in parsed_yaml["components"]["schemas"]
    assert "SampleItemModel" in parsed_yaml["components"]["schemas"]

    # Check specific path details
    get_operation = parsed_yaml["paths"]["/items/{item_id}"]["get"]
    assert get_operation["summary"] == "Get an item"
    assert get_operation["description"] == "Get an item by ID"

    # Check response schema
    assert "200" in get_operation["responses"]
    assert get_operation["responses"]["200"]["description"] == "Successful response"


def test_generate_openapi_schema_yaml_with_unicode():
    """Test generate_openapi_schema with YAML output and Unicode characters."""
    # Create a blueprint
    blueprint = Blueprint("test_api", __name__)

    # Create a MethodView with Unicode in docstrings
    class ChineseItemView(OpenAPIMethodViewMixin, MethodView):
        """中文 API 视图."""

        @openapi_metadata(
            summary="获取一个项目",
            description="通过 ID 获取项目",
            responses=OpenAPIMetaResponse(
                responses={
                    "200": OpenAPIMetaResponseItem(
                        model=SampleResponse,
                        description="成功响应",
                    ),
                },
            ),
        )
        def get(self, item_id: str):
            """获取一个项目."""
            return jsonify({"id": item_id, "message": "项目找到了"})

    # Register the view to the blueprint
    ChineseItemView.register_to_blueprint(blueprint, "/items/<item_id>", "chinese_items")

    # Create a schema generator directly to register models
    generator = MethodViewOpenAPISchemaGenerator(
        title="测试 API",
        version="1.0.0",
        description="这是一个测试 API",
    )

    # Manually register models
    register_model_schema(generator, SampleResponse)

    # Process MethodView resources
    generator.process_methodview_resources(blueprint=blueprint)

    # Generate schema
    schema_dict = generator.generate_schema()

    # Convert to YAML
    schema = yaml.dump(schema_dict, sort_keys=False, default_flow_style=False, allow_unicode=True)

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

    # Check that the path operation contains Unicode
    path_operation = parsed_yaml["paths"]["/items/{item_id}"]["get"]
    assert path_operation["summary"] == "获取一个项目"
    assert path_operation["description"] == "通过 ID 获取项目"
    assert path_operation["responses"]["200"]["description"] == "成功响应"


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


def test_generate_openapi_schema_json_with_real_view(blueprint):
    """Test generate_openapi_schema with JSON output using a real MethodView."""
    # Register the view to the blueprint
    SampleItemView.register_to_blueprint(blueprint, "/items/<item_id>", "items")

    # Create a schema generator directly to register models
    generator = MethodViewOpenAPISchemaGenerator(
        title="Test API",
        version="1.0.0",
        description="Test API Description",
    )

    # Manually register models
    register_model_schema(generator, SampleResponse)
    register_model_schema(generator, SampleItemModel)

    # Process MethodView resources
    generator.process_methodview_resources(blueprint=blueprint)

    # Generate schema
    schema = generator.generate_schema()

    # Check that the schema is a dictionary (JSON)
    assert isinstance(schema, dict)
    assert schema["openapi"] == "3.0.3"
    assert schema["info"]["title"] == "Test API"
    assert schema["info"]["version"] == "1.0.0"
    assert schema["info"]["description"] == "Test API Description"

    # Check that the paths were processed correctly
    assert "/items/{item_id}" in schema["paths"]
    assert "get" in schema["paths"]["/items/{item_id}"]
    assert "post" in schema["paths"]["/items/{item_id}"]

    # Check that the models were registered
    assert "SampleResponse" in schema["components"]["schemas"]
    assert "SampleItemModel" in schema["components"]["schemas"]

    # Check specific path details
    get_operation = schema["paths"]["/items/{item_id}"]["get"]
    assert get_operation["summary"] == "Get an item"
    assert get_operation["description"] == "Get an item by ID"

    # Check response schema
    assert "200" in get_operation["responses"]
    assert get_operation["responses"]["200"]["description"] == "Successful response"
    assert (
        get_operation["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/SampleResponse"
    )


def test_generate_openapi_schema_with_i18n():
    """Test generating an OpenAPI schema with internationalized strings."""

    # Create I18nStr instances for title and description
    title = I18nStr({"en": "Test API", "zh": "测试 API"})
    description = I18nStr({"en": "Test API Description", "zh": "测试 API 描述"})

    # Create a schema generator for English
    en_generator = MethodViewOpenAPISchemaGenerator(
        title=title,
        version="1.0.0",
        description=description,
        language="en",
    )

    # Generate the schema
    en_schema = en_generator.generate_schema()

    # Check that the schema uses English strings
    assert en_schema["info"]["title"] == "Test API"
    assert en_schema["info"]["description"] == "Test API Description"

    # Create a schema generator for Chinese
    zh_generator = MethodViewOpenAPISchemaGenerator(
        title=title,
        version="1.0.0",
        description=description,
        language="zh",
    )

    # Generate the schema
    zh_schema = zh_generator.generate_schema()

    # Check that the schema uses Chinese strings
    assert zh_schema["info"]["title"] == "测试 API"
    assert zh_schema["info"]["description"] == "测试 API 描述"


def test_generate_openapi_schema_with_default_language():
    """Test generate_openapi_schema with default language."""
    # Create I18nStr instances for title and description
    title = I18nStr({"en": "Test API", "fr": "API de test"})
    description = I18nStr({"en": "Test API Description", "fr": "Description de l'API de test"})

    # Set the current language to French
    set_current_language("fr")

    try:
        # Create a schema generator without specifying a language (should use default language - French)
        generator = MethodViewOpenAPISchemaGenerator(
            title=title,
            version="1.0.0",
            description=description,
        )

        # Generate schema
        schema = generator.generate_schema()

        # Check that the schema uses French strings (the default language)
        assert isinstance(schema, dict)
        assert schema["info"]["title"] == "API de test"
        assert schema["info"]["version"] == "1.0.0"
        assert schema["info"]["description"] == "Description de l'API de test"
    finally:
        # Reset the current language to English
        set_current_language("en")


@pytest.fixture
def app():
    """Create a Flask app for testing."""
    return Flask(__name__)


@pytest.fixture
def blueprint():
    """Create a Flask blueprint for testing."""
    return Blueprint("test_api", __name__)


def test_register_model_schema():
    """Test registering a model schema with a generator."""
    # Create a schema generator
    generator = MethodViewOpenAPISchemaGenerator(title="Test API", version="1.0.0", description="Test API Description")

    # Register a model
    register_model_schema(generator, SampleModel)

    # Generate the schema
    schema = generator.generate_schema()

    # Check that the model was registered
    assert "SampleModel" in schema["components"]["schemas"]
    assert schema["components"]["schemas"]["SampleModel"]["properties"]["name"]["description"] == "The name"
    assert schema["components"]["schemas"]["SampleModel"]["properties"]["age"]["description"] == "The age"


def test_register_model_schema_with_real_generator():
    """Test register_model_schema function with a real generator."""
    # Create a real schema generator
    generator = MethodViewOpenAPISchemaGenerator(
        title="Test API",
        version="1.0.0",
        description="Test API Description",
    )

    # Register a model
    register_model_schema(generator, SampleModel)

    # Generate the schema
    schema = generator.generate_schema()

    # Check that the model was registered
    assert "SampleModel" in schema["components"]["schemas"]
    assert schema["components"]["schemas"]["SampleModel"]["properties"]["name"]["description"] == "The name"
    assert schema["components"]["schemas"]["SampleModel"]["properties"]["age"]["description"] == "The age"


def test_register_model_schema_with_nested_models_real():
    """Test register_model_schema with nested models using a real generator."""

    # Create nested models
    class NestedModel(BaseModel):
        """Nested model for testing."""

        value: str = Field(..., description="A value")

    class ParentModel(BaseModel):
        """Parent model with nested model."""

        name: str = Field(..., description="The name")
        nested: NestedModel = Field(..., description="Nested model")

    # Create a real schema generator
    generator = MethodViewOpenAPISchemaGenerator(
        title="Test API",
        version="1.0.0",
        description="Test API Description",
    )

    # Register the parent model
    register_model_schema(generator, ParentModel)

    # Generate the schema
    schema = generator.generate_schema()

    # Check that both models were registered
    assert "ParentModel" in schema["components"]["schemas"]
    assert "NestedModel" in schema["components"]["schemas"]

    # Check parent model properties
    parent_schema = schema["components"]["schemas"]["ParentModel"]
    assert parent_schema["properties"]["name"]["description"] == "The name"
    assert parent_schema["properties"]["nested"]["description"] == "Nested model"
    assert parent_schema["properties"]["nested"]["$ref"] == "#/components/schemas/NestedModel"

    # Check nested model properties
    nested_schema = schema["components"]["schemas"]["NestedModel"]
    assert nested_schema["properties"]["value"]["description"] == "A value"
