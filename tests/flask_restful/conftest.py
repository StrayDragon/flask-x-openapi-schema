"""
Shared fixtures for Flask-RESTful specific tests.
"""

import pytest
from flask import Flask, Blueprint
from flask_restful import Api


@pytest.fixture
def flask_app():
    """Create a Flask app for testing."""
    app = Flask(__name__)
    return app


@pytest.fixture
def flask_client(flask_app):
    """Create a test client for the Flask app."""
    return flask_app.test_client()


@pytest.fixture
def flask_blueprint():
    """Create a Flask blueprint for testing."""
    bp = Blueprint("api", __name__, url_prefix="/api")
    return bp


@pytest.fixture
def flask_api(flask_app):
    """Create a Flask-RESTful API for testing."""
    api = Api(flask_app)
    return api


@pytest.fixture
def flask_blueprint_api(flask_blueprint):
    """Create a Flask-RESTful API with a blueprint for testing."""
    api = Api(flask_blueprint)
    return api, flask_blueprint
