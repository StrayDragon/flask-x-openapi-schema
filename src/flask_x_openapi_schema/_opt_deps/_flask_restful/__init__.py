"""Manage optional dependencies imports.

This module provides a centralized way to handle optional dependencies.
It allows the library to work even when optional dependencies are not installed.
"""

from flask_x_openapi_schema._opt_deps._import_utils import import_optional_dependency

flask_restful = import_optional_dependency("flask_restful", "Flask-RESTful integration", raise_error=False)
HAS_FLASK_RESTFUL = flask_restful is not None

if HAS_FLASK_RESTFUL:
    from .real import Api, Resource, reqparse
else:
    from .placeholders import Api, Resource, reqparse

__all__ = [
    # flask-restful
    "HAS_FLASK_RESTFUL",
    "Api",
    "Resource",
    "reqparse",
    # ...
]
