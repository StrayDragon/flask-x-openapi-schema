"""
Tests for the utils module.

This module tests the utility functions for OpenAPI schema generation.
"""

from enum import Enum
from datetime import date, datetime, time
from typing import Dict, List, Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field

from flask_x_openapi_schema.utils import (
    pydantic_to_openapi_schema,
    python_type_to_openapi_type,
    response_schema,
    error_response_schema,
    success_response,
    responses_schema,
)


class SampleEnum(Enum):
    """Test enum for testing."""

    VALUE1 = "value1"
    VALUE2 = "value2"


class SampleModel(BaseModel):
    """Test model for testing.

    This is a test model with various field types.
    """

    string_field: str = Field(..., description="A string field")
    int_field: int = Field(..., description="An integer field")
    float_field: float = Field(..., description="A float field")
    bool_field: bool = Field(..., description="A boolean field")
    optional_field: Optional[str] = Field(None, description="An optional field")
    list_field: List[str] = Field(default_factory=list, description="A list field")
    dict_field: Dict[str, Any] = Field(default_factory=dict, description="A dict field")
    enum_field: SampleEnum = Field(SampleEnum.VALUE1, description="An enum field")

    model_config = {"arbitrary_types_allowed": True}


class NestedModel(BaseModel):
    """Nested model for testing."""

    name: str = Field(..., description="The name")
    value: int = Field(..., description="The value")

    model_config = {"arbitrary_types_allowed": True}


class SampleModelWithNested(BaseModel):
    """Test model with nested model."""

    id: str = Field(..., description="The ID")
    nested: NestedModel = Field(..., description="A nested model")

    model_config = {"arbitrary_types_allowed": True}


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="The error message")
    code: int = Field(..., description="The error code")

    model_config = {"arbitrary_types_allowed": True}


def test_pydantic_to_openapi_schema():
    """Test converting a Pydantic model to an OpenAPI schema."""
    # Test with a simple model
    schema = pydantic_to_openapi_schema(SampleModel)

    # Check schema structure
    assert schema["type"] == "object"
    assert "properties" in schema
    assert "required" in schema

    # Check properties
    properties = schema["properties"]
    assert "string_field" in properties
    assert "int_field" in properties
    assert "float_field" in properties
    assert "bool_field" in properties
    assert "optional_field" in properties
    assert "list_field" in properties
    assert "dict_field" in properties
    assert "enum_field" in properties

    # Check property types
    assert properties["string_field"]["type"] == "string"
    assert properties["int_field"]["type"] == "integer"
    assert properties["float_field"]["type"] == "number"
    assert properties["bool_field"]["type"] == "boolean"
    assert properties["list_field"]["type"] == "array"
    assert properties["dict_field"]["type"] == "object"

    # Check required fields
    required = schema["required"]
    assert "string_field" in required
    assert "int_field" in required
    assert "float_field" in required
    assert "bool_field" in required
    assert "optional_field" not in required

    # Check descriptions
    assert properties["string_field"]["description"] == "A string field"
    assert properties["int_field"]["description"] == "An integer field"

    # Check model description
    assert "description" in schema
    assert "This is a test model with various field types." in schema["description"]

    # Test with a model that has a nested model
    schema = pydantic_to_openapi_schema(SampleModelWithNested)

    # Check nested model reference
    properties = schema["properties"]
    assert "nested" in properties
    # The reference format might be different in Pydantic v2
    assert "$ref" in properties["nested"]
    assert "NestedModel" in properties["nested"]["$ref"]


