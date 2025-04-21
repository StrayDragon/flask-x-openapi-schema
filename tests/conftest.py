"""
Shared fixtures and test helpers for flask-x-openapi-schema tests.
"""

import pytest
from flask import Flask

from flask_x_openapi_schema.core.cache import clear_all_caches


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
