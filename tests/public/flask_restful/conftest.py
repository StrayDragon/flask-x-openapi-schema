"""Shared fixtures for Flask-RESTful specific tests."""

import pytest
from flask import Blueprint, Flask

from flask_x_openapi_schema._opt_deps._flask_restful import Api


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


@pytest.fixture
def flask_api(flask_app):
    """Create a Flask-RESTful API for testing."""
    return Api(flask_app)


@pytest.fixture
def flask_blueprint_api(flask_blueprint):
    """Create a Flask-RESTful API with a blueprint for testing."""
    api = Api(flask_blueprint)
    return api, flask_blueprint
