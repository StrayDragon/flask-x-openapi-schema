"""
Tests for the mixins module to improve coverage.
"""

from unittest.mock import MagicMock
import yaml

from flask_x_openapi_schema.x.flask_restful.resources import (
    OpenAPIIntegrationMixin,
    OpenAPIBlueprintMixin,
)


class TestMixinsCoverage:
    """Tests for mixins to improve coverage."""

    def test_openapi_integration_mixin(self):
        """Test OpenAPIIntegrationMixin."""
        # Create a mock blueprint
        blueprint = MagicMock()
        blueprint.url_prefix = "/api"

        # Create a mock resource class
        class TestResource:
            def get(self):
                """Test method."""
                return {"message": "Hello, world!"}

        resource = TestResource

        # Create an instance of the mixin
        mixin = OpenAPIIntegrationMixin()
        mixin.blueprint = blueprint
        mixin.resources = [(resource, ("/test",), {})]

        # Test generate_openapi_schema with default parameters
        schema_yaml = mixin.generate_openapi_schema(
            title="Test API", version="1.0.0", description="Test API Description"
        )

        # Check that the result is a string (YAML)
        assert isinstance(schema_yaml, str)

        # Parse the YAML to check its structure
        schema = yaml.safe_load(schema_yaml)
        assert schema["info"]["title"] == "Test API"
        assert schema["info"]["version"] == "1.0.0"
        assert schema["info"]["description"] == "Test API Description"

        # Test generate_openapi_schema with JSON output
        schema_json = mixin.generate_openapi_schema(
            title="Test API",
            version="1.0.0",
            description="Test API Description",
            output_format="json",
        )

        # Check that the result is a dictionary
        assert isinstance(schema_json, dict)
        assert schema_json["info"]["title"] == "Test API"
        assert schema_json["info"]["version"] == "1.0.0"
        assert schema_json["info"]["description"] == "Test API Description"

    def test_openapi_blueprint_mixin(self):
        """Test OpenAPIBlueprintMixin."""
        # Create an instance of the mixin
        mixin = OpenAPIBlueprintMixin()
        mixin._methodview_openapi_resources = []

        # Test generate_openapi_schema with default parameters
        schema_yaml = mixin.generate_openapi_schema(
            title="Test API", version="1.0.0", description="Test API Description"
        )

        # Check that the result is a string (YAML)
        assert isinstance(schema_yaml, str)

        # Parse the YAML to check its structure
        schema = yaml.safe_load(schema_yaml)
        assert schema["info"]["title"] == "Test API"
        assert schema["info"]["version"] == "1.0.0"
        assert schema["info"]["description"] == "Test API Description"

        # Test generate_openapi_schema with JSON output
        schema_json = mixin.generate_openapi_schema(
            title="Test API",
            version="1.0.0",
            description="Test API Description",
            output_format="json",
        )

        # Check that the result is a dictionary
        assert isinstance(schema_json, dict)
        assert schema_json["info"]["title"] == "Test API"
        assert schema_json["info"]["version"] == "1.0.0"
        assert schema_json["info"]["description"] == "Test API Description"
