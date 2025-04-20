"""
Shared fixtures and test helpers for flask-x-openapi-schema tests.
"""

import pytest
from flask import Flask


@pytest.fixture
def app():
    """Create a Flask app for testing."""
    app = Flask(__name__)
    return app


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()
