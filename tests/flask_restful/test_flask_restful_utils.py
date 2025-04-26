"""Tests for Flask-RESTful utility functions."""

from __future__ import annotations

from enum import Enum
from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel, Field

from flask_x_openapi_schema.models.file_models import FileField
from flask_x_openapi_schema.x.flask_restful.utils import (
    _get_field_type,
    create_reqparse_from_pydantic,
    pydantic_model_to_reqparse,
)


# Test models
class SampleEnum(Enum):
    """Sample enum for testing."""

    OPTION1 = "option1"
    OPTION2 = "option2"


class SampleColor(str, Enum):
    """Test color enum."""

    RED = "red"
    GREEN = "green"
    BLUE = "blue"


class SampleRequestModel(BaseModel):
    """Sample model for testing request parsing."""

    name: str = Field(..., description="The name")
    age: int = Field(..., description="The age")
    is_active: bool = Field(False, description="Active status")
    score: float = Field(0.0, description="Score value")
    tags: list[str] = Field([], description="Tags list")
    metadata: dict[str, str] = Field({}, description="Metadata dictionary")
    category: str | None = Field(None, description="Optional category")
    enum_field: SampleEnum = Field(SampleEnum.OPTION1, description="Enum field")


class SampleFileModel(BaseModel):
    """Sample model for testing file uploads."""

    file: FileField = Field(..., description="File to upload")
    description: str = Field("", description="File description")

    model_config = {"arbitrary_types_allowed": True}


class SampleQueryModel(BaseModel):
    """Test query model."""

    q: str = Field(..., description="Search query")
    limit: int = Field(10, description="Result limit")
    offset: int = Field(0, description="Result offset")
    filter: str | None = Field(None, description="Filter")


class SampleBodyModel(BaseModel):
    """Test body model."""

    name: str = Field(..., description="The name")
    age: int = Field(..., description="The age")
    tags: list[str] = Field(default_factory=list, description="Tags")
    color: SampleColor = Field(SampleColor.RED, description="Color")
    active: bool = Field(True, description="Active status")


class SampleFormModel(BaseModel):
    """Test form model."""

    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")
    remember: bool = Field(False, description="Remember me")


class SampleNestedModel(BaseModel):
    """Test nested model."""

    value: str = Field(..., description="A value")
    count: int = Field(0, description="A count")


class SampleComplexModel(BaseModel):
    """Test model with complex types."""

    name: str = Field(..., description="The name")
    nested: SampleNestedModel = Field(..., description="Nested model")
    items: list[str] = Field(default_factory=list, description="List of items")
    mapping: dict[str, int] = Field(default_factory=dict, description="Mapping")
    optional_value: float | None = Field(None, description="Optional value")

    model_config = {"arbitrary_types_allowed": True}


class SampleMixedFileModel(BaseModel):
    """Test model with both regular and file fields."""

    name: str = Field(..., description="The name")
    description: str = Field("", description="Description")
    file: FileField = Field(..., description="The file")
    thumbnail: FileField | None = Field(None, description="Thumbnail")

    model_config = {"arbitrary_types_allowed": True}


def test_pydantic_model_to_reqparse_2():
    """Test converting a Pydantic model to a Flask-RESTful RequestParser."""
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


# Mock Flask-RESTful's reqparse
class MockRequestParser:
    """Mock RequestParser for testing."""

    def __init__(self):
        """Initialize with empty args list."""
        self.args = []

    def add_argument(self, name, **kwargs):
        """Add an argument to the parser."""
        self.args.append({"name": name, **kwargs})
        return self

    def parse_args(self):
        """Parse arguments (mock method)."""
        return {}

    def copy(self):
        """Create a copy of the parser."""
        new_parser = MockRequestParser()
        new_parser.args = self.args.copy()
        return new_parser


@pytest.fixture
def mock_reqparse():
    """Create a mock reqparse module."""
    mock = MagicMock()
    mock.RequestParser = MockRequestParser
    return mock


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
    assert _get_field_type(str | None) is str

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

    # Test with a custom class that's not an Enum or FileField
    class CustomClass:
        pass

    custom_type = _get_field_type(CustomClass)
    assert custom_type is str  # Should default to str

    # Test bool type with additional values
    bool_func = _get_field_type(bool)
    assert bool_func("true") is True
    assert bool_func("false") is False
    assert bool_func(True) is True
    assert bool_func(False) is False

    # Test Enum types with str, Enum
    enum_func = _get_field_type(SampleColor)
    assert enum_func("red") == SampleColor.RED

    # Test FileField type with MagicMock
    file_func = _get_field_type(FileField)
    mock_file = MagicMock()
    assert file_func(mock_file) is mock_file


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


