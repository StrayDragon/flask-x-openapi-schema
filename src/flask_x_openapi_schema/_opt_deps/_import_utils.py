"""
Utility functions for managing optional dependencies.

This module provides utility functions for handling optional dependencies in a consistent way.
It is inspired by the approach used in popular libraries like Pandas and SQLAlchemy.
"""

import importlib
from typing import Any, Optional, Type


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


def import_optional_dependency(
    name: str,
    feature: str,
    raise_error: bool = True,
) -> Optional[Any]:
    """
    Import an optional dependency.

    Parameters
    ----------
    name : str
        The name of the dependency to import.
    feature : str
        The name of the feature that requires this dependency.
    raise_error : bool, default True
        If True, raise MissingDependencyError if the dependency is not installed.
        If False, return None if the dependency is not installed.

    Returns
    -------
    module : Optional[Any]
        The imported module if the dependency is installed, None otherwise.

    Raises
    ------
    MissingDependencyError
        If the dependency is not installed and raise_error is True.
    """
    try:
        return importlib.import_module(name)
    except ImportError:
        if raise_error:
            raise MissingDependencyError(name, feature)
        return None


def create_placeholder_class(name: str, dependency: str, feature: str) -> Type:
    """
    Create a placeholder class for an optional dependency.

    Parameters
    ----------
    name : str
        The name of the class to create.
    dependency : str
        The name of the dependency that provides the real implementation.
    feature : str
        The name of the feature that requires this dependency.

    Returns
    -------
    cls : Type
        A placeholder class that raises MissingDependencyError when instantiated or accessed.
    """

    class PlaceholderClass:
        """Placeholder for an optional dependency."""

        def __init__(self, *args, **kwargs):
            raise MissingDependencyError(dependency, feature)

        def __getattr__(self, attr):
            raise MissingDependencyError(dependency, feature)

    PlaceholderClass.__name__ = name
    PlaceholderClass.__qualname__ = name
    PlaceholderClass.__doc__ = f"Placeholder for {dependency}.{name}"

    return PlaceholderClass
