"""Tests for placeholder classes to improve coverage."""

import sys
from unittest.mock import patch

import pytest

from flask_x_openapi_schema._opt_deps._import_utils import MissingDependencyError, create_placeholder_class


def test_create_placeholder_class():
    """Test creating a placeholder class."""
    TestClass = create_placeholder_class("TestClass", "test-dependency", "Test feature")

    assert TestClass.__name__ == "TestClass"
    assert TestClass.__qualname__ == "TestClass"
    assert "Placeholder for test-dependency.TestClass" in TestClass.__doc__

    # Test instantiation raises error
    with pytest.raises(MissingDependencyError) as excinfo:
        TestClass()

    assert "test-dependency" in str(excinfo.value)
    assert "Test feature" in str(excinfo.value)

    # Create an instance without raising error for attribute testing
    placeholder_class = type(
        "PlaceholderTest", (), {"__getattr__": lambda self, attr: TestClass.__getattr__(self, attr)}
    )
    placeholder = placeholder_class()

    # Test attribute access raises error
    with pytest.raises(MissingDependencyError) as excinfo:
        placeholder.some_attribute

    assert "test-dependency" in str(excinfo.value)
    assert "Test feature" in str(excinfo.value)


def test_reqparse_class():
    """Test the _reqparse class directly."""
    # Import with patching to ensure it's tested regardless of flask-restful installation
    with patch.dict(sys.modules, {"flask_restful": None}):
        from flask_x_openapi_schema._opt_deps._flask_restful.placeholders import _reqparse, reqparse

        assert isinstance(reqparse, _reqparse)

        # Test __getattr__ raises error
        with pytest.raises(MissingDependencyError) as excinfo:
            reqparse.some_attribute

        assert "flask-restful" in str(excinfo.value)
        assert "Flask-RESTful integration" in str(excinfo.value)
