"""
Shared fixtures and test helpers for flask-x-openapi-schema tests.
"""

import pytest
from flask import Flask, Blueprint
from flask.views import MethodView
from pydantic import BaseModel, Field

from flask_x_openapi_schema.core.cache import clear_all_caches

# Import the modules that contain doctest examples
from flask_x_openapi_schema import (
    ConventionalPrefixConfig,
    configure_prefixes,
    reset_prefixes,
    I18nStr,
    set_current_language,
    get_current_language,
    OpenAPIMetaResponse,
    OpenAPIMetaResponseItem,
    BaseRespModel,
    FileUploadModel,
    ImageUploadModel,
    MultipleFileUploadModel,
)
from flask_x_openapi_schema.x.flask import openapi_metadata
from flask_x_openapi_schema.x.flask import OpenAPIMethodViewMixin
from flask_x_openapi_schema.x.flask_restful import (
    openapi_metadata as flask_restful_openapi_metadata,
    OpenAPIIntegrationMixin,
    OpenAPIBlueprintMixin,
)

from flask_restful import Resource, Api

HAS_FLASK_RESTFUL = True


@pytest.fixture(autouse=True)
def clear_caches():
    """Clear all caches before and after each test."""
    # Clear caches before test
    clear_all_caches()

    # Run the test
    yield

    # Clear caches after test
    clear_all_caches()

    # Import and reset any module-level variables that might persist
    from importlib import reload
    from flask_x_openapi_schema.core import cache

    reload(cache)


@pytest.fixture
def app():
    """Create a Flask app for testing."""
    app = Flask(__name__)
    return app


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()


@pytest.fixture(autouse=True)
def add_imports(doctest_namespace):
    """Add imports to the doctest namespace."""
    # Add Flask imports
    doctest_namespace["Flask"] = Flask
    doctest_namespace["Blueprint"] = Blueprint
    doctest_namespace["MethodView"] = MethodView

    # Add Flask-RESTful imports
    doctest_namespace["Resource"] = Resource
    doctest_namespace["Api"] = Api

    # Add Pydantic imports
    doctest_namespace["BaseModel"] = BaseModel
    doctest_namespace["Field"] = Field

    # Add flask_x_openapi_schema imports
    doctest_namespace["ConventionalPrefixConfig"] = ConventionalPrefixConfig
    doctest_namespace["configure_prefixes"] = configure_prefixes
    doctest_namespace["reset_prefixes"] = reset_prefixes
    doctest_namespace["I18nStr"] = I18nStr
    doctest_namespace["set_current_language"] = set_current_language
    doctest_namespace["get_current_language"] = get_current_language
    doctest_namespace["OpenAPIMetaResponse"] = OpenAPIMetaResponse
    doctest_namespace["OpenAPIMetaResponseItem"] = OpenAPIMetaResponseItem
    doctest_namespace["BaseRespModel"] = BaseRespModel
    doctest_namespace["FileUploadModel"] = FileUploadModel
    doctest_namespace["ImageUploadModel"] = ImageUploadModel
    doctest_namespace["MultipleFileUploadModel"] = MultipleFileUploadModel

    # Add flask_x_openapi_schema.x.flask imports
    doctest_namespace["openapi_metadata"] = openapi_metadata
    doctest_namespace["OpenAPIMethodViewMixin"] = OpenAPIMethodViewMixin

    # Add flask_x_openapi_schema.x.flask_restful imports
    doctest_namespace["flask_restful_openapi_metadata"] = flask_restful_openapi_metadata
    doctest_namespace["OpenAPIIntegrationMixin"] = OpenAPIIntegrationMixin
    doctest_namespace["OpenAPIBlueprintMixin"] = OpenAPIBlueprintMixin
