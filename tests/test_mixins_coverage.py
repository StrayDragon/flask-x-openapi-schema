"""
Tests for the mixins module to improve coverage.
"""

import pytest
from unittest.mock import patch

from flask import Blueprint
from flask.views import MethodView

from flask_x_openapi_schema import OpenAPIIntegrationMixin, OpenAPIMethodViewMixin
from flask_x_openapi_schema.x.flask_restful.resources import OpenAPIBlueprintMixin
from flask_x_openapi_schema.i18n.i18n_string import I18nStr, set_current_language


class TestMixinsCoverage:
    """Tests for mixins to improve coverage."""

    def test_openapi_blueprint_mixin_init(self):
        """Test OpenAPIBlueprintMixin initialization."""

        # Create a blueprint with the mixin
        class TestBlueprint(OpenAPIBlueprintMixin, Blueprint):
            pass

        # Initialize the blueprint
        bp = TestBlueprint("test", __name__)

        # Check that the _methodview_openapi_resources attribute was initialized
        assert hasattr(bp, "_methodview_openapi_resources")
        assert bp._methodview_openapi_resources == []

    def test_openapi_blueprint_mixin_init_with_resources(self):
        """Test OpenAPIBlueprintMixin initialization with resources."""

        # Create a blueprint with the mixin
        class TestBlueprint(OpenAPIBlueprintMixin, Blueprint):
            pass

        # Initialize the blueprint with resources
        bp = TestBlueprint("test", __name__)
        bp.resources = [("TestResource", ("/test",), {})]

        # Check that the resources attribute was set
        assert hasattr(bp, "resources")
        assert bp.resources == [("TestResource", ("/test",), {})]

    def test_openapi_blueprint_mixin_generate_schema(self):
        """Test OpenAPIBlueprintMixin.generate_openapi_schema method."""

        # Create a blueprint with the mixin
        class TestBlueprint(OpenAPIBlueprintMixin, Blueprint):
            pass

        # Initialize the blueprint
        bp = TestBlueprint("test", __name__, url_prefix="/api")

        # Create a MethodView class
        class TestView(OpenAPIMethodViewMixin, MethodView):
            def get(self, item_id):
                """Get an item by ID."""
                return {"id": item_id, "name": "Test Item"}

            def put(self, item_id):
                """Update an item."""
                return {"id": item_id, "status": "updated"}

        # Register the view to the blueprint
        TestView.register_to_blueprint(bp, "/items/<int:item_id>")

        # Generate schema with string title and description
        schema_yaml = bp.generate_openapi_schema(
            title="Test API",
            version="1.0.0",
            description="Test API Description",
            output_format="yaml",
        )

        # Check that the schema was generated
        assert isinstance(schema_yaml, str)
        assert "Test API" in schema_yaml
        assert "1.0.0" in schema_yaml
        assert "Test API Description" in schema_yaml

        # Generate schema with I18nString title and description
        title = I18nStr({"en-US": "Test API", "zh-Hans": "测试 API"})
        description = I18nStr(
            {"en-US": "Test API Description", "zh-Hans": "测试 API 描述"}
        )

        # Set language to Chinese
        set_current_language("zh-Hans")

        schema_json = bp.generate_openapi_schema(
            title=title,
            version="1.0.0",
            description=description,
            output_format="json",
            language="zh-Hans",
        )

        # Check that the schema was generated with Chinese strings
        assert isinstance(schema_json, dict)
        assert schema_json["info"]["title"] == "测试 API"
        assert schema_json["info"]["version"] == "1.0.0"
        assert schema_json["info"]["description"] == "测试 API 描述"

        # Reset to English for other tests
        set_current_language("en-US")

    @patch("flask_x_openapi_schema.mixins.HAS_FLASK_RESTFUL", False)
    @patch("flask_x_openapi_schema.mixins.Api")
    def test_openapi_integration_mixin_without_flask_restful(self, mock_api):
        """Test OpenAPIIntegrationMixin when Flask-RESTful is not available."""
        # This test ensures that the mixin works even when Flask-RESTful is not installed
        # by mocking the HAS_FLASK_RESTFUL flag to False

        # Create a class that inherits from OpenAPIIntegrationMixin
        class TestAPI(OpenAPIIntegrationMixin):
            def __init__(self):
                self.blueprint = Blueprint("test", __name__)
                self.resources = []

        # Create an instance
        api = TestAPI()

        # Generate schema
        schema = api.generate_openapi_schema(
            title="Test API",
            version="1.0.0",
            description="Test API Description",
            output_format="json",
        )

        # Check that the schema was generated
        assert isinstance(schema, dict)
        assert schema["info"]["title"] == "Test API"
        assert schema["info"]["version"] == "1.0.0"
        assert schema["info"]["description"] == "Test API Description"

    def test_openapi_integration_mixin_with_yaml_output(self):
        """Test OpenAPIIntegrationMixin with YAML output format."""
        # Skip if Flask-RESTful is not installed
        try:
            from flask_restful import Api  # noqa: F401
        except ImportError:
            pytest.skip("Flask-RESTful not installed")

        # Create a class that inherits from OpenAPIIntegrationMixin
        class TestAPI(OpenAPIIntegrationMixin):
            def __init__(self):
                self.blueprint = Blueprint("test", __name__)
                self.resources = []

        # Create an instance
        api = TestAPI()

        # Generate schema with YAML output
        schema_yaml = api.generate_openapi_schema(
            title="Test API",
            version="1.0.0",
            description="Test API Description",
            output_format="yaml",
        )

        # Check that the schema was generated as YAML
        assert isinstance(schema_yaml, str)
        assert "title: Test API" in schema_yaml
        assert "version: 1.0.0" in schema_yaml
        assert "description: Test API Description" in schema_yaml
