"""
Re-export flask-restful components.

This module re-exports the flask-restful components that are used by the library.
It should only be imported when flask-restful is installed.
"""

from flask_restful import Api, Resource, reqparse

__all__ = [
    "Api",
    "Resource",
    "reqparse",
]