def test_get_field_type_with_complex_types():
    """Test _get_field_type function with complex types."""
    # Test generic types - these should default to str since the function
    # doesn't handle generic types like List[str] directly
    list_type = _get_field_type(list[str])
    assert list_type is str

    dict_type = _get_field_type(dict[str, int])
    assert dict_type is str

    # Test nested Optional types
    optional_list_type = _get_field_type(list[str] | None)
    assert optional_list_type is str

    # Test Union type (not Optional)
    union_type = _get_field_type(str | int)
    assert union_type is str  # Should default to str


@patch("flask_x_openapi_schema.x.flask_restful.utils.HAS_FLASK_RESTFUL", True)
@patch("flask_x_openapi_schema.x.flask_restful.utils.reqparse")
def test_pydantic_model_to_reqparse_with_complex_model(mock_reqparse):
    """Test pydantic_model_to_reqparse with a complex model."""
    # Set up mock
    mock_reqparse.RequestParser.return_value = MockRequestParser()

    # Test with complex model
    parser = pydantic_model_to_reqparse(SampleComplexModel, location="json")

    # Check that arguments were added correctly
    args = parser.args
    assert len(args) == 5  # name, nested, items, mapping, optional_value

    # Check nested model field
    nested_arg = next(arg for arg in args if arg["name"] == "nested")
    assert nested_arg["type"] is str  # Complex types default to str
    assert nested_arg["required"] is True
    assert nested_arg["location"] == "json"
    assert nested_arg["help"] == "Nested model"

    # Check list field
    items_arg = next(arg for arg in args if arg["name"] == "items")
    assert items_arg["type"] is str  # Complex types default to str
    assert items_arg["required"] is False
    assert items_arg["location"] == "json"
    assert items_arg["help"] == "List of items"

    # Check dict field
    mapping_arg = next(arg for arg in args if arg["name"] == "mapping")
    assert mapping_arg["type"] is str  # Complex types default to str
    assert mapping_arg["required"] is False
    assert mapping_arg["location"] == "json"
    assert mapping_arg["help"] == "Mapping"

    # Check optional field
    optional_arg = next(arg for arg in args if arg["name"] == "optional_value")
    assert optional_arg["type"] is float
    assert optional_arg["required"] is False
    assert optional_arg["location"] == "json"
    assert optional_arg["help"] == "Optional value"
    assert optional_arg["nullable"] is True


@patch("flask_x_openapi_schema.x.flask_restful.utils.HAS_FLASK_RESTFUL", True)
@patch("flask_x_openapi_schema.x.flask_restful.utils.reqparse")
def test_pydantic_model_to_reqparse_with_missing_field_info(mock_reqparse):
    """Test pydantic_model_to_reqparse with missing field info."""
    # Set up mock
    mock_reqparse.RequestParser.return_value = MockRequestParser()

    # Create a model with a field that will be missing from model_fields
    model = MagicMock(spec=BaseModel)
    model.model_json_schema.return_value = {
        "properties": {
            "name": {"description": "The name"},
            "missing_field": {"description": "This field will be missing"},
        },
        "required": ["name"],
    }
    model.model_fields = {
        "name": MagicMock(annotation=str),
        # missing_field is not here
    }

    # Test with model that has missing field info
    parser = pydantic_model_to_reqparse(model, location="json")

    # Check that only the valid argument was added
    args = parser.args
    assert len(args) == 1
    assert args[0]["name"] == "name"


@patch("flask_x_openapi_schema.x.flask_restful.utils.HAS_FLASK_RESTFUL", True)
@patch("flask_x_openapi_schema.x.flask_restful.utils.reqparse")
def test_pydantic_model_to_reqparse_with_file_field_in_non_files_location(
    mock_reqparse,
):
    """Test pydantic_model_to_reqparse with file field in non-files location."""
    # Set up mock
    mock_reqparse.RequestParser.return_value = MockRequestParser()

    # Test with file model but using a different location
    parser = pydantic_model_to_reqparse(SampleMixedFileModel, location="json")

    # Check that arguments were added correctly
    args = parser.args
    assert len(args) == 4

    # Check file field - should use the specified location, not 'files'
    file_arg = next(arg for arg in args if arg["name"] == "file")
    assert file_arg["location"] == "json"  # Not 'files'
    assert file_arg["help"] == "The file"


