"""Shared fixtures for Flask-specific tests."""

import pytest
from flask import Blueprint, Flask


@pytest.fixture
def flask_app():
    """Create a Flask app for testing."""
    return Flask(__name__)


@pytest.fixture
def flask_client(flask_app):
    """Create a test client for the Flask app."""
    return flask_app.test_client()


@pytest.fixture
def flask_blueprint():
    """Create a Flask blueprint for testing."""
    return Blueprint("api", __name__, url_prefix="/api")
