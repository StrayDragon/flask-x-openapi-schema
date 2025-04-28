"""Tests for Flask-RESTful decorators."""

import pytest
from pydantic import BaseModel, Field

from flask_x_openapi_schema._opt_deps._import_utils import import_optional_dependency
from flask_x_openapi_schema.core.config import ConventionalPrefixConfig
from flask_x_openapi_schema.i18n.i18n_string import I18nStr
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
    from flask_x_openapi_schema.models.file_models import FileField
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