@patch("flask_x_openapi_schema.x.flask_restful.utils.HAS_FLASK_RESTFUL", True)
@patch("flask_x_openapi_schema.x.flask_restful.utils.reqparse")
@patch("flask_x_openapi_schema.x.flask_restful.utils.pydantic_model_to_reqparse")
def test_create_reqparse_from_pydantic_with_mixed_file_model(mock_to_reqparse, mock_reqparse):
    """Test create_reqparse_from_pydantic with a model containing both regular and file fields."""
    # Set up mocks
    mock_parser = MockRequestParser()
    mock_reqparse.RequestParser.return_value = mock_parser
    mock_to_reqparse.return_value = MockRequestParser()

    # Test with mixed file model
    create_reqparse_from_pydantic(body_model=SampleMixedFileModel)

    # Verify that pydantic_model_to_reqparse was called with location="files"
    # This checks that the function correctly detected file fields in the model
    mock_to_reqparse.assert_called_with(SampleMixedFileModel, location="files")


@patch("flask_x_openapi_schema.x.flask_restful.utils.HAS_FLASK_RESTFUL", True)
@patch("flask_x_openapi_schema.x.flask_restful.utils.reqparse")
def test_create_reqparse_from_pydantic_with_no_models(mock_reqparse):
    """Test create_reqparse_from_pydantic with no models provided."""
    # Set up mock
    mock_parser = MockRequestParser()
    mock_reqparse.RequestParser.return_value = mock_parser

    # Test with no models
    parser = create_reqparse_from_pydantic()

    # Check that no arguments were added
    assert len(parser.args) == 0


@patch("flask_x_openapi_schema.x.flask_restful.utils.HAS_FLASK_RESTFUL", True)
@patch("flask_x_openapi_schema.x.flask_restful.utils.reqparse")
def test_pydantic_model_to_reqparse(mock_reqparse):
    """Test pydantic_model_to_reqparse function with mock."""
    # Set up mock
    mock_reqparse.RequestParser.return_value = MockRequestParser()

    # Test with query model
    parser = pydantic_model_to_reqparse(SampleQueryModel, location="args")

    # Check that arguments were added correctly
    args = parser.args
    assert len(args) == 4

    # Check q parameter
    q_arg = next(arg for arg in args if arg["name"] == "q")
    assert q_arg["type"] is str
    assert q_arg["required"] is True
    assert q_arg["location"] == "args"
    assert q_arg["help"] == "Search query"

    # Check limit parameter
    limit_arg = next(arg for arg in args if arg["name"] == "limit")
    assert limit_arg["type"] is int
    assert limit_arg["required"] is False
    assert limit_arg["location"] == "args"
    assert limit_arg["help"] == "Result limit"

    # Test with body model
    # Create a new parser to avoid accumulating arguments
    mock_reqparse.RequestParser.return_value = MockRequestParser()
    parser = pydantic_model_to_reqparse(SampleBodyModel, location="json")

    # Check that arguments were added correctly
    args = parser.args
    assert len(args) == 5

    # Check color parameter (enum)
    color_arg = next(arg for arg in args if arg["name"] == "color")
    assert color_arg["location"] == "json"
    assert color_arg["help"] == "Color"

    # Test with file model
    # Create a new parser to avoid accumulating arguments
    mock_reqparse.RequestParser.return_value = MockRequestParser()
    parser = pydantic_model_to_reqparse(SampleFileModel, location="files")

    # Check that arguments were added correctly
    args = parser.args
    assert len(args) == 2

    # Check file parameter
    file_arg = next(arg for arg in args if arg["name"] == "file")
    assert file_arg["location"] == "files"
    assert file_arg["help"] == "File to upload"

    # Test with exclude parameter
    # Create a new parser to avoid accumulating arguments
    mock_reqparse.RequestParser.return_value = MockRequestParser()
    parser = pydantic_model_to_reqparse(SampleQueryModel, location="args", exclude=["limit", "offset"])

    # Check that excluded arguments were not added
    args = parser.args
    assert len(args) == 2
    assert all(arg["name"] != "limit" for arg in args)
    assert all(arg["name"] != "offset" for arg in args)


