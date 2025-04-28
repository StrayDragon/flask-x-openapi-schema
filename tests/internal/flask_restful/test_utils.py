"""Tests for Flask-RESTful utilities."""

import pytest
from pydantic import BaseModel, Field

from flask_x_openapi_schema._opt_deps._import_utils import import_optional_dependency

# Skip tests if flask-restful is not installed
flask_restful = import_optional_dependency("flask_restful", "Flask-RESTful tests", raise_error=False)
pytestmark = pytest.mark.skipif(flask_restful is None, reason="flask-restful not installed")


@pytest.mark.skipif(flask_restful is None, reason="flask-restful not installed")
def test_create_reqparse_from_pydantic():
    """Test creating a RequestParser from a Pydantic model."""
    from flask_x_openapi_schema.x.flask_restful.utils import create_reqparse_from_pydantic

    # Define a test model
    class TestModel(BaseModel):
        name: str = Field(..., description="The name")
        age: int = Field(..., description="The age")
        is_active: bool = Field(True, description="Active status")
        tags: list[str] = Field([], description="Tags")

    # Create a parser
    parser = create_reqparse_from_pydantic(model=TestModel)

    # Check that the parser has the expected arguments
    args = parser.args

    # Check argument names
    arg_names = [arg.name for arg in args]
    assert "name" in arg_names
    assert "age" in arg_names
    assert "is_active" in arg_names
    assert "tags" in arg_names

    # Check argument types
    name_arg = next(arg for arg in args if arg.name == "name")
    age_arg = next(arg for arg in args if arg.name == "age")
    is_active_arg = next(arg for arg in args if arg.name == "is_active")
    tags_arg = next(arg for arg in args if arg.name == "tags")

    assert name_arg.type is str
    assert age_arg.type is int
    assert is_active_arg.type is bool
    assert tags_arg.type is str
    assert tags_arg.action == "append"

    # Check required status
    assert name_arg.required
    assert age_arg.required
    assert not is_active_arg.required
    assert not tags_arg.required

    # Check help text (description)
    assert name_arg.help == "The name"
    assert age_arg.help == "The age"
    assert is_active_arg.help == "Active status"
    assert tags_arg.help == "Tags"


@pytest.mark.skipif(flask_restful is None, reason="flask-restful not installed")
def test_create_reqparse_from_pydantic_with_location():
    """Test creating a RequestParser with a specific location."""
    from flask_x_openapi_schema.x.flask_restful.utils import create_reqparse_from_pydantic

    # Define a test model
    class TestModel(BaseModel):
        name: str
        age: int

    # Create a parser with a specific location
    parser = create_reqparse_from_pydantic(model=TestModel, location="form")

    # Check that the parser has the expected arguments
    args = parser.args

    # Check argument locations
    name_arg = next(arg for arg in args if arg.name == "name")
    age_arg = next(arg for arg in args if arg.name == "age")

    assert name_arg.location == "form"
    assert age_arg.location == "form"


@pytest.mark.skipif(flask_restful is None, reason="flask-restful not installed")
def test_create_reqparse_from_pydantic_with_bundle_errors():
    """Test creating a RequestParser with bundle_errors option."""
    from flask_x_openapi_schema.x.flask_restful.utils import create_reqparse_from_pydantic

    # Define a test model
    class TestModel(BaseModel):
        name: str
        age: int

    # Create a parser with bundle_errors=False
    parser = create_reqparse_from_pydantic(model=TestModel, bundle_errors=False)

    # Check that the parser has the expected bundle_errors setting
    assert not parser.bundle_errors

    # Create a parser with bundle_errors=True
    parser = create_reqparse_from_pydantic(model=TestModel, bundle_errors=True)

    # Check that the parser has the expected bundle_errors setting
    assert parser.bundle_errors


@pytest.mark.skipif(flask_restful is None, reason="flask-restful not installed")
def test_create_reqparse_from_pydantic_with_complex_types():
    """Test creating a RequestParser with complex types."""
    from flask_x_openapi_schema.x.flask_restful.utils import create_reqparse_from_pydantic

    # Define a nested model
    class Address(BaseModel):
        street: str
        city: str

    # Define a test model with complex types
    class TestModel(BaseModel):
        name: str
        address: Address
        scores: dict[str, float]

    # Create a parser
    parser = create_reqparse_from_pydantic(model=TestModel)

    # Check that the parser has the expected arguments
    args = parser.args

    # Check argument names
    arg_names = [arg.name for arg in args]
    assert "name" in arg_names
    assert "address" in arg_names
    assert "scores" in arg_names

    # Check argument types
    name_arg = next(arg for arg in args if arg.name == "name")
    address_arg = next(arg for arg in args if arg.name == "address")
    scores_arg = next(arg for arg in args if arg.name == "scores")

    assert name_arg.type is str
    # Complex types might be handled as strings or dicts depending on implementation
    assert address_arg.type in [str, dict]
    assert scores_arg.type in [str, dict]
