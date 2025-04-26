"""Tests for the restful_utils module.

This module tests the utilities for integrating Pydantic models with Flask-RESTful.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

import pytest
from pydantic import BaseModel, Field

from flask_x_openapi_schema.x.flask_restful.utils import (
    _get_field_type,
    create_reqparse_from_pydantic,
    pydantic_model_to_reqparse,
)


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
    optional_field: str | None = Field(None, description="An optional field")
    list_field: list[str] = Field(default_factory=list, description="A list field")
    dict_field: dict[str, Any] = Field(default_factory=dict, description="A dict field")
    enum_field: SampleEnum = Field(SampleEnum.VALUE1, description="An enum field")

    model_config = {"arbitrary_types_allowed": True}


class SampleQueryModel(BaseModel):
    """Test model for query parameters."""

    sort: str | None = Field(None, description="Sort order")
    limit: int | None = Field(None, description="Limit results")
    page: int | None = Field(None, description="Page number")

    model_config = {"arbitrary_types_allowed": True}


class SampleBodyModel(BaseModel):
    """Test model for request body."""

    name: str = Field(..., description="The name")
    age: int = Field(..., description="The age")
    email: str | None = Field(None, description="The email")

    model_config = {"arbitrary_types_allowed": True}


class SampleFormModel(BaseModel):
    """Test model for form data."""

    username: str = Field(..., description="The username")
    password: str = Field(..., description="The password")

    model_config = {"arbitrary_types_allowed": True}


def test_pydantic_model_to_reqparse():
    """Test converting a Pydantic model to a Flask-RESTful RequestParser."""
    # Create a parser from the model
    parser = pydantic_model_to_reqparse(SampleModel)

    # Check that all fields were added to the parser
    arg_names = [arg.name for arg in parser.args]
    assert "string_field" in arg_names
    assert "int_field" in arg_names
    assert "bool_field" in arg_names
    assert "float_field" in arg_names
    assert "optional_field" in arg_names
    assert "list_field" in arg_names
    assert "dict_field" in arg_names
    assert "enum_field" in arg_names


def test_get_field_type():
    """Test the _get_field_type function."""
    # Test basic types
    assert _get_field_type(str) is str
    assert _get_field_type(int) is int
    assert _get_field_type(float) is float

    # Test bool type (special case)
    bool_converter = _get_field_type(bool)
    assert bool_converter("true") is True
    assert bool_converter("false") is False
    assert bool_converter(True) is True

    # Test container types
    assert _get_field_type(list) is list
    assert _get_field_type(dict) is dict

    # Test Optional types
    assert _get_field_type(str | None) is str

    # Test Enum types
    enum_converter = _get_field_type(SampleEnum)
    assert enum_converter("value1") == SampleEnum.VALUE1


def test_create_reqparse_from_pydantic():
    """Test creating a RequestParser from multiple Pydantic models."""
    # Create a parser with all types of models
    parser = create_reqparse_from_pydantic(
        query_model=SampleQueryModel,
        body_model=SampleBodyModel,
        form_model=SampleFormModel,
    )

    # Check that the parser has arguments from all models
    arg_names = [arg.name for arg in parser.args]

    # Check that fields from all models are present
    assert "sort" in arg_names  # from query model
    assert "limit" in arg_names  # from query model
    assert "page" in arg_names  # from query model

    assert "name" in arg_names  # from body model
    assert "age" in arg_names  # from body model
    assert "email" in arg_names  # from body model

    assert "username" in arg_names  # from form model
    assert "password" in arg_names  # from form model


class TestRestfulUtilsCoverage:
    """Tests for restful_utils to improve coverage."""

    def test_get_field_type_with_enum(self):
        """Test the _get_field_type function with an Enum type."""

        # Create an Enum class
        class Color(Enum):
            RED = "red"
            GREEN = "green"
            BLUE = "blue"

        # Get the field type function
        type_func = _get_field_type(Color)

        # Check that the function converts strings to Enum values
        assert type_func("red") == Color.RED
        assert type_func("green") == Color.GREEN
        assert type_func("blue") == Color.BLUE

        # Check that the function raises an error for invalid values
        with pytest.raises(ValueError):
            type_func("yellow")
