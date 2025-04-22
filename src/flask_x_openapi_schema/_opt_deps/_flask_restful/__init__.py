"""
Manage optional dependencies imports.

This module provides a centralized way to handle optional dependencies.
It allows the library to work even when optional dependencies are not installed.
"""

from .._import_utils import import_optional_dependency

# 检测 flask_restful 是否已安装
flask_restful = import_optional_dependency(
    "flask_restful", "Flask-RESTful integration", raise_error=False
)
HAS_FLASK_RESTFUL = flask_restful is not None

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
