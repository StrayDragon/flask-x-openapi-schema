"""
Decorators for adding OpenAPI metadata to API endpoints.
"""

from .base import (
    ConventionalPrefixConfig,
    configure_prefixes,
    reset_prefixes,
    GLOBAL_CONFIG_HOLDER,
)
from .flask import openapi_metadata as flask_openapi_metadata
from .flask_restful import openapi_metadata as restful_openapi_metadata

# Import detection utilities
import inspect
from typing import Any, Callable, TypeVar

# Type variables
T = TypeVar('T')


def openapi_metadata(*args, **kwargs):
    """
    Smart decorator that automatically chooses between Flask and Flask-RESTful implementations.

    This decorator detects whether it's being applied to a Flask-RESTful Resource method
    or a Flask MethodView method, and uses the appropriate implementation.

    Usage is identical for both Flask and Flask-RESTful:

    @openapi_metadata(summary="My API endpoint", ...)
    def get(self):
        ...
    """
    # Handle both @openapi_metadata and @openapi_metadata() usage
    if len(args) == 1 and callable(args[0]) and not kwargs:
        # Called as @openapi_metadata without arguments
        func = args[0]
        return _choose_decorator(func)(func)
    else:
        # Called as @openapi_metadata(...) with arguments
        def decorator(func):
            return _choose_decorator(func, **kwargs)(func)
        return decorator


def _choose_decorator(func: Callable[..., Any], **kwargs) -> Callable[[T], T]:
    """
    Choose the appropriate decorator based on the function's class.

    Args:
        func: The function being decorated
        **kwargs: Decorator arguments

    Returns:
        The appropriate decorator function
    """
    # Try to get the class that defines this method
    try:
        if hasattr(func, "__qualname__") and "." in func.__qualname__:
            class_name = func.__qualname__.split(".")[0]
            module = inspect.getmodule(func)
            if module and hasattr(module, class_name):
                cls = getattr(module, class_name)

                # Check if it's a Flask-RESTful Resource
                if hasattr(cls, "__mro__"):
                    for base in cls.__mro__:
                        if base.__name__ == "Resource" and base.__module__.startswith("flask_restful"):
                            return lambda f: restful_openapi_metadata(**kwargs)(f)
    except Exception:
        # If any error occurs during detection, default to Flask implementation
        pass

    # Default to Flask implementation
    return lambda f: flask_openapi_metadata(**kwargs)(f)

__all__ = [
    "ConventionalPrefixConfig",
    "configure_prefixes",
    "reset_prefixes",
    "GLOBAL_CONFIG_HOLDER",
    "openapi_metadata",
]