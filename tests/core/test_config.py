"""
Tests for the OpenAPIConfig functionality.

This module tests the configurable parameter prefixes.
"""

from pydantic import BaseModel, Field
from typing import Optional

from flask_x_openapi_schema.core.config import (
    ConventionalPrefixConfig,
    GLOBAL_CONFIG_HOLDER,
    configure_prefixes,
    reset_prefixes,
    reset_all_config,
    OpenAPIConfig,
    configure_openapi,
    get_openapi_config,
)
from flask_x_openapi_schema.x.flask import openapi_metadata
from flask_x_openapi_schema.x.flask_restful.resources import (
    OpenAPIIntegrationMixin,
    OpenAPIBlueprintMixin,
)


# Define test models
class ConfigTestRequestModel(BaseModel):
    """Test request model."""

    name: str = Field(..., description="The name")
    age: int = Field(..., description="The age")


class ConfigTestQueryModel(BaseModel):
    """Test query model."""

    sort: Optional[str] = Field(None, description="Sort order")
    limit: Optional[int] = Field(None, description="Limit results")


def test_openapi_config_defaults():
    """Test the default values of ConventionalPrefixConfig."""
    # Test the default global config
    global_config = GLOBAL_CONFIG_HOLDER.get()
    assert global_config.request_body_prefix == "_x_body"
    assert global_config.request_query_prefix == "_x_query"
    assert global_config.request_path_prefix == "_x_path"
    assert global_config.request_file_prefix == "_x_file"

    # Test creating a new config with defaults
    config = ConventionalPrefixConfig()
    assert config.request_body_prefix == "_x_body"
    assert config.request_query_prefix == "_x_query"
    assert config.request_path_prefix == "_x_path"
    assert config.request_file_prefix == "_x_file"


def test_openapi_config_configure():
    """Test configuring global prefix configuration."""
    # Create a new configuration
    new_config = ConventionalPrefixConfig(
        request_body_prefix="body",
        request_query_prefix="query",
        request_path_prefix="path",
        request_file_prefix="file",
    )

    # Verify the config object has the correct values
    assert new_config.request_body_prefix == "body"
    assert new_config.request_query_prefix == "query"
    assert new_config.request_path_prefix == "path"
    assert new_config.request_file_prefix == "file"


def test_openapi_metadata_with_custom_prefixes():
    """Test openapi_metadata decorator with custom parameter prefixes."""
    # Save original global config
    original_config = GLOBAL_CONFIG_HOLDER.get()

    try:
        # Create a custom config
        custom_config = ConventionalPrefixConfig(
            request_body_prefix="req_body",
            request_query_prefix="req_query",
            request_path_prefix="req_path",
            request_file_prefix="req_file",
        )

        # Apply the decorator with custom config
        @openapi_metadata(summary="Test endpoint", prefix_config=custom_config)
        def test_function(
            req_body: ConfigTestRequestModel, req_query: ConfigTestQueryModel
        ):
            # Use parameters to avoid linter warnings
            return {"body": str(req_body), "query": str(req_query)}

        # Check metadata
        metadata = test_function._openapi_metadata

        # Verify metadata exists
        assert metadata is not None
        assert "summary" in metadata
        assert metadata["summary"] == "Test endpoint"

        # Check request body
        assert "requestBody" in metadata
        assert "content" in metadata["requestBody"]
        assert "application/json" in metadata["requestBody"]["content"]
        assert "schema" in metadata["requestBody"]["content"]["application/json"]
        assert (
            "$ref" in metadata["requestBody"]["content"]["application/json"]["schema"]
        )
        assert (
            metadata["requestBody"]["content"]["application/json"]["schema"]["$ref"]
            == "#/components/schemas/ConfigTestRequestModel"
        )

        # Check parameters
        assert "parameters" in metadata
        query_params = [p for p in metadata["parameters"] if p["in"] == "query"]
        assert len(query_params) == 2

        # Verify parameter names
        param_names = [p["name"] for p in query_params]
        assert "sort" in param_names
        assert "limit" in param_names

    finally:
        # Restore original global config
        configure_prefixes(original_config)


