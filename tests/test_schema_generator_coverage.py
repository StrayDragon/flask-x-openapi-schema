"""
Tests for the schema_generator module to improve coverage.
"""

from unittest.mock import MagicMock

from flask_restful import Resource  # type: ignore
from pydantic import BaseModel, Field

from flask_x_openapi_schema.i18n.i18n_model import I18nBaseModel
from flask_x_openapi_schema.i18n.i18n_string import I18nString
from flask_x_openapi_schema.schema_generator import OpenAPISchemaGenerator


class TestSchemaGeneratorCoverage:
    """Tests for schema_generator to improve coverage."""

    def test_process_resource(self):
        """Test the _process_resource method."""
        # Create a schema generator
        generator = OpenAPISchemaGenerator(
            title="Test API", version="1.0.0", description="Test API Description"
        )

        # Create a resource class
        class TestResource(Resource):
            def get(self, item_id):
                """Get an item by ID.

                Returns the item with the specified ID.
                """
                return {"id": item_id, "name": "Test Item"}

            def put(self, item_id):
                """Update an item."""
                return {"id": item_id, "status": "updated"}

            def delete(self, item_id):
                """Delete an item."""
                return {"status": "deleted"}

        # Process the resource
        generator._process_resource(TestResource, ("/items/<int:item_id>",), "/api")

        # Check that the paths were added
        assert "/api/items/{item_id}" in generator.paths

        # Check that the methods were added
        assert "get" in generator.paths["/api/items/{item_id}"]
        assert "put" in generator.paths["/api/items/{item_id}"]
        assert "delete" in generator.paths["/api/items/{item_id}"]

        # Check that the metadata was added
        assert (
            generator.paths["/api/items/{item_id}"]["get"]["summary"]
            == "Get an item by ID."
        )
        assert (
            "Returns the item with the specified ID"
            in generator.paths["/api/items/{item_id}"]["get"]["description"]
        )
        assert (
            generator.paths["/api/items/{item_id}"]["put"]["summary"]
            == "Update an item."
        )
        assert (
            generator.paths["/api/items/{item_id}"]["delete"]["summary"]
            == "Delete an item."
        )

        # Check that parameters were added
        assert "parameters" in generator.paths["/api/items/{item_id}"]["get"]
        assert (
            generator.paths["/api/items/{item_id}"]["get"]["parameters"][0]["name"]
            == "item_id"
        )
        assert (
            generator.paths["/api/items/{item_id}"]["get"]["parameters"][0]["in"]
            == "path"
        )
        assert (
            generator.paths["/api/items/{item_id}"]["get"]["parameters"][0]["schema"][
                "type"
            ]
            == "integer"
        )

    def test_add_request_schema(self):
        """Test the _add_request_schema method."""
        # Create a schema generator
        generator = OpenAPISchemaGenerator(title="Test API", version="1.0.0")

        # Create a Pydantic model
        class TestModel(BaseModel):
            name: str = Field(..., description="The name")
            age: int = Field(..., description="The age")

        # Create a method with a Pydantic model parameter
        def test_method(self, data: TestModel):
            return {"status": "ok"}

        # Create an operation dict
        operation = {}

        # Add request schema
        generator._add_request_schema(test_method, operation)

        # Check that the request body was added
        assert "requestBody" in operation
        assert "content" in operation["requestBody"]
        assert "application/json" in operation["requestBody"]["content"]
        assert "schema" in operation["requestBody"]["content"]["application/json"]
        assert (
            "$ref" in operation["requestBody"]["content"]["application/json"]["schema"]
        )
        assert (
            operation["requestBody"]["content"]["application/json"]["schema"]["$ref"]
            == "#/components/schemas/TestModel"
        )

        # Check that the model was registered
        assert "TestModel" in generator.components["schemas"]
        assert (
            generator.components["schemas"]["TestModel"]["properties"]["name"][
                "description"
            ]
            == "The name"
        )
        assert (
            generator.components["schemas"]["TestModel"]["properties"]["age"][
                "description"
            ]
            == "The age"
        )

    def test_add_response_schema(self):
        """Test the _add_response_schema method."""
        # Create a schema generator
        generator = OpenAPISchemaGenerator(title="Test API", version="1.0.0")

        # Create a Pydantic model
        class ResponseModel(BaseModel):
            status: str = Field(..., description="The status")
            message: str = Field(..., description="The message")

        # Create a method with a return type annotation
        def test_method(self) -> ResponseModel:
            return ResponseModel(status="ok", message="Success")

        # Create an operation dict
        operation = {}

        # Add response schema
        generator._add_response_schema(test_method, operation)

        # Check that the responses were added
        assert "responses" in operation
        assert "200" in operation["responses"]
        assert "description" in operation["responses"]["200"]
        assert "content" in operation["responses"]["200"]
        assert "application/json" in operation["responses"]["200"]["content"]
        assert "schema" in operation["responses"]["200"]["content"]["application/json"]
        assert (
            "$ref"
            in operation["responses"]["200"]["content"]["application/json"]["schema"]
        )
        assert (
            operation["responses"]["200"]["content"]["application/json"]["schema"][
                "$ref"
            ]
            == "#/components/schemas/ResponseModel"
        )

        # Check that the model was registered
        assert "ResponseModel" in generator.components["schemas"]
        assert (
            generator.components["schemas"]["ResponseModel"]["properties"]["status"][
                "description"
            ]
            == "The status"
        )
        assert (
            generator.components["schemas"]["ResponseModel"]["properties"]["message"][
                "description"
            ]
            == "The message"
        )

    def test_add_response_schema_no_return_type(self):
        """Test the _add_response_schema method with no return type."""
        # Create a schema generator
        generator = OpenAPISchemaGenerator(title="Test API", version="1.0.0")

        # Create a method with no return type annotation
        def test_method(self):
            return {"status": "ok"}

        # Create an operation dict
        operation = {}

        # Add response schema
        generator._add_response_schema(test_method, operation)

        # Check that default responses were added
        assert "responses" in operation
        assert "200" in operation["responses"]
        assert "description" in operation["responses"]["200"]
        assert operation["responses"]["200"]["description"] == "Successful response"

    def test_register_model_i18n_base_model(self):
        """Test the _register_model method with I18nBaseModel."""
        # Create a schema generator
        generator = OpenAPISchemaGenerator(
            title="Test API", version="1.0.0", language="zh-Hans"
        )

        # Create an I18nBaseModel
        class TestI18nModel(I18nBaseModel):
            name: str
            description: I18nString
            title: I18nString

        # Register the model
        generator._register_model(TestI18nModel)

        # Check that the model was registered
        assert "TestI18nModel" in generator.components["schemas"]

        # Check that the schema has string fields for I18nString fields
        schema = generator.components["schemas"]["TestI18nModel"]
        assert schema["properties"]["name"]["type"] == "string"
        assert schema["properties"]["description"]["type"] == "string"
        assert schema["properties"]["title"]["type"] == "string"

    def test_process_i18n_dict_nested(self):
        """Test the _process_i18n_dict method with nested structures."""
        # Create a schema generator
        generator = OpenAPISchemaGenerator(
            title="Test API", version="1.0.0", language="zh-Hans"
        )

        # Create a nested dictionary with I18nString values
        data = {
            "title": I18nString({"en-US": "Title", "zh-Hans": "标题"}),
            "metadata": {
                "description": I18nString({"en-US": "Description", "zh-Hans": "描述"}),
                "keywords": ["key1", "key2"],
                "nested": {"label": I18nString({"en-US": "Label", "zh-Hans": "标签"})},
            },
            "items": [
                {
                    "name": I18nString({"en-US": "Item 1", "zh-Hans": "项目 1"}),
                    "tags": ["tag1", "tag2"],
                },
                {
                    "name": I18nString({"en-US": "Item 2", "zh-Hans": "项目 2"}),
                    "tags": ["tag3", "tag4"],
                },
            ],
        }

        # Process the dictionary
        result = generator._process_i18n_dict(data)

        # Check that I18nString values were converted to strings in Chinese
        assert result["title"] == "标题"
        assert result["metadata"]["description"] == "描述"
        assert result["metadata"]["keywords"] == ["key1", "key2"]
        assert result["metadata"]["nested"]["label"] == "标签"
        assert result["items"][0]["name"] == "项目 1"
        assert result["items"][0]["tags"] == ["tag1", "tag2"]
        assert result["items"][1]["name"] == "项目 2"
        assert result["items"][1]["tags"] == ["tag3", "tag4"]

    def test_process_i18n_value(self):
        """Test the _process_i18n_value method."""
        # Create a schema generator
        generator = OpenAPISchemaGenerator(
            title="Test API", version="1.0.0", language="zh-Hans"
        )

        # Test with an I18nString
        value = I18nString({"en-US": "Value", "zh-Hans": "值"})
        result = generator._process_i18n_value(value)
        assert result == "值"

        # Test with a dictionary
        value = {"key": I18nString({"en-US": "Value", "zh-Hans": "值"})}
        result = generator._process_i18n_value(value)
        assert result == {"key": "值"}

        # Test with a list
        value = [
            I18nString({"en-US": "Item 1", "zh-Hans": "项目 1"}),
            I18nString({"en-US": "Item 2", "zh-Hans": "项目 2"}),
        ]
        result = generator._process_i18n_value(value)
        assert result == ["项目 1", "项目 2"]

        # Test with a nested structure
        value = [
            {
                "name": I18nString({"en-US": "Name", "zh-Hans": "名称"}),
                "items": [I18nString({"en-US": "Item", "zh-Hans": "项目"})],
            }
        ]
        result = generator._process_i18n_value(value)
        assert result == [{"name": "名称", "items": ["项目"]}]

        # Test with a non-I18nString value
        value = "Regular string"
        result = generator._process_i18n_value(value)
        assert result == "Regular string"

    def test_add_security_scheme_with_i18n(self):
        """Test add_security_scheme method with I18nString."""
        # Create a schema generator
        generator = OpenAPISchemaGenerator(
            title="Test API",
            version="1.0.0",
            description="Test API Description",
        )

        # Add a security scheme with I18nString description
        description = I18nString(
            {"en-US": "API Key Authentication", "zh-Hans": "API 密钥认证"}
        )
        scheme = {
            "type": "apiKey",
            "description": description,
            "in": "header",
            "name": "X-API-Key",
        }
        generator.add_security_scheme(name="api_key", scheme=scheme)

        # Check that the security scheme was added with the correct description
        assert "api_key" in generator.components["securitySchemes"]
        assert (
            generator.components["securitySchemes"]["api_key"]["description"]
            == "API Key Authentication"
        )

    def test_add_tag_with_i18n(self):
        """Test add_tag method with I18nString."""
        # Create a schema generator
        generator = OpenAPISchemaGenerator(
            title="Test API",
            version="1.0.0",
            description="Test API Description",
        )

        # Add a tag with I18nString name and description
        name = I18nString({"en-US": "Users", "zh-Hans": "用户"})
        description = I18nString({"en-US": "User management", "zh-Hans": "用户管理"})
        generator.add_tag(name=name, description=description)

        # Check that the tag was added with the correct name and description
        assert len(generator.tags) == 1
        assert generator.tags[0]["name"] == "Users"
        assert generator.tags[0]["description"] == "User management"

    def test_scan_blueprint_without_resources(self):
        """Test scan_blueprint method with a blueprint that has no resources."""
        # Create a schema generator
        generator = OpenAPISchemaGenerator(
            title="Test API",
            version="1.0.0",
            description="Test API Description",
        )

        # Create a mock blueprint without resources
        blueprint = MagicMock()
        delattr(blueprint, "resources")

        # Scan the blueprint
        generator.scan_blueprint(blueprint)

        # Check that no paths were added
        assert len(generator.paths) == 0

    def test_process_i18n_dict_with_list(self):
        """Test _process_i18n_dict method with a list containing I18nString values."""
        # Create a schema generator
        generator = OpenAPISchemaGenerator(
            title="Test API",
            version="1.0.0",
            description="Test API Description",
        )

        # Create a dictionary with a list containing I18nString values
        data = {
            "items": [
                I18nString({"en-US": "Item 1", "zh-Hans": "项目 1"}),
                I18nString({"en-US": "Item 2", "zh-Hans": "项目 2"}),
                "Regular string",
            ]
        }

        # Process the dictionary
        result = generator._process_i18n_dict(data)

        # Check that the list was processed correctly
        assert result["items"][0] == "Item 1"
        assert result["items"][1] == "Item 2"
        assert result["items"][2] == "Regular string"
