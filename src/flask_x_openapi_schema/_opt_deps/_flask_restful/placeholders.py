"""Placeholder types for optional dependencies.

This module provides placeholder types for optional dependencies that are not installed.
These placeholders allow the library to be imported and used without the optional dependencies,
but will raise appropriate errors if the actual functionality is used.
"""

from flask_x_openapi_schema._opt_deps._import_utils import MissingDependencyError, create_placeholder_class

Api = create_placeholder_class("Api", "flask-restful", "Flask-RESTful integration")
Resource = create_placeholder_class("Resource", "flask-restful", "Flask-RESTful integration")
RequestParser = create_placeholder_class("RequestParser", "flask-restful", "Flask-RESTful integration")


class _reqparse:  # noqa: N801
    """Placeholder for flask_restful.reqparse."""

    RequestParser = RequestParser

    def __getattr__(self, name):  # noqa: ANN001, ANN204
        msg = "flask-restful"
        raise MissingDependencyError(msg, "Flask-RESTful integration")


reqparse = _reqparse()

__all__ = [
    "Api",
    "MissingDependencyError",
    "Resource",
    "reqparse",
]