@patch("flask_x_openapi_schema.x.flask_restful.utils.HAS_FLASK_RESTFUL", True)
@patch("flask_x_openapi_schema.x.flask_restful.utils.reqparse")
def test_create_reqparse_from_pydantic_with_mock(mock_reqparse):
    """Test create_reqparse_from_pydantic function with mock."""
    # Set up mock
    mock_parser = MockRequestParser()
    mock_reqparse.RequestParser.return_value = mock_parser

    # Mock the pydantic_model_to_reqparse function to avoid circular dependencies
    with patch("flask_x_openapi_schema.x.flask_restful.utils.pydantic_model_to_reqparse") as mock_to_reqparse:
        # Set up mock parsers for each model type
        query_parser = MockRequestParser()
        for i in range(4):  # 4 query parameters
            query_parser.add_argument(f"query_param_{i}", location="args")

        body_parser = MockRequestParser()
        for i in range(5):  # 5 body parameters
            body_parser.add_argument(f"body_param_{i}", location="json")

        form_parser = MockRequestParser()
        for i in range(3):  # 3 form parameters
            form_parser.add_argument(f"form_param_{i}", location="form")

        file_parser = MockRequestParser()
        file_parser.add_argument("file", location="files")
        file_parser.add_argument("description", location="files")

        file_body_parser = MockRequestParser()
        file_body_parser.add_argument("name", location="json")
        file_body_parser.add_argument("file", location="files")

        # Configure mock to return different parsers based on arguments
        def side_effect(model, location="json", exclude=None):
            if model == SampleQueryModel:
                return query_parser
            if model == SampleBodyModel:
                return body_parser
            if model == SampleFormModel:
                return form_parser
            if model == SampleFileModel:
                return file_parser
            # BodyWithFileModel
            return file_body_parser

        mock_to_reqparse.side_effect = side_effect

        # Test with all model types
        parser = create_reqparse_from_pydantic(
            query_model=SampleQueryModel,
            body_model=SampleBodyModel,
            form_model=SampleFormModel,
            file_model=SampleFileModel,
        )

        # Check that arguments from all models were added
        assert len(parser.args) == 14  # 4 + 5 + 3 + 2

        # Reset mock for next test
        mock_parser = MockRequestParser()
        mock_reqparse.RequestParser.return_value = mock_parser

        # Test with only query model
        parser = create_reqparse_from_pydantic(query_model=SampleQueryModel)
        assert len(parser.args) == 4

        # Reset mock for next test
        mock_parser = MockRequestParser()
        mock_reqparse.RequestParser.return_value = mock_parser

        # Test with only body model
        parser = create_reqparse_from_pydantic(body_model=SampleBodyModel)
        assert len(parser.args) == 5

        # Reset mock for next test
        mock_parser = MockRequestParser()
        mock_reqparse.RequestParser.return_value = mock_parser

        # Test with only form model
        parser = create_reqparse_from_pydantic(form_model=SampleFormModel)
        assert len(parser.args) == 3

        # Reset mock for next test
        mock_parser = MockRequestParser()
        mock_reqparse.RequestParser.return_value = mock_parser

        # Test with only file model
        parser = create_reqparse_from_pydantic(file_model=SampleFileModel)
        assert len(parser.args) == 2

        # Test with body model containing file fields
        class BodyWithFileModel(BaseModel):
            """Body model with file field."""

            name: str = Field(..., description="The name")
            file: FileField = Field(..., description="The file")

            model_config = {"arbitrary_types_allowed": True}

        # Reset mock for next test
        mock_parser = MockRequestParser()
        mock_reqparse.RequestParser.return_value = mock_parser

        # Test with body model containing file fields
        parser = create_reqparse_from_pydantic(body_model=BodyWithFileModel)
        assert len(parser.args) == 2

        # Verify that file fields are handled correctly
        mock_to_reqparse.assert_called_with(BodyWithFileModel, location="files")


@patch("flask_x_openapi_schema.x.flask_restful.utils.HAS_FLASK_RESTFUL", False)
def test_pydantic_model_to_reqparse_no_flask_restful():
    """Test pydantic_model_to_reqparse when Flask-RESTful is not installed."""
    with pytest.raises(ImportError):
        pydantic_model_to_reqparse(SampleQueryModel)


@patch("flask_x_openapi_schema.x.flask_restful.utils.HAS_FLASK_RESTFUL", False)
def test_create_reqparse_from_pydantic_no_flask_restful():
    """Test create_reqparse_from_pydantic when Flask-RESTful is not installed."""
    with pytest.raises(ImportError):
        create_reqparse_from_pydantic(query_model=SampleQueryModel)
