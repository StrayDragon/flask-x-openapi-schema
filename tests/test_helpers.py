"""Helper functions and classes for testing flask-x-openapi-schema."""

import contextlib

from flask import Flask


@contextlib.contextmanager
def flask_request_context():
    """Create a Flask request context for testing."""
    app = Flask(__name__)
    with app.app_context():
        yield app
