"""Shared fixtures and test helpers for flask-x-openapi-schema tests."""

import pytest
from _pytest.config import Config
from flask import Blueprint, Flask
from flask.views import MethodView
from flask_restful import Api, Resource
from pydantic import BaseModel, Field

# Import the modules that contain doctest examples
from flask_x_openapi_schema import (
    BaseRespModel,
    ConventionalPrefixConfig,
    FileUploadModel,
    I18nStr,
    ImageUploadModel,
    MultipleFileUploadModel,
    OpenAPIMetaResponse,
    OpenAPIMetaResponseItem,
    configure_prefixes,
    get_current_language,
    reset_prefixes,
    set_current_language,
)
from flask_x_openapi_schema.core.cache import clear_all_caches
from flask_x_openapi_schema.x.flask import OpenAPIMethodViewMixin, openapi_metadata
from flask_x_openapi_schema.x.flask_restful import (
    OpenAPIBlueprintMixin,
    OpenAPIIntegrationMixin,
)
from flask_x_openapi_schema.x.flask_restful import (
    openapi_metadata as flask_restful_openapi_metadata,
)

HAS_FLASK_RESTFUL = True


def pytest_configure(config: Config) -> None:
    """Configure pytest for parallel testing.

    This function is called once at the beginning of a test run.
    """
    # Register a custom marker for tests that cannot run in parallel
    config.addinivalue_line("markers", "serial: mark test to run serially (not in parallel with other tests)")


def pytest_configure_node(node) -> None:
    """Configure pytest-xdist for parallel testing.

    This function is called once for each worker at the beginning of a test run.
    """
    # Each worker gets its own random seed
    import random
    import time

    random.seed(int(time.time()) + ord(node.gateway.id[-1]))


def pytest_collection_modifyitems(config: Config, items: list) -> None:
    """Modify test items before execution.

    This function is called after test collection and before test execution.
    """
    if config.getoption("-n", default="1") != "1":
        # Running in parallel mode
        serial_items = []
        parallel_items = []

        for item in items:
            if item.get_closest_marker("serial"):
                serial_items.append(item)
            else:
                parallel_items.append(item)

        # Put serial tests at the beginning to run them first
        items[:] = serial_items + parallel_items


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
