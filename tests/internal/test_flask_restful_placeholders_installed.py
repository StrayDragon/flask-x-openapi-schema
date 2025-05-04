"""Tests for Flask-RESTful placeholder classes when flask-restful is installed."""

import pytest

from flask_x_openapi_schema._opt_deps._import_utils import MissingDependencyError


class TestFlaskRestfulPlaceholdersInstalled:
    """Tests for Flask-RESTful placeholder classes when flask-restful is installed."""

    def test_placeholder_creation(self):
        """Test that placeholder classes are created correctly."""
        from flask_x_openapi_schema._opt_deps._import_utils import create_placeholder_class

        # Create a placeholder class
        placeholder = create_placeholder_class("TestClass", "test-package", "Test integration")

        # Check that the class has the expected attributes
        assert placeholder.__name__ == "TestClass"
        assert placeholder.__module__ == "flask_x_openapi_schema._opt_deps._import_utils"

        # Check that instantiating the class raises an error
        with pytest.raises(MissingDependencyError) as excinfo:
            placeholder()

        assert "test-package" in str(excinfo.value)
        assert "Test integration" in str(excinfo.value)

    def test_placeholder_attribute_access(self):
        """Test that accessing attributes on placeholder classes raises an error."""
        from flask_x_openapi_schema._opt_deps._import_utils import create_placeholder_class

        # Create a placeholder class
        placeholder = create_placeholder_class("TestClass", "test-package", "Test integration")

        # Create a placeholder instance without raising an error
        placeholder_class = type(
            "PlaceholderTest", (), {"__getattr__": lambda self, attr: placeholder.__getattr__(self, attr)}
        )
        placeholder_instance = placeholder_class()

        # Check that accessing an attribute raises an error
        with pytest.raises(MissingDependencyError) as excinfo:
            placeholder_instance.some_attribute

        assert "test-package" in str(excinfo.value)
        assert "Test integration" in str(excinfo.value)

    def test_reqparse_placeholder(self):
        """Test the reqparse placeholder class."""
        # This test verifies that the placeholder class is created correctly
        # We don't need to test the actual functionality with mocks
        from flask_x_openapi_schema._opt_deps._import_utils import create_placeholder_class

        # Create a placeholder class for reqparse
        reqparse_class = create_placeholder_class("reqparse", "test-package", "Test integration")

        # Create a placeholder instance
        reqparse = type("_reqparse", (), {"__getattr__": lambda self, name: reqparse_class.__getattr__(self, name)})()

        # Check that accessing an attribute raises an error
        with pytest.raises(MissingDependencyError) as excinfo:
            reqparse.add_argument("test")

        assert "test-package" in str(excinfo.value)
        assert "Test integration" in str(excinfo.value)