def test_python_type_to_openapi_type():
    """Test converting Python types to OpenAPI types."""
    # Test primitive types
    assert python_type_to_openapi_type(str) == {"type": "string"}
    assert python_type_to_openapi_type(int) == {"type": "integer"}
    assert python_type_to_openapi_type(float) == {"type": "number"}
    assert python_type_to_openapi_type(bool) == {"type": "boolean"}

    # Test list types
    assert python_type_to_openapi_type(list) == {"type": "array"}
    assert python_type_to_openapi_type(List[str]) == {
        "type": "array",
        "items": {"type": "string"},
    }
    assert python_type_to_openapi_type(List[int]) == {
        "type": "array",
        "items": {"type": "integer"},
    }

    # Test dict types
    assert python_type_to_openapi_type(dict) == {"type": "object"}
    assert python_type_to_openapi_type(Dict[str, Any]) == {"type": "object"}

    # Test special types
    assert python_type_to_openapi_type(UUID) == {"type": "string", "format": "uuid"}
    assert python_type_to_openapi_type(datetime) == {
        "type": "string",
        "format": "date-time",
    }
    assert python_type_to_openapi_type(date) == {"type": "string", "format": "date"}
    assert python_type_to_openapi_type(time) == {"type": "string", "format": "time"}

    # Test enum types
    enum_schema = python_type_to_openapi_type(SampleEnum)
    assert enum_schema["type"] == "string"
    assert "enum" in enum_schema
    assert enum_schema["enum"] == ["value1", "value2"]

    # Test Pydantic model types
    model_schema = python_type_to_openapi_type(SampleModel)
    assert model_schema["$ref"] == "#/components/schemas/SampleModel"

    # Test unknown types
    class UnknownType:
        pass

    assert python_type_to_openapi_type(UnknownType) == {"type": "string"}


def test_response_schema():
    """Test generating an OpenAPI response schema."""
    # Test with default status code
    schema = response_schema(SampleModel, "Successful response")

    # Check schema structure
    assert "200" in schema
    assert schema["200"]["description"] == "Successful response"
    assert "content" in schema["200"]
    assert "application/json" in schema["200"]["content"]
    assert "schema" in schema["200"]["content"]["application/json"]
    assert (
        schema["200"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/SampleModel"
    )

    # Test with custom status code
    schema = response_schema(SampleModel, "Created successfully", 201)

    # Check schema structure
    assert "201" in schema
    assert schema["201"]["description"] == "Created successfully"

    # Test with string status code
    schema = response_schema(SampleModel, "Accepted", "202")

    # Check schema structure
    assert "202" in schema
    assert schema["202"]["description"] == "Accepted"


def test_error_response_schema():
    """Test generating an OpenAPI error response schema."""
    # Test with default status code
    schema = error_response_schema("Bad request")

    # Check schema structure
    assert "400" in schema
    assert schema["400"]["description"] == "Bad request"

    # Test with custom status code
    schema = error_response_schema("Not found", 404)

    # Check schema structure
    assert "404" in schema
    assert schema["404"]["description"] == "Not found"

    # Test with string status code
    schema = error_response_schema("Unauthorized", "401")

    # Check schema structure
    assert "401" in schema
    assert schema["401"]["description"] == "Unauthorized"


def test_success_response():
    """Test creating a success response tuple."""
    # Create a success response tuple
    response = success_response(SampleModel, "Successful response")

    # Check tuple structure
    assert isinstance(response, tuple)
    assert len(response) == 2
    assert response[0] == SampleModel
    assert response[1] == "Successful response"


def test_responses_schema():
    """Test generating a complete OpenAPI responses schema."""
    # Test with success responses only
    schema = responses_schema(
        {
            200: success_response(SampleModel, "Successful response"),
            201: success_response(SampleModel, "Created successfully"),
        }
    )

    # Check schema structure
    assert "200" in schema
    assert schema["200"]["description"] == "Successful response"
    assert (
        schema["200"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/SampleModel"
    )

    assert "201" in schema
    assert schema["201"]["description"] == "Created successfully"
    assert (
        schema["201"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/SampleModel"
    )

    # Test with success and error responses
    schema = responses_schema(
        {
            200: success_response(SampleModel, "Successful response"),
            201: success_response(SampleModel, "Created successfully"),
        },
        {400: "Bad request", 404: "Not found"},
    )

    # Check schema structure
    assert "200" in schema
    assert schema["200"]["description"] == "Successful response"

    assert "201" in schema
    assert schema["201"]["description"] == "Created successfully"

    assert "400" in schema
    assert schema["400"]["description"] == "Bad request"

    assert "404" in schema
    assert schema["404"]["description"] == "Not found"

    # Test with string status codes
    schema = responses_schema(
        {
            "200": success_response(SampleModel, "Successful response"),
            "201": success_response(SampleModel, "Created successfully"),
        },
        {"400": "Bad request", "404": "Not found"},
    )

    # Check schema structure
    assert "200" in schema
    assert "201" in schema
    assert "400" in schema
    assert "404" in schema
