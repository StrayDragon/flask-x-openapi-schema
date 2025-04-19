"""
Tests for the restful_utils module.

This module tests the utilities for integrating Pydantic models with Flask-RESTful.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from flask_x_openapi_schema.x.flask_restful.utils import _get_field_type, create_reqparse_from_pydantic, pydantic_model_to_reqparse


class SampleEnum(Enum):
    """Test enum for testing."""

    VALUE1 = "value1"
    VALUE2 = "value2"


class SampleModel(BaseModel):
    """Test model for testing."""

    string_field: str = Field(..., description="A string field")
    int_field: int = Field(..., description="An integer field")
    float_field: float = Field(..., description="A float field")
    bool_field: bool = Field(..., description="A boolean field")
    optional_field: Optional[str] = Field(None, description="An optional field")
    list_field: List[str] = Field(default_factory=list, description="A list field")
    dict_field: Dict[str, Any] = Field(default_factory=dict, description="A dict field")
    enum_field: SampleEnum = Field(SampleEnum.VALUE1, description="An enum field")

    model_config = {"arbitrary_types_allowed": True}


class SampleQueryModel(BaseModel):
    """Test model for query parameters."""

    sort: Optional[str] = Field(None, description="Sort order")
    limit: Optional[int] = Field(None, description="Limit results")
    page: Optional[int] = Field(None, description="Page number")

    model_config = {"arbitrary_types_allowed": True}


class SampleBodyModel(BaseModel):
    """Test model for request body."""

    name: str = Field(..., description="The name")
    age: int = Field(..., description="The age")
    email: Optional[str] = Field(None, description="The email")

    model_config = {"arbitrary_types_allowed": True}


class SampleFormModel(BaseModel):
    """Test model for form data."""

    username: str = Field(..., description="The username")
    password: str = Field(..., description="The password")

    model_config = {"arbitrary_types_allowed": True}


def test_pydantic_model_to_reqparse():
    """Test converting a Pydantic model to a Flask-RESTful RequestParser."""
    parser = pydantic_model_to_reqparse(SampleModel)

    # Check that all fields are added to the parser
    arg_names = [arg.name for arg in parser.args]
    assert "string_field" in arg_names
    assert "int_field" in arg_names
    assert "float_field" in arg_names
    assert "bool_field" in arg_names
    assert "optional_field" in arg_names
    assert "list_field" in arg_names
    assert "dict_field" in arg_names
    assert "enum_field" in arg_names

    # Check required fields
    required_args = [arg for arg in parser.args if arg.required]
    required_names = [arg.name for arg in required_args]
    assert "string_field" in required_names
    assert "int_field" in required_names
    assert "float_field" in required_names
    assert "bool_field" in required_names
    assert "optional_field" not in required_names

    # Check field types
    string_arg = next((arg for arg in parser.args if arg.name == "string_field"), None)
    assert string_arg is not None
    assert string_arg.type is str

    int_arg = next((arg for arg in parser.args if arg.name == "int_field"), None)
    assert int_arg is not None
    assert int_arg.type is int

    float_arg = next((arg for arg in parser.args if arg.name == "float_field"), None)
    assert float_arg is not None
    assert float_arg.type is float

    # Check field descriptions
    assert string_arg.help == "A string field"

    # Check location
    assert string_arg.location == "json"

    # Test with different location
    parser = pydantic_model_to_reqparse(SampleModel, location="args")
    string_arg = next((arg for arg in parser.args if arg.name == "string_field"), None)
    assert string_arg.location == "args"

    # Test with exclude
    parser = pydantic_model_to_reqparse(
        SampleModel, exclude=["string_field", "int_field"]
    )
    arg_names = [arg.name for arg in parser.args]
    assert "string_field" not in arg_names
    assert "int_field" not in arg_names
    assert "float_field" in arg_names


def test_get_field_type():
    """Test the _get_field_type function."""
    # Test basic types
    assert _get_field_type(str) is str
    assert _get_field_type(int) is int
    assert _get_field_type(float) is float
    assert _get_field_type(bool) is not bool  # It returns a lambda function
    assert _get_field_type(list) is list
    assert _get_field_type(dict) is dict

    # Test Optional types
    assert _get_field_type(Optional[str]) is str
    assert _get_field_type(Optional[int]) is int
    assert _get_field_type(Optional[float]) is float

    # Test Enum types
    enum_type = _get_field_type(SampleEnum)
    assert callable(enum_type)

    # Test unknown type
    class UnknownType:
        pass

    assert _get_field_type(UnknownType) is str  # Default to string


def test_create_reqparse_from_pydantic():
    """Test creating a RequestParser from multiple Pydantic models."""
    # Test with query model only
    parser = create_reqparse_from_pydantic(query_model=SampleQueryModel)
    arg_names = [arg.name for arg in parser.args]
    assert "sort" in arg_names
    assert "limit" in arg_names
    assert "page" in arg_names

    # Check locations
    sort_arg = next((arg for arg in parser.args if arg.name == "sort"), None)
    assert sort_arg.location == "args"

    # Test with body model only
    parser = create_reqparse_from_pydantic(body_model=SampleBodyModel)
    arg_names = [arg.name for arg in parser.args]
    assert "name" in arg_names
    assert "age" in arg_names
    assert "email" in arg_names

    # Check locations
    name_arg = next((arg for arg in parser.args if arg.name == "name"), None)
    assert name_arg.location == "json"

    # Test with form model only
    parser = create_reqparse_from_pydantic(form_model=SampleFormModel)
    arg_names = [arg.name for arg in parser.args]
    assert "username" in arg_names
    assert "password" in arg_names

    # Check locations
    username_arg = next((arg for arg in parser.args if arg.name == "username"), None)
    assert username_arg.location == "form"

    # Test with all models
    parser = create_reqparse_from_pydantic(
        query_model=SampleQueryModel,
        body_model=SampleBodyModel,
        form_model=SampleFormModel,
    )
    arg_names = [arg.name for arg in parser.args]
    assert "sort" in arg_names
    assert "limit" in arg_names
    assert "page" in arg_names
    assert "name" in arg_names
    assert "age" in arg_names
    assert "email" in arg_names
    assert "username" in arg_names
    assert "password" in arg_names

    # Check locations
    sort_arg = next((arg for arg in parser.args if arg.name == "sort"), None)
    assert sort_arg.location == "args"

    name_arg = next((arg for arg in parser.args if arg.name == "name"), None)
    assert name_arg.location == "json"

    username_arg = next((arg for arg in parser.args if arg.name == "username"), None)
    assert username_arg.location == "form"
