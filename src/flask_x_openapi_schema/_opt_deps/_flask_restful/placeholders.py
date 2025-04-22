"""
Placeholder types for optional dependencies.

This module provides placeholder types for optional dependencies that are not installed.
These placeholders allow the library to be imported and used without the optional dependencies,
but will raise appropriate errors if the actual functionality is used.
"""

from typing import Any, Dict, List, Optional, Union


class MissingDependencyError(ImportError):
    """Error raised when an optional dependency is used but not installed."""

    def __init__(self, dependency: str, feature: str):
        self.dependency = dependency
        self.feature = feature
        message = (
            f"The '{feature}' feature requires the '{dependency}' package, "
            f"which is not installed. Please install it with: "
            f"pip install {dependency} or pip install flask-x-openapi-schema[{dependency}]"
        )
        super().__init__(message)


class Api:
    """Placeholder for flask_restful.Api."""

    def __init__(self, *args, **kwargs):
        raise MissingDependencyError("flask-restful", "Flask-RESTful integration")

    def __getattr__(self, name):
        raise MissingDependencyError("flask-restful", "Flask-RESTful integration")


class Resource:
    """Placeholder for flask_restful.Resource."""

    def __init__(self, *args, **kwargs):
        raise MissingDependencyError("flask-restful", "Flask-RESTful integration")

    def __getattr__(self, name):
        raise MissingDependencyError("flask-restful", "Flask-RESTful integration")


class RequestParser:
    """Placeholder for flask_restful.reqparse.RequestParser."""

    def __init__(self, *args, **kwargs):
        raise MissingDependencyError("flask-restful", "Flask-RESTful integration")

    def add_argument(self, *args, **kwargs):
        raise MissingDependencyError("flask-restful", "Flask-RESTful integration")

    def parse_args(self, *args, **kwargs):
        raise MissingDependencyError("flask-restful", "Flask-RESTful integration")

    def __getattr__(self, name):
        raise MissingDependencyError("flask-restful", "Flask-RESTful integration")


class reqparse:
    """Placeholder for flask_restful.reqparse."""

    RequestParser = RequestParser

    def __getattr__(self, name):
        raise MissingDependencyError("flask-restful", "Flask-RESTful integration")


__all__ = [
    "Api",
    "Resource",
    "reqparse",
    "MissingDependencyError",
]
