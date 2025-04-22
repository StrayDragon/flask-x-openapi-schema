"""
Manage optional dependencies imports.

This module provides a centralized way to handle optional dependencies.
It allows the library to work even when optional dependencies are not installed.
"""

from typing import Any, Dict, List, Optional, Set, Type, Union

# Flag to indicate if flask-restful is installed
HAS_FLASK_RESTFUL = False

try:
    import flask_x_openapi_schema._opt_deps._flask_restful.real as real  # noqa: F401
    HAS_FLASK_RESTFUL = True
except ImportError:
    pass

# Re-export flask-restful components if available
if HAS_FLASK_RESTFUL:
    from .real import Api, Resource, reqparse
else:
    # Provide placeholder types when flask-restful is not installed
    from .placeholders import Api, Resource, reqparse

__all__ = [
    # Flags
    "HAS_FLASK_RESTFUL",
    # Flask-RESTful components
    "Api",
    "Resource",
    "reqparse",
]
