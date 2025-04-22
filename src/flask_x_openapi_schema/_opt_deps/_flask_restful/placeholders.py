"""
Placeholder types for optional dependencies.

This module provides placeholder types for optional dependencies that are not installed.
These placeholders allow the library to be imported and used without the optional dependencies,
but will raise appropriate errors if the actual functionality is used.
"""

# No typing imports needed

from .._import_utils import MissingDependencyError, create_placeholder_class

# Create placeholder classes for flask-restful components
Api = create_placeholder_class("Api", "flask-restful", "Flask-RESTful integration")
Resource = create_placeholder_class(
    "Resource", "flask-restful", "Flask-RESTful integration"
)

# Create RequestParser class with specific methods
RequestParser = create_placeholder_class(
    "RequestParser", "flask-restful", "Flask-RESTful integration"
)


# Create reqparse module-like class
class reqparse:
    """Placeholder for flask_restful.reqparse."""

    RequestParser = RequestParser

    def __getattr__(self, name):
        raise MissingDependencyError("flask-restful", "Flask-RESTful integration")


# Create an instance of reqparse
reqparse = reqparse()

__all__ = [
    "Api",
    "Resource",
    "reqparse",
    "MissingDependencyError",
]
