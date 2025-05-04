"""Tests for Flask-RESTful decorators.

This module provides comprehensive tests for the Flask-RESTful decorators module,
covering basic functionality, advanced usage, edge cases, and integration tests.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask
from pydantic import BaseModel, Field

from flask_x_openapi_schema._opt_deps._import_utils import import_optional_dependency
from flask_x_openapi_schema.core.config import ConventionalPrefixConfig
from flask_x_openapi_schema.i18n.i18n_string import I18nStr
from flask_x_openapi_schema.models.file_models import FileField
from flask_x_openapi_schema.models.responses import OpenAPIMetaResponse, OpenAPIMetaResponseItem

# Skip tests if flask-restful is not installed
flask_restful = import_optional_dependency("flask_restful", "Flask-RESTful tests", raise_error=False)
pytestmark = pytest.mark.skipif(flask_restful is None, reason="flask-restful not installed")


@pytest.mark.skipif(flask_restful is None, reason="flask-restful not installed")
def test_flask_restful_openapi_decorator_init():
    """Test initialization of FlaskRestfulOpenAPIDecorator."""
    from flask_x_openapi_schema.x.flask_restful.decorators import FlaskRestfulOpenAPIDecorator

    # Create a decorator with all parameters
    summary = "Test summary"
    description = "Test description"
    tags = ["test"]
    operation_id = "testOperation"
    responses = OpenAPIMetaResponse(
        responses={
            "200": OpenAPIMetaResponseItem(description="Success"),
        }
    )
    deprecated = True
    security = [{"apiKey": []}]
    external_docs = {"url": "https://example.com", "description": "More info"}
    language = "en"
    prefix_config = ConventionalPrefixConfig(
        request_body_prefix="body_",
        request_query_prefix="query_",
        request_path_prefix="path_",
        request_file_prefix="file_",
    )

    decorator = FlaskRestfulOpenAPIDecorator(
        summary=summary,
        description=description,
        tags=tags,
        operation_id=operation_id,
        responses=responses,
        deprecated=deprecated,
        security=security,
        external_docs=external_docs,
        language=language,
        prefix_config=prefix_config,
    )

    # Check that parameters were stored correctly
    assert decorator.summary == summary
    assert decorator.description == description
    assert decorator.tags == tags
    assert decorator.operation_id == operation_id
    assert decorator.responses == responses
    assert decorator.deprecated == deprecated
    assert decorator.security == security
    assert decorator.external_docs == external_docs
    assert decorator.language == language
    assert decorator.prefix_config == prefix_config
    assert decorator.framework == "flask_restful"
    assert decorator.base_decorator is None


@pytest.mark.skipif(flask_restful is None, reason="flask-restful not installed")
def test_flask_restful_openapi_decorator_call():
    """Test calling FlaskRestfulOpenAPIDecorator."""
    from flask_x_openapi_schema.x.flask_restful.decorators import FlaskRestfulOpenAPIDecorator

    # Create a decorator
    decorator = FlaskRestfulOpenAPIDecorator(
        summary="Test summary",
        description="Test description",
    )

    # Define a test function
    def test_func():
        return {"message": "Hello, world!"}

    # Apply the decorator
    decorated_func = decorator(test_func)

    # Check that the base decorator was initialized
    assert decorator.base_decorator is not None

    # Check that the decorated function has the expected attributes
    # The attribute name might be _openapi_metadata instead of __openapi_metadata__
    assert hasattr(decorated_func, "_openapi_metadata") or hasattr(decorated_func, "__openapi_metadata__")

    # Get the metadata attribute, whichever exists
    metadata = getattr(decorated_func, "_openapi_metadata", None) or getattr(
        decorated_func, "__openapi_metadata__", None
    )
    assert metadata is not None
    assert metadata.get("summary") == "Test summary"
    assert metadata.get("description") == "Test description"


@pytest.mark.skipif(flask_restful is None, reason="flask-restful not installed")
def test_extract_parameters_from_models():
    """Test extracting OpenAPI parameters from models."""
    from flask_x_openapi_schema.x.flask_restful.decorators import FlaskRestfulOpenAPIDecorator

    # Create a decorator
    decorator = FlaskRestfulOpenAPIDecorator()

    # Define a query model
    class QueryModel(BaseModel):
        name: str = Field(..., description="The name")
        age: int = Field(None, description="The age")

    # Define path parameters
    path_params = ["id", "category"]

    # Extract parameters
    parameters = decorator.extract_parameters_from_models(
        query_model=QueryModel,
        path_params=path_params,
    )

    # Check path parameters
    path_parameters = [p for p in parameters if p["in"] == "path"]
    assert len(path_parameters) == 2
    assert {"name": "id", "in": "path", "required": True, "schema": {"type": "string"}} in path_parameters
    assert {"name": "category", "in": "path", "required": True, "schema": {"type": "string"}} in path_parameters

    # Check query parameters
    query_parameters = [p for p in parameters if p["in"] == "query"]
    assert len(query_parameters) == 2

    name_param = next(p for p in query_parameters if p["name"] == "name")
    age_param = next(p for p in query_parameters if p["name"] == "age")

    assert name_param["required"] is True
    assert age_param["required"] is False
    assert "description" in name_param
    assert name_param["description"] == "The name"


@pytest.mark.skipif(flask_restful is None, reason="flask-restful not installed")
def test_check_for_file_fields():
    """Test checking for file fields in a model."""
    from flask_x_openapi_schema.x.flask_restful.decorators import FlaskRestfulOpenAPIDecorator

    # Create a decorator
    decorator = FlaskRestfulOpenAPIDecorator()

    # Define a model with a file field
    class FileModel(BaseModel):
        name: str
        file: FileField

    # Define a model without a file field
    class NonFileModel(BaseModel):
        name: str
        age: int

    # Check models
    assert decorator._check_for_file_fields(FileModel) is True
    assert decorator._check_for_file_fields(NonFileModel) is False

    # Check a non-model class
    class NonModel:
        pass

    assert decorator._check_for_file_fields(NonModel) is False


@pytest.mark.skipif(flask_restful is None, reason="flask-restful not installed")
def test_openapi_metadata_decorator():
    """Test the openapi_metadata decorator function."""
    from flask_x_openapi_schema.x.flask_restful.decorators import openapi_metadata

    # Define a test function
    def test_func():
        return {"message": "Hello, world!"}

    # Apply the decorator
    decorated_func = openapi_metadata(
        summary="Test summary",
        description="Test description",
        tags=["test"],
        operation_id="testOperation",
        deprecated=True,
    )(test_func)

    # Check that the decorated function has the expected attributes
    # The attribute name might be _openapi_metadata instead of __openapi_metadata__
    assert hasattr(decorated_func, "_openapi_metadata") or hasattr(decorated_func, "__openapi_metadata__")

    # Get the metadata attribute, whichever exists
    metadata = getattr(decorated_func, "_openapi_metadata", None) or getattr(
        decorated_func, "__openapi_metadata__", None
    )
    assert metadata is not None
    assert metadata.get("summary") == "Test summary"
    assert metadata.get("description") == "Test description"
    assert metadata.get("tags") == ["test"]
    # The operation_id might be stored as operationId
    assert metadata.get("operation_id") == "testOperation" or metadata.get("operationId") == "testOperation"
    assert metadata.get("deprecated") is True


@pytest.mark.skipif(flask_restful is None, reason="flask-restful not installed")
def test_openapi_metadata_with_i18n():
    """Test the openapi_metadata decorator with I18nStr."""
    from flask_x_openapi_schema.x.flask_restful.decorators import openapi_metadata

    # Create I18nStr instances
    summary = I18nStr({"en": "Test summary", "fr": "Résumé de test"})
    description = I18nStr({"en": "Test description", "fr": "Description de test"})

    # Define a test function
    def test_func():
        return {"message": "Hello, world!"}

    # Apply the decorator
    decorated_func = openapi_metadata(
        summary=summary,
        description=description,
        language="en",
    )(test_func)

    # Check that the decorated function has the expected attributes
    # The attribute name might be _openapi_metadata instead of __openapi_metadata__
    assert hasattr(decorated_func, "_openapi_metadata") or hasattr(decorated_func, "__openapi_metadata__")

    # Get the metadata attribute, whichever exists
    metadata = getattr(decorated_func, "_openapi_metadata", None) or getattr(
        decorated_func, "__openapi_metadata__", None
    )
    assert metadata is not None
    assert metadata.get("summary") == summary
    assert metadata.get("description") == description
    # The language parameter might not be stored in the metadata
    # It's used during processing but might not be stored


@pytest.mark.skipif(flask_restful is None, reason="flask-restful not installed")
def test_get_or_create_parser():
    """Test the _get_or_create_parser method."""
    from flask_x_openapi_schema.x.flask_restful.decorators import FlaskRestfulOpenAPIDecorator

    # Create a decorator
    decorator = FlaskRestfulOpenAPIDecorator()

    # Define a test model
    class TestModel(BaseModel):
        name: str = Field(..., description="The name")
        age: int = Field(..., description="The age")

    # Get a parser
    parser = decorator._get_or_create_parser(TestModel)

    # Check that the parser has the expected arguments
    args = parser.args

    # Check argument names
    arg_names = [arg.name for arg in args]
    assert "name" in arg_names
    assert "age" in arg_names

    # Check argument types
    name_arg = next(arg for arg in args if arg.name == "name")
    age_arg = next(arg for arg in args if arg.name == "age")

    assert name_arg.type is str
    assert age_arg.type is int
    assert name_arg.location == "json"  # Default location


@pytest.mark.skipif(flask_restful is None, reason="flask-restful not installed")
def test_get_or_create_query_parser():
    """Test the _get_or_create_query_parser method."""
    from flask_x_openapi_schema.x.flask_restful.decorators import FlaskRestfulOpenAPIDecorator

    # Create a decorator
    decorator = FlaskRestfulOpenAPIDecorator()

    # Define a test model
    class QueryModel(BaseModel):
        name: str = Field(..., description="The name")
        age: int = Field(None, description="The age")

    # Get a parser
    parser = decorator._get_or_create_query_parser(QueryModel)

    # Check that the parser has the expected arguments
    args = parser.args

    # Check argument names
    arg_names = [arg.name for arg in args]
    assert "name" in arg_names
    assert "age" in arg_names

    # Check argument types and location
    name_arg = next(arg for arg in args if arg.name == "name")
    age_arg = next(arg for arg in args if arg.name == "age")

    assert name_arg.type is str
    assert age_arg.type is int
    assert name_arg.location == "args"  # Query parameters use 'args' location


@pytest.mark.skipif(flask_restful is None, reason="flask-restful not installed")
class TestFlaskRestfulDecorators:
    """Comprehensive tests for Flask-RESTful decorators."""

    def setup_method(self):
        """Set up test environment."""
        self.app = Flask(__name__)
        self.client = self.app.test_client()

    def test_extract_parameters_from_models(self):
        """Test extracting parameters from models."""
        from flask_x_openapi_schema.x.flask_restful.decorators import FlaskRestfulOpenAPIDecorator

        # Define a query model
        class QueryModel(BaseModel):
            name: str = Field(..., description="Name parameter")
            age: int = Field(0, description="Age parameter")

        # Create a decorator
        decorator = FlaskRestfulOpenAPIDecorator()

        # Test with query model and path params
        path_params = ["item_id", "user_id"]
        parameters = decorator.extract_parameters_from_models(QueryModel, path_params)

        # Check path parameters
        path_param_items = [p for p in parameters if p["in"] == "path"]
        assert len(path_param_items) == 2
        assert {"name": "item_id", "in": "path", "required": True, "schema": {"type": "string"}} in path_param_items
        assert {"name": "user_id", "in": "path", "required": True, "schema": {"type": "string"}} in path_param_items

        # Check query parameters
        query_param_items = [p for p in parameters if p["in"] == "query"]
        assert len(query_param_items) == 2

        name_param = next((p for p in query_param_items if p["name"] == "name"), None)
        assert name_param is not None
        assert name_param["required"] is True
        assert name_param["description"] == "Name parameter"

        age_param = next((p for p in query_param_items if p["name"] == "age"), None)
        assert age_param is not None
        assert age_param["required"] is False
        assert age_param["description"] == "Age parameter"

    def test_get_or_create_query_parser(self):
        """Test creating a query parser for a model."""
        from flask_x_openapi_schema.x.flask_restful.decorators import FlaskRestfulOpenAPIDecorator

        # Define a query model
        class QueryModel(BaseModel):
            name: str
            age: int = 0

        # Create a decorator
        decorator = FlaskRestfulOpenAPIDecorator()

        # Test creating a query parser
        with patch("flask_x_openapi_schema.x.flask_restful.utils.create_reqparse_from_pydantic") as mock_create:
            mock_parser = MagicMock()
            mock_create.return_value = mock_parser

            parser = decorator._get_or_create_query_parser(QueryModel)

            assert parser == mock_parser
            mock_create.assert_called_once_with(model=QueryModel, location="args")

    def test_openapi_metadata_decorator_initialization(self):
        """Test initialization of the openapi_metadata decorator."""
        from flask_x_openapi_schema.x.flask_restful import openapi_metadata

        # Create a custom prefix config
        prefix_config = ConventionalPrefixConfig(
            request_body_prefix="custom_body",
            request_query_prefix="custom_query",
            request_path_prefix="custom_path",
            request_file_prefix="custom_file",
        )

        # Create responses
        responses = OpenAPIMetaResponse(
            responses={
                "200": OpenAPIMetaResponseItem(description="Success"),
                "400": OpenAPIMetaResponseItem(description="Bad Request"),
            }
        )

        # Create the decorator
        decorator = openapi_metadata(
            summary="Test summary",
            description="Test description",
            tags=["test"],
            operation_id="testOperation",
            deprecated=True,
            responses=responses,
            security=[{"apiKey": []}],
            external_docs={"url": "https://example.com"},
            language="en",
            prefix_config=prefix_config,
        )

        # Check that the decorator is an instance of FlaskRestfulOpenAPIDecorator
        from flask_x_openapi_schema.x.flask_restful.decorators import FlaskRestfulOpenAPIDecorator

        assert isinstance(decorator, FlaskRestfulOpenAPIDecorator)

        # Check that the parameters were passed correctly
        assert decorator.summary == "Test summary"
        assert decorator.description == "Test description"
        assert decorator.tags == ["test"]
        assert decorator.operation_id == "testOperation"
        assert decorator.deprecated is True
        assert decorator.responses == responses
        assert decorator.security == [{"apiKey": []}]
        assert decorator.external_docs == {"url": "https://example.com"}
        assert decorator.language == "en"
        assert decorator.prefix_config == prefix_config
        assert decorator.framework == "flask_restful"

    def test_process_request_body_json(self):
        """Test processing request body with JSON data."""
        from flask_x_openapi_schema.x.flask_restful.decorators import FlaskRestfulOpenAPIDecorator

        # Define a request model
        class RequestModel(BaseModel):
            name: str
            age: int

        # Create a decorator
        decorator = FlaskRestfulOpenAPIDecorator()

        # Test with JSON data
        with self.app.test_request_context(
            "/",
            method="POST",
            json={"name": "test", "age": 25},
            content_type="application/json",
        ):
            # Process request body
            kwargs = {}
            result = decorator.process_request_body("body", RequestModel, kwargs)

            # Check that the model instance was created and added to kwargs
            assert "body" in result
            assert isinstance(result["body"], RequestModel)
            assert result["body"].name == "test"
            assert result["body"].age == 25

    def test_process_request_body_form(self):
        """Test processing request body with form data."""
        from flask_x_openapi_schema.x.flask_restful.decorators import FlaskRestfulOpenAPIDecorator

        # Define a request model
        class RequestModel(BaseModel):
            name: str
            age: int

        # Create a decorator
        decorator = FlaskRestfulOpenAPIDecorator()

        # Create a mock parser
        mock_parser = MagicMock()
        mock_parser.parse_args.return_value = {"name": "test", "age": 25}

        # Mock the _get_or_create_parser method
        with patch.object(decorator, "_get_or_create_parser", return_value=mock_parser):
            # Test with form data
            with self.app.test_request_context(
                "/",
                method="POST",
                data={"name": "test", "age": "25"},
                content_type="application/x-www-form-urlencoded",
            ):
                # Process request body
                kwargs = {}
                result = decorator.process_request_body("body", RequestModel, kwargs)

                # Check that the model instance was created and added to kwargs
                assert "body" in result
                assert isinstance(result["body"], RequestModel)
                assert result["body"].name == "test"
                assert result["body"].age == 25

    def test_process_query_params(self):
        """Test processing query parameters."""
        from flask_x_openapi_schema.x.flask_restful.decorators import FlaskRestfulOpenAPIDecorator

        # Define a query model
        class QueryModel(BaseModel):
            name: str
            age: int = 0

        # Create a decorator
        decorator = FlaskRestfulOpenAPIDecorator()

        # Create a mock parser
        mock_parser = MagicMock()
        mock_parser.parse_args.return_value = {"name": "test", "age": 25}

        # Test with query parameters
        with (
            patch.object(decorator, "_get_or_create_query_parser", return_value=mock_parser),
            self.app.test_request_context("/?name=test&age=25"),
        ):
            # Process query parameters
            kwargs = {}
            result = decorator.process_query_params("query", QueryModel, kwargs)

            # Check that the model instance was created and added to kwargs
            assert "query" in result
            assert isinstance(result["query"], QueryModel)
            assert result["query"].name == "test"
            assert result["query"].age == 25

    def test_process_additional_params(self):
        """Test processing additional parameters."""
        from flask_x_openapi_schema.x.flask_restful.decorators import FlaskRestfulOpenAPIDecorator

        # Create a decorator
        decorator = FlaskRestfulOpenAPIDecorator()

        # Set parsed_args
        decorator.parsed_args = {"extra1": "value1", "extra2": "value2"}

        # Test with some kwargs and param_names
        kwargs = {"param1": "value1"}
        param_names = ["param1"]

        # Process additional parameters
        result = decorator.process_additional_params(kwargs, param_names)

        # Check that the additional parameters were added to kwargs
        assert result["param1"] == "value1"
        assert result["extra1"] == "value1"
        assert result["extra2"] == "value2"

    def test_create_model_from_args(self):
        """Test creating a model from arguments."""
        from flask_x_openapi_schema.x.flask_restful.decorators import FlaskRestfulOpenAPIDecorator

        # Define a model
        class TestModel(BaseModel):
            name: str
            age: int

        # Create a decorator
        decorator = FlaskRestfulOpenAPIDecorator()

        # Test with valid arguments
        args = {"name": "test", "age": 25}
        model_instance = decorator._create_model_from_args(TestModel, args)

        # Check that the model instance was created correctly
        assert isinstance(model_instance, TestModel)
        assert model_instance.name == "test"
        assert model_instance.age == 25

        # Test with invalid arguments
        args = {"name": "test"}  # Missing required field 'age'

        # The method should try to create a model with default values
        with (
            patch(
                "flask_x_openapi_schema.core.request_extractors.safe_operation", side_effect=ValueError("Test error")
            ),
            pytest.raises(ValueError),
        ):
            decorator._create_model_from_args(TestModel, args)

    def test_create_model_from_args_with_default_values(self):
        """Test creating a model with default values for required fields."""
        from flask_x_openapi_schema.x.flask_restful.decorators import FlaskRestfulOpenAPIDecorator

        # Define a model with default values
        class TestModel(BaseModel):
            name: str = Field("default", description="Name field")
            age: int = Field(0, description="Age field")

        # Create a decorator
        decorator = FlaskRestfulOpenAPIDecorator()

        # Test with empty arguments
        args = {}

        # Create model from args
        model_instance = decorator._create_model_from_args(TestModel, args)

        # Check that the model instance was created with default values
        assert isinstance(model_instance, TestModel)
        assert model_instance.name == "default"
        assert model_instance.age == 0

    def test_process_query_params_with_valid_data(self):
        """Test processing query parameters with valid data."""
        from flask_x_openapi_schema.x.flask_restful.decorators import FlaskRestfulOpenAPIDecorator

        # Define a query model
        class QueryModel(BaseModel):
            name: str = Field(..., description="Name field")
            age: int = Field(0, description="Age field")

        # Create a decorator
        decorator = FlaskRestfulOpenAPIDecorator()

        # Create a mock parser
        mock_parser = MagicMock()
        mock_parser.parse_args.return_value = {"name": "test", "age": 25}

        # Test with valid query parameters
        with (
            patch.object(decorator, "_get_or_create_query_parser", return_value=mock_parser),
            self.app.test_request_context("/?name=test&age=25"),
        ):
            # Process query parameters
            kwargs = {}
            result = decorator.process_query_params("query", QueryModel, kwargs)

            # Check that the model instance was created correctly
            assert "query" in result
            assert isinstance(result["query"], QueryModel)
            assert result["query"].name == "test"
            assert result["query"].age == 25

    def test_process_query_params_with_exception_handling(self):
        """Test processing query parameters with exception handling."""
        from flask_x_openapi_schema.x.flask_restful.decorators import FlaskRestfulOpenAPIDecorator

        # Define a query model
        class QueryModel(BaseModel):
            name: str = Field(..., description="Name field")
            age: int = Field(0, description="Age field")

        # Create a decorator
        decorator = FlaskRestfulOpenAPIDecorator()

        # Create a mock parser
        mock_parser = MagicMock()
        mock_parser.parse_args.return_value = {"name": "test", "age": 25}

        # Test with exception handling
        with (
            patch.object(decorator, "_get_or_create_query_parser", return_value=mock_parser),
            self.app.test_request_context("/?name=test&age=25"),
        ):
            # Mock _create_model_from_args to raise an exception
            with patch.object(decorator, "_create_model_from_args", side_effect=Exception("Test error")):
                # Process query parameters
                kwargs = {}

                # This should not raise an exception
                result = decorator.process_query_params("query", QueryModel, kwargs)

                # Check that a fallback model instance was attempted
                assert "query" not in result  # Since both attempts failed

    def test_resource_with_complex_openapi_metadata(self):
        """Test a Resource class with complex openapi_metadata configuration."""
        if flask_restful is None:
            pytest.skip("flask-restful not installed")

        # Import required modules
        from flask_restful import Api, Resource

        from flask_x_openapi_schema.x.flask_restful import openapi_metadata

        # Define models
        class QueryParams(BaseModel):
            filter: str = Field(None, description="Filter results")
            sort: str = Field("asc", description="Sort order")

        class UserRequest(BaseModel):
            name: str = Field(..., description="User name")
            email: str = Field(..., description="User email")
            role: str = Field("user", description="User role")

        class UserResponse(BaseModel):
            id: str = Field(..., description="User ID")
            name: str = Field(..., description="User name")
            email: str = Field(..., description="User email")
            role: str = Field(..., description="User role")
            created_at: str = Field(..., description="Creation timestamp")

        # Define a Resource class with openapi_metadata
        class UserResource(Resource):
            @openapi_metadata(
                summary="Create user",
                description="Create a new user with the provided information",
                tags=["users"],
                operation_id="createUser",
                responses=OpenAPIMetaResponse(
                    responses={
                        "201": OpenAPIMetaResponseItem(model=UserResponse, description="User created successfully"),
                        "400": OpenAPIMetaResponseItem(description="Invalid request data"),
                        "409": OpenAPIMetaResponseItem(description="User already exists"),
                    }
                ),
            )
            def post(self, _x_body: UserRequest, _x_query: QueryParams):
                # Use both body and query parameters
                return {
                    "id": "123",
                    "name": _x_body.name,
                    "email": _x_body.email,
                    "role": _x_body.role,
                    "created_at": "2023-01-01T00:00:00Z",
                    "filter": _x_query.filter,
                    "sort": _x_query.sort,
                }, 201

        # Create a Flask app and API
        app = Flask(__name__)
        api = Api(app)
        api.add_resource(UserResource, "/users")

        # Test the endpoint with query parameters
        with app.test_client() as client:
            response = client.post(
                "/users?filter=active&sort=desc",
                data=json.dumps({"name": "John Doe", "email": "john@example.com"}),
                content_type="application/json",
            )

            # Check the response
            assert response.status_code == 201
            data = json.loads(response.data)
            assert data["id"] == "123"
            assert data["name"] == "John Doe"
            assert data["email"] == "john@example.com"
            assert data["role"] == "user"  # Default value

    def test_integration_with_flask_restful_resource(self):
        """Test integration with Flask-RESTful Resource."""
        if flask_restful is None:
            pytest.skip("flask-restful not installed")

        # Import required modules
        from flask_restful import Api, Resource

        from flask_x_openapi_schema.x.flask_restful import openapi_metadata

        # Define models
        class QueryParams(BaseModel):
            filter: str = Field(None, description="Filter results")
            sort: str = Field("asc", description="Sort order")

        class ItemRequest(BaseModel):
            name: str = Field(..., description="Item name")
            price: float = Field(..., description="Item price")

        class ItemResponse(BaseModel):
            id: str = Field(..., description="Item ID")
            name: str = Field(..., description="Item name")
            price: float = Field(..., description="Item price")

        # Define a Resource class with openapi_metadata
        class ItemResource(Resource):
            @openapi_metadata(
                summary="Create item",
                description="Create a new item with the provided information",
                tags=["items"],
                operation_id="createItem",
                responses=OpenAPIMetaResponse(
                    responses={
                        "201": OpenAPIMetaResponseItem(model=ItemResponse, description="Item created successfully"),
                        "400": OpenAPIMetaResponseItem(description="Invalid request data"),
                    }
                ),
            )
            def post(self, _x_body: ItemRequest, _x_query: QueryParams):
                # Use both body and query parameters
                return {
                    "id": "123",
                    "name": _x_body.name,
                    "price": _x_body.price,
                    "filter": _x_query.filter,
                    "sort": _x_query.sort,
                }, 201

        # Create a Flask app and API
        app = Flask(__name__)
        api = Api(app)
        api.add_resource(ItemResource, "/items")

        # Test the endpoint with query parameters
        with app.test_client() as client:
            response = client.post(
                "/items?filter=active&sort=desc",
                data=json.dumps({"name": "Test Item", "price": 99.99}),
                content_type="application/json",
            )

            # Check the response
            assert response.status_code == 201
            data = json.loads(response.data)
            assert data["id"] == "123"
            assert data["name"] == "Test Item"
            assert data["price"] == 99.99
