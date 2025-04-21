"""
Tests for Flask-RESTful utility functions.
"""

from enum import Enum
from typing import Optional, List, Dict
from pydantic import BaseModel, Field

from flask_x_openapi_schema.x.flask_restful.utils import (
    pydantic_model_to_reqparse,
    _get_field_type,
    create_reqparse_from_pydantic,
)
from flask_x_openapi_schema.models.file_models import FileField


# Renamed to avoid pytest collection warning
class SampleEnum(Enum):
    """Sample enum for testing."""

    OPTION1 = "option1"
    OPTION2 = "option2"


# Renamed to avoid pytest collection warning
class SampleRequestModel(BaseModel):
    """Sample model for testing request parsing."""

    name: str = Field(..., description="The name")
    age: int = Field(..., description="The age")
    is_active: bool = Field(False, description="Active status")
    score: float = Field(0.0, description="Score value")
    tags: List[str] = Field([], description="Tags list")
    metadata: Dict[str, str] = Field({}, description="Metadata dictionary")
    category: Optional[str] = Field(None, description="Optional category")
    enum_field: SampleEnum = Field(SampleEnum.OPTION1, description="Enum field")


# Renamed to avoid pytest collection warning
class SampleFileModel(BaseModel):
    """Sample model for testing file uploads."""

    file: FileField = Field(..., description="File to upload")
    description: str = Field("", description="File description")


def test_pydantic_model_to_reqparse():
    """Test converting a Pydantic model to a Flask-RESTful RequestParser."""
    # Create a parser from the model
    parser = pydantic_model_to_reqparse(SampleRequestModel)

    # Check that all fields were added to the parser
    arg_names = [arg.name for arg in parser.args]
    assert "name" in arg_names
    assert "age" in arg_names
    assert "is_active" in arg_names
    assert "score" in arg_names
    assert "tags" in arg_names
    assert "metadata" in arg_names
    assert "category" in arg_names
    assert "enum_field" in arg_names

    # Check that required fields are marked as required
    required_args = [arg for arg in parser.args if arg.required]
    required_names = [arg.name for arg in required_args]
    assert "name" in required_names
    assert "age" in required_names

    # Check that optional fields are not marked as required
    assert "category" not in required_names

    # Check that descriptions are set correctly
    name_arg = next(arg for arg in parser.args if arg.name == "name")
    assert name_arg.help == "The name"


def test_pydantic_model_to_reqparse_with_location():
    """Test converting a Pydantic model to a RequestParser with different locations."""
    # Test with query parameters
    query_parser = pydantic_model_to_reqparse(SampleRequestModel, location="args")
    for arg in query_parser.args:
        assert arg.location == "args"

    # Test with form data
    form_parser = pydantic_model_to_reqparse(SampleRequestModel, location="form")
    for arg in form_parser.args:
        assert arg.location == "form"


def test_pydantic_model_to_reqparse_with_exclude():
    """Test converting a Pydantic model to a RequestParser with excluded fields."""
    # Create a parser with excluded fields
    parser = pydantic_model_to_reqparse(SampleRequestModel, exclude=["age", "tags"])

    # Check that excluded fields are not in the parser
    arg_names = [arg.name for arg in parser.args]
    assert "name" in arg_names
    assert "age" not in arg_names
    assert "tags" not in arg_names


def test_get_field_type():
    """Test getting the appropriate type function for field annotations."""
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
    assert _get_field_type(Optional[str]) is str

    # Test Enum types
    enum_converter = _get_field_type(SampleEnum)
    assert enum_converter("option1") == SampleEnum.OPTION1

    # Test FileField types
    file_converter = _get_field_type(FileField)
    mock_file = object()
    assert file_converter(mock_file) is mock_file

    # Test unknown type (defaults to str)
    class UnknownType:
        pass

    assert _get_field_type(UnknownType) is str


def test_create_reqparse_from_pydantic():
    """Test creating a RequestParser from multiple Pydantic models."""
    # Create a parser with all types of models
    parser = create_reqparse_from_pydantic(
        query_model=SampleRequestModel,
        body_model=SampleRequestModel,
        form_model=SampleRequestModel,
        file_model=SampleFileModel,
    )

    # Check that the parser has arguments from all models
    arg_names = [arg.name for arg in parser.args]

    # Each model adds its fields, so we should have multiple instances of each field
    # (except for file which is only in the file model)
    assert arg_names.count("name") == 3  # query, body, form
    assert arg_names.count("age") == 3  # query, body, form
    assert "file" in arg_names  # from file model

    # Check locations
    query_args = [arg for arg in parser.args if arg.location == "args"]
    assert len(query_args) > 0

    json_args = [arg for arg in parser.args if arg.location == "json"]
    assert len(json_args) > 0

    form_args = [arg for arg in parser.args if arg.location == "form"]
    assert len(form_args) > 0

    file_args = [arg for arg in parser.args if arg.location == "files"]
    assert len(file_args) > 0


def test_create_reqparse_from_pydantic_with_file_in_body():
    """Test creating a RequestParser with a file field in the body model."""
    # Create a parser with a body model that contains a file field
    parser = create_reqparse_from_pydantic(
        body_model=SampleFileModel,
    )

    # Check that the file field uses the files location
    file_args = [arg for arg in parser.args if arg.name == "file"]
    assert len(file_args) == 1
    assert file_args[0].location == "files"