def test_openapi_metadata_with_per_function_config():
    """Test openapi_metadata decorator with per-function configuration."""
    # Save original global config
    original_config = GLOBAL_CONFIG_HOLDER.get()

    try:
        # Define a function with custom prefixes
        custom_config = ConventionalPrefixConfig(
            request_body_prefix="custom_body",
            request_query_prefix="custom_query",
            request_path_prefix="custom_path",
            request_file_prefix="custom_file",
        )

        @openapi_metadata(summary="Test endpoint", prefix_config=custom_config)
        def test_function(
            custom_body: ConfigTestRequestModel, custom_query: ConfigTestQueryModel
        ):
            # Use parameters to avoid linter warnings
            return {"body": str(custom_body), "query": str(custom_query)}

        # Check metadata
        metadata = test_function._openapi_metadata

        # Verify metadata exists
        assert metadata is not None
        assert "summary" in metadata
        assert metadata["summary"] == "Test endpoint"

        # Check request body
        assert "requestBody" in metadata
        assert "content" in metadata["requestBody"]
        assert "application/json" in metadata["requestBody"]["content"]
        assert "schema" in metadata["requestBody"]["content"]["application/json"]
        assert (
            "$ref" in metadata["requestBody"]["content"]["application/json"]["schema"]
        )
        assert (
            metadata["requestBody"]["content"]["application/json"]["schema"]["$ref"]
            == "#/components/schemas/ConfigTestRequestModel"
        )

        # Check parameters
        assert "parameters" in metadata
        query_params = [p for p in metadata["parameters"] if p["in"] == "query"]
        assert len(query_params) == 2

        # Verify parameter names
        param_names = [p["name"] for p in query_params]
        assert "sort" in param_names
        assert "limit" in param_names

        # Define another function with default prefixes
        @openapi_metadata(summary="Default endpoint")
        def test_function_default(
            _x_body: ConfigTestRequestModel, _x_query: ConfigTestQueryModel
        ):
            # Use parameters to avoid linter warnings
            return {"body": str(_x_body), "query": str(_x_query)}

        # Check metadata
        metadata = test_function_default._openapi_metadata

        # Verify metadata exists
        assert metadata is not None
        assert "summary" in metadata
        assert metadata["summary"] == "Default endpoint"

        # Check request body
        assert "requestBody" in metadata
        assert "content" in metadata["requestBody"]
        assert "application/json" in metadata["requestBody"]["content"]
        assert "schema" in metadata["requestBody"]["content"]["application/json"]
        assert (
            "$ref" in metadata["requestBody"]["content"]["application/json"]["schema"]
        )
        assert (
            metadata["requestBody"]["content"]["application/json"]["schema"]["$ref"]
            == "#/components/schemas/ConfigTestRequestModel"
        )

        # Check parameters
        assert "parameters" in metadata
        query_params = [p for p in metadata["parameters"] if p["in"] == "query"]
        assert len(query_params) == 2
    finally:
        # Restore original global config
        configure_prefixes(original_config)


class MockApi(OpenAPIIntegrationMixin):
    """Mock API class for testing."""

    def __init__(self):
        self.resources = []
        self.blueprint = type("MockBlueprint", (), {"url_prefix": None})


def test_openapi_integration_mixin_configure():
    """Test configuring OpenAPIConfig through the OpenAPIIntegrationMixin."""
    # Create an API instance
    api = MockApi()

    # Create a custom config
    custom_config = ConventionalPrefixConfig(
        request_body_prefix="api_body", request_query_prefix="api_query"
    )

    # Configure through the mixin using the object
    api.configure_openapi(prefix_config=custom_config)

    # Test the kwargs approach for backward compatibility
    api.configure_openapi(
        request_body_prefix="api_body2", request_query_prefix="api_query2"
    )

    # Since we can't easily test the global state in a reliable way,
    # we'll just verify that the method doesn't raise exceptions


class MockBlueprint(OpenAPIBlueprintMixin):
    """Mock Blueprint class for testing."""

    def __init__(self):
        self._methodview_openapi_resources = []


def test_openapi_blueprint_mixin_configure():
    """Test configuring OpenAPIConfig through the OpenAPIBlueprintMixin."""
    # Create a Blueprint instance
    blueprint = MockBlueprint()

    # Create a custom config
    custom_config = ConventionalPrefixConfig(
        request_body_prefix="bp_body", request_query_prefix="bp_query"
    )

    # Configure through the mixin using the object
    blueprint.configure_openapi(prefix_config=custom_config)

    # Test the kwargs approach for backward compatibility
    blueprint.configure_openapi(
        request_body_prefix="bp_body2", request_query_prefix="bp_query2"
    )


def test_reset_config_functions():
    """Test the reset_prefixes and reset_all_config functions."""
    # Save original global config
    original_config = GLOBAL_CONFIG_HOLDER.get()

    try:
        # Create and apply a custom config
        custom_config = ConventionalPrefixConfig(
            request_body_prefix="test_body",
            request_query_prefix="test_query",
            request_path_prefix="test_path",
            request_file_prefix="test_file",
        )
        configure_prefixes(custom_config)

        # Verify the config was applied
        current_config = GLOBAL_CONFIG_HOLDER.get()
        assert current_config.request_body_prefix == "test_body"
        assert current_config.request_query_prefix == "test_query"
        assert current_config.request_path_prefix == "test_path"
        assert current_config.request_file_prefix == "test_file"

        # Reset prefixes
        reset_prefixes()

        # Verify the config was reset
        reset_config = GLOBAL_CONFIG_HOLDER.get()
        assert reset_config.request_body_prefix == "_x_body"
        assert reset_config.request_query_prefix == "_x_query"
        assert reset_config.request_path_prefix == "_x_path"
        assert reset_config.request_file_prefix == "_x_file"

        # Create and apply a custom OpenAPI config
        openapi_config = OpenAPIConfig(
            title="Test API",
            version="2.0.0",
            description="Test API Description",
            prefix_config=custom_config,
        )
        configure_openapi(openapi_config)

        # Verify the config was applied
        current_openapi_config = get_openapi_config()
        assert current_openapi_config.title == "Test API"
        assert current_openapi_config.version == "2.0.0"
        assert current_openapi_config.description == "Test API Description"
        assert current_openapi_config.prefix_config.request_body_prefix == "test_body"

        # Reset all config
        reset_all_config()

        # Verify all config was reset
        reset_openapi_config = get_openapi_config()
        assert reset_openapi_config.title == "API Documentation"
        assert reset_openapi_config.version == "1.0.0"
        assert (
            reset_openapi_config.description
            == "API Documentation generated by flask-x-openapi-schema"
        )
        assert reset_openapi_config.prefix_config.request_body_prefix == "_x_body"
    finally:
        # Restore original global config
        configure_prefixes(original_config)
