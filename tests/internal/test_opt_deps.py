"""Tests for optional dependencies handling.

This module tests the internal implementation of optional dependencies handling.
"""

import pytest

from flask_x_openapi_schema._opt_deps import (
    MissingDependencyError,
    create_placeholder_class,
    import_optional_dependency,
)
from flask_x_openapi_schema._opt_deps._flask_restful import (
    HAS_FLASK_RESTFUL,
    Api,
    Resource,
    reqparse,
)


def test_import_optional_dependency():
    """Test import_optional_dependency function."""
    # Test importing an existing module
    os = import_optional_dependency("os", "testing", raise_error=True)
    assert os is not None

    # Test importing a non-existing module with raise_error=False
    non_existent = import_optional_dependency("non_existent_module", "testing", raise_error=False)
    assert non_existent is None

    # Test importing a non-existing module with raise_error=True
    with pytest.raises(MissingDependencyError) as excinfo:
        import_optional_dependency("non_existent_module", "testing", raise_error=True)
    assert "testing" in str(excinfo.value)
    assert "non_existent_module" in str(excinfo.value)


def test_create_placeholder_class():
    """Test create_placeholder_class function."""
    TestClass = create_placeholder_class("TestClass", "test-dep", "testing")

    # Check class name and docstring
    assert TestClass.__name__ == "TestClass"
    assert "test-dep.TestClass" in TestClass.__doc__

    # Check that instantiating raises the correct error
    with pytest.raises(MissingDependencyError) as excinfo:
        TestClass()
    assert "testing" in str(excinfo.value)
    assert "test-dep" in str(excinfo.value)

    # Check that accessing attributes raises the correct error
    instance = object.__new__(TestClass)
    with pytest.raises(MissingDependencyError) as excinfo:
        instance.some_attribute
    assert "testing" in str(excinfo.value)
    assert "test-dep" in str(excinfo.value)


def test_flask_restful_imports():
    """Test Flask-RESTful imports."""
    if HAS_FLASK_RESTFUL:
        # If Flask-RESTful is installed, these should be the real classes
        assert hasattr(Api, "__module__")
        assert hasattr(Resource, "__module__")
        assert hasattr(reqparse, "RequestParser")
    else:
        # If Flask-RESTful is not installed, these should be placeholder classes
        with pytest.raises(MissingDependencyError) as excinfo:
            Api()
        assert "Flask-RESTful integration" in str(excinfo.value)
        assert "flask-restful" in str(excinfo.value)

        with pytest.raises(MissingDependencyError) as excinfo:
            Resource()
        assert "Flask-RESTful integration" in str(excinfo.value)
        assert "flask-restful" in str(excinfo.value)

        with pytest.raises(MissingDependencyError) as excinfo:
            reqparse.RequestParser()
        assert "Flask-RESTful integration" in str(excinfo.value)
        assert "flask-restful" in str(excinfo.value)
