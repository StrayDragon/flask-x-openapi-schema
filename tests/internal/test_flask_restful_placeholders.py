"""Tests for Flask-RESTful placeholder classes."""

import importlib.util

import pytest

from flask_x_openapi_schema._opt_deps._import_utils import MissingDependencyError

# Check if flask-restful is installed
flask_restful_installed = importlib.util.find_spec("flask_restful") is not None

# Skip all tests if flask-restful is installed
pytestmark = pytest.mark.skipif(
    flask_restful_installed, reason="These tests are only valid when flask-restful is not installed"
)

# Only import placeholders if flask-restful is not installed
if not flask_restful_installed:
    from flask_x_openapi_schema._opt_deps._flask_restful.placeholders import (
        Api,
        Resource,
        reqparse,
    )


def test_api_placeholder_raises_error():
    """Test that Api placeholder raises MissingDependencyError when instantiated."""
    if flask_restful_installed:
        pytest.skip("flask-restful is installed")

    with pytest.raises(MissingDependencyError) as excinfo:
        Api()

    assert "flask-restful" in str(excinfo.value)
    assert "Flask-RESTful integration" in str(excinfo.value)


def test_resource_placeholder_raises_error():
    """Test that Resource placeholder raises MissingDependencyError when instantiated."""
    if flask_restful_installed:
        pytest.skip("flask-restful is installed")

    with pytest.raises(MissingDependencyError) as excinfo:
        Resource()

    assert "flask-restful" in str(excinfo.value)
    assert "Flask-RESTful integration" in str(excinfo.value)


def test_reqparse_placeholder_raises_error():
    """Test that reqparse placeholder raises MissingDependencyError when accessed."""
    if flask_restful_installed:
        pytest.skip("flask-restful is installed")

    with pytest.raises(MissingDependencyError) as excinfo:
        reqparse.add_argument("test")

    assert "flask-restful" in str(excinfo.value)
    assert "Flask-RESTful integration" in str(excinfo.value)


def test_reqparse_requestparser_raises_error():
    """Test that RequestParser placeholder raises MissingDependencyError when instantiated."""
    if flask_restful_installed:
        pytest.skip("flask-restful is installed")

    with pytest.raises(MissingDependencyError) as excinfo:
        reqparse.RequestParser()

    assert "flask-restful" in str(excinfo.value)
    assert "Flask-RESTful integration" in str(excinfo.value)


def test_placeholder_attribute_access_raises_error():
    """Test that accessing attributes on placeholder classes raises MissingDependencyError."""
    if flask_restful_installed:
        pytest.skip("flask-restful is installed")

    # Create a placeholder instance without raising an error
    placeholder_class = type("PlaceholderTest", (), {"__getattr__": lambda self, attr: Api.__getattr__(self, attr)})
    placeholder = placeholder_class()

    with pytest.raises(MissingDependencyError) as excinfo:
        placeholder.some_attribute

    assert "flask-restful" in str(excinfo.value)
    assert "Flask-RESTful integration" in str(excinfo.value)
