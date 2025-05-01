"""Utility functions for managing optional dependencies.

This module provides utility functions for handling optional dependencies in a consistent way.
It is inspired by the approach used in popular libraries like Pandas and SQLAlchemy.

The module includes functions for importing optional dependencies and creating placeholder
classes that raise appropriate errors when optional dependencies are missing.
"""

import importlib
from typing import Any


class MissingDependencyError(ImportError):
    """Error raised when an optional dependency is used but not installed.

    This exception provides a helpful error message that includes the missing dependency
    and the feature that requires it, along with installation instructions.

    Attributes:
        dependency: The name of the missing dependency package.
        feature: The name of the feature that requires the dependency.

    """

    def __init__(self, dependency: str, feature: str) -> None:
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
) -> Any | None:
    """Import an optional dependency.

    Attempts to import a module that is an optional dependency. If the module
    cannot be imported, either raises an informative error or returns None.

    Args:
        name: The name of the dependency to import.
        feature: The name of the feature that requires this dependency.
        raise_error: If True, raise MissingDependencyError if the dependency
            is not installed. If False, return None if the dependency is not installed.
            Defaults to True.

    Returns:
        The imported module if the dependency is installed, None otherwise.

    Raises:
        MissingDependencyError: If the dependency is not installed and raise_error is True.

    Examples:
        >>> # Import flask_restful for RESTful API support
        >>> restful = import_optional_dependency("flask_restful", "RESTful API")
        >>> # Import with fallback to None if not installed
        >>> mdx = import_optional_dependency("mdx_math", "Math rendering", raise_error=False)

    """
    try:
        return importlib.import_module(name)
    except ImportError as e:
        if raise_error:
            raise MissingDependencyError(name, feature) from e
        return None


def create_placeholder_class(name: str, dependency: str, feature: str) -> type:
    """Create a placeholder class for an optional dependency.

    Creates a class that raises an informative error when instantiated or when any
    attribute is accessed. This is useful for providing clear error messages when
    optional dependencies are used but not installed.

    Args:
        name: The name of the class to create.
        dependency: The name of the dependency that provides the real implementation.
        feature: The name of the feature that requires this dependency.

    Returns:
        A placeholder class that raises MissingDependencyError when instantiated or
        when any attribute is accessed.

    Examples:
        >>> # Create a placeholder for a missing SQLAlchemy model
        >>> Model = create_placeholder_class("Model", "sqlalchemy", "ORM features")
        >>> # Attempting to use the placeholder will raise an informative error
        >>> # model = Model()  # This would raise MissingDependencyError

    """

    class PlaceholderClass:
        """Placeholder for an optional dependency.

        This class raises MissingDependencyError when instantiated or when any
        attribute is accessed, providing a clear error message about the missing
        dependency and how to install it.
        """

        def __init__(self, *args, **kwargs) -> None:  # noqa: ARG002
            raise MissingDependencyError(dependency, feature)

        def __getattr__(self, attr):  # noqa: ANN001, ANN204
            raise MissingDependencyError(dependency, feature)

    PlaceholderClass.__name__ = name
    PlaceholderClass.__qualname__ = name
    PlaceholderClass.__doc__ = f"Placeholder for {dependency}.{name}"

    return PlaceholderClass
