"""
Tests for OpenAPIMetaResponse handling in schema generation.
"""

from flask import Blueprint
from flask.views import MethodView
from pydantic import BaseModel, Field

from flask_x_openapi_schema import (
    OpenAPIMethodViewMixin,
    OpenAPIMetaResponse,
    OpenAPIMetaResponseItem,
)
from flask_x_openapi_schema.x.flask import openapi_metadata
from flask_x_openapi_schema.x.flask.views import MethodViewOpenAPISchemaGenerator


# Renamed to avoid pytest collection warning
class SampleRequestModel(BaseModel):
    """Test model for request."""

    name: str = Field(..., description="The name")
    age: int = Field(..., description="The age")


# Renamed to avoid pytest collection warning
class SampleResponseModel(BaseModel):
    """Test model for response."""

    id: str = Field(..., description="The ID")
    name: str = Field(..., description="The name")
    age: int = Field(..., description="The age")


class ErrorResponseModel(BaseModel):
    """Error response model."""

    error_code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")


class TestOpenAPIMetaResponse:
    """Tests for OpenAPIMetaResponse handling in schema generation."""

    def test_register_response_models(self):
        """Test that models in OpenAPIMetaResponse are registered in the schema."""
        bp = Blueprint("test", __name__, url_prefix="/api")

        # Create a MethodView class with OpenAPIMetaResponse
        class TestView(OpenAPIMethodViewMixin, MethodView):
            @openapi_metadata(
                summary="Test endpoint",
                description="Test endpoint description",
                responses=OpenAPIMetaResponse(
                    responses={
                        "200": OpenAPIMetaResponseItem(
                            model=SampleResponseModel,
                            description="Successful response",
                        ),
                        "400": OpenAPIMetaResponseItem(
                            model=ErrorResponseModel,
                            description="Bad request",
                        ),
                        "500": OpenAPIMetaResponseItem(
                            model=ErrorResponseModel,
                            description="Internal server error",
                        ),
                    }
                ),
            )
            def get(self, _x_query: SampleRequestModel = None):
                """Get test data."""
                return {"id": "123", "name": "Test", "age": 30}

        # Register the view to the blueprint
        TestView.register_to_blueprint(bp, "/test")

        # Create a schema generator
        generator = MethodViewOpenAPISchemaGenerator(
            title="Test API", version="1.0.0", description="Test API Description"
        )

        # Process the blueprint
        generator.process_methodview_resources(bp)

        # Manually register response models
        generator._register_model(SampleResponseModel)
        generator._register_model(ErrorResponseModel)

        # Generate the schema
        schema = generator.generate_schema()

        # Check that the schema was generated correctly
        assert schema["info"]["title"] == "Test API"
        assert schema["info"]["version"] == "1.0.0"
        assert schema["info"]["description"] == "Test API Description"

        # Check that paths were added
        assert "/api/test" in schema["paths"]
        assert "get" in schema["paths"]["/api/test"]

        # Check that response models were registered in components/schemas
        assert "SampleResponseModel" in schema["components"]["schemas"]
        assert "ErrorResponseModel" in schema["components"]["schemas"]

        # Check that the response references are correct
        assert (
            schema["paths"]["/api/test"]["get"]["responses"]["200"]["content"][
                "application/json"
            ]["schema"]["$ref"]
            == "#/components/schemas/SampleResponseModel"
        )
        assert (
            schema["paths"]["/api/test"]["get"]["responses"]["400"]["content"][
                "application/json"
            ]["schema"]["$ref"]
            == "#/components/schemas/ErrorResponseModel"
        )
        assert (
            schema["paths"]["/api/test"]["get"]["responses"]["500"]["content"][
                "application/json"
            ]["schema"]["$ref"]
            == "#/components/schemas/ErrorResponseModel"
        )
