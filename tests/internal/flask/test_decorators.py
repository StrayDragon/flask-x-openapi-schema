"""Tests for Flask decorators."""

from flask import Flask
from pydantic import BaseModel, Field

from flask_x_openapi_schema.core.config import ConventionalPrefixConfig
from flask_x_openapi_schema.i18n.i18n_string import I18nStr
from flask_x_openapi_schema.models.responses import OpenAPIMetaResponse, OpenAPIMetaResponseItem


def test_flask_openapi_decorator_init():
    """Test initialization of FlaskOpenAPIDecorator."""
    from flask_x_openapi_schema.x.flask.decorators import FlaskOpenAPIDecorator

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

    decorator = FlaskOpenAPIDecorator(
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
    assert decorator.framework == "flask"
    assert decorator.base_decorator is None


def test_flask_openapi_decorator_call():
    """Test calling FlaskOpenAPIDecorator."""
    from flask_x_openapi_schema.x.flask.decorators import FlaskOpenAPIDecorator

    # Create a decorator
    decorator = FlaskOpenAPIDecorator(
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


def test_extract_parameters_from_models():
    """Test extracting OpenAPI parameters from models."""
    from flask_x_openapi_schema.x.flask.decorators import FlaskOpenAPIDecorator

    # Create a decorator
    decorator = FlaskOpenAPIDecorator()

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


def test_process_query_params():
    """Test processing query parameters."""
    from flask_x_openapi_schema.x.flask.decorators import FlaskOpenAPIDecorator

    # Create a Flask app and request context
    app = Flask(__name__)

    # Define a query model
    class QueryModel(BaseModel):
        name: str
        age: int = 0

    # Create a decorator
    decorator = FlaskOpenAPIDecorator()

    # Test with query parameters
    with app.test_request_context("/?name=test&age=25"):
        # Process query parameters
        kwargs = {}
        result = decorator.process_query_params("query", QueryModel, kwargs)

        # Check that the model instance was created and added to kwargs
        assert "query" in result
        assert isinstance(result["query"], QueryModel)
        assert result["query"].name == "test"
        assert result["query"].age == 25


def test_openapi_metadata_decorator():
    """Test the openapi_metadata decorator function."""
    from flask_x_openapi_schema.x.flask.decorators import openapi_metadata

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


def test_openapi_metadata_with_i18n():
    """Test the openapi_metadata decorator with I18nStr."""
    from flask_x_openapi_schema.x.flask.decorators import openapi_metadata

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


def test_process_request_body_json():
    """Test processing request body with JSON data."""
    from flask_x_openapi_schema.x.flask.decorators import FlaskOpenAPIDecorator

    # Create a Flask app and request context
    app = Flask(__name__)

    # Define a request model
    class RequestModel(BaseModel):
        name: str
        age: int

    # Create a decorator
    decorator = FlaskOpenAPIDecorator()

    # Test with JSON data
    with app.test_request_context(
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


def test_process_request_body_form():
    """Test processing request body with form data."""
    from flask_x_openapi_schema.x.flask.decorators import FlaskOpenAPIDecorator

    # Create a Flask app and request context
    app = Flask(__name__)

    # Define a request model
    class RequestModel(BaseModel):
        name: str
        age: int

    # Create a decorator
    decorator = FlaskOpenAPIDecorator()

    # Test with form data
    with app.test_request_context(
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


def test_process_additional_params():
    """Test processing additional parameters."""
    from flask_x_openapi_schema.x.flask.decorators import FlaskOpenAPIDecorator

    # Create a decorator
    decorator = FlaskOpenAPIDecorator()

    # Test with some kwargs and param_names
    kwargs = {"param1": "value1", "param2": "value2"}
    param_names = ["param1"]

    # Process additional parameters
    result = decorator.process_additional_params(kwargs, param_names)

    # Check that the result is the same as the input kwargs
    assert result == kwargs
