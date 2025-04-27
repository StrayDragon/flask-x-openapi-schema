"""Factory pattern implementation for OpenAPI decorators.

This module implements the Factory pattern for creating OpenAPI decorators.
It provides a base factory class and concrete factory implementations for different frameworks.

Design Patterns:
    - Abstract Factory Pattern: The OpenAPIDecoratorFactory defines an interface for
      creating OpenAPI decorators, with concrete factories for different frameworks.
    - Factory Method Pattern: Each concrete factory implements the create_decorator method
      to instantiate the appropriate decorator for its framework.
    - Dependency Injection: Framework-specific dependencies are injected at creation time,
      allowing for loose coupling between components.

Benefits:
    - Extensibility: New frameworks can be supported by adding new factory implementations
      without modifying existing code.
    - Encapsulation: The creation logic for decorators is encapsulated within factories,
      hiding implementation details from clients.
    - Testability: Factories can be mocked or replaced in tests to isolate components.

Usage:
    ```python
    # Create a factory for Flask
    factory = create_decorator_factory("flask")

    # Create a decorator with specific options
    decorator = factory.create_decorator(
        summary="My API endpoint", description="Detailed description", tags=["api", "v1"]
    )


    # Apply the decorator to a function
    @decorator
    def my_endpoint():
        return {"message": "Hello, world!"}
    ```
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, TypeVar, cast

from flask_x_openapi_schema.core.config import ConventionalPrefixConfig
from flask_x_openapi_schema.i18n.i18n_string import I18nStr
from flask_x_openapi_schema.models.responses import OpenAPIMetaResponse

# Type variable for decorated functions
F = TypeVar("F", bound=Callable[..., Any])


class OpenAPIDecoratorFactory(ABC):
    """Abstract factory for creating OpenAPI decorators."""

    @abstractmethod
    def create_decorator(
        self,
        summary: str | I18nStr | None = None,
        description: str | I18nStr | None = None,
        tags: list[str] | None = None,
        operation_id: str | None = None,
        responses: OpenAPIMetaResponse | None = None,
        deprecated: bool = False,
        security: list[dict[str, list[str]]] | None = None,
        external_docs: dict[str, str] | None = None,
        language: str | None = None,
        prefix_config: ConventionalPrefixConfig | None = None,
    ) -> Callable[[F], F]:
        """Create an OpenAPI decorator.

        Args:
            summary: Operation summary
            description: Operation description
            tags: Operation tags
            operation_id: Operation ID
            responses: Response models
            deprecated: Whether the operation is deprecated
            security: Security requirements
            external_docs: External documentation
            language: Language for i18n strings
            prefix_config: Parameter prefix configuration

        Returns:
            A decorator function

        """


class FlaskOpenAPIDecoratorFactory(OpenAPIDecoratorFactory):
    """Factory for creating Flask OpenAPI decorators."""

    def create_decorator(
        self,
        summary: str | I18nStr | None = None,
        description: str | I18nStr | None = None,
        tags: list[str] | None = None,
        operation_id: str | None = None,
        responses: OpenAPIMetaResponse | None = None,
        deprecated: bool = False,
        security: list[dict[str, list[str]]] | None = None,
        external_docs: dict[str, str] | None = None,
        language: str | None = None,
        prefix_config: ConventionalPrefixConfig | None = None,
    ) -> Callable[[F], F]:
        """Create a Flask OpenAPI decorator.

        Args:
            summary: Operation summary
            description: Operation description
            tags: Operation tags
            operation_id: Operation ID
            responses: Response models
            deprecated: Whether the operation is deprecated
            security: Security requirements
            external_docs: External documentation
            language: Language for i18n strings
            prefix_config: Parameter prefix configuration

        Returns:
            A decorator function for Flask endpoints

        """
        # Import here to avoid circular imports
        from flask_x_openapi_schema.x.flask.decorators import FlaskOpenAPIDecorator

        # Create the decorator directly
        decorator = FlaskOpenAPIDecorator(
            summary=summary,
            description=description,
            tags=tags,
            operation_id=operation_id,
            responses=responses,
            deprecated=deprecated,
            security=security,
            external_docs=external_docs,
            language=language,
            prefix_config=prefix_config,
        )

        return cast("Callable[[F], F]", decorator)


class FlaskRestfulOpenAPIDecoratorFactory(OpenAPIDecoratorFactory):
    """Factory for creating Flask-RESTful OpenAPI decorators."""

    def create_decorator(
        self,
        summary: str | I18nStr | None = None,
        description: str | I18nStr | None = None,
        tags: list[str] | None = None,
        operation_id: str | None = None,
        responses: OpenAPIMetaResponse | None = None,
        deprecated: bool = False,
        security: list[dict[str, list[str]]] | None = None,
        external_docs: dict[str, str] | None = None,
        language: str | None = None,
        prefix_config: ConventionalPrefixConfig | None = None,
    ) -> Callable[[F], F]:
        """Create a Flask-RESTful OpenAPI decorator.

        Args:
            summary: Operation summary
            description: Operation description
            tags: Operation tags
            operation_id: Operation ID
            responses: Response models
            deprecated: Whether the operation is deprecated
            security: Security requirements
            external_docs: External documentation
            language: Language for i18n strings
            prefix_config: Parameter prefix configuration

        Returns:
            A decorator function for Flask-RESTful endpoints

        """
        # Import here to avoid circular imports
        from flask_x_openapi_schema.x.flask_restful.decorators import FlaskRestfulOpenAPIDecorator

        # Create the decorator directly
        decorator = FlaskRestfulOpenAPIDecorator(
            summary=summary,
            description=description,
            tags=tags,
            operation_id=operation_id,
            responses=responses,
            deprecated=deprecated,
            security=security,
            external_docs=external_docs,
            language=language,
            prefix_config=prefix_config,
        )

        return cast("Callable[[F], F]", decorator)


def create_decorator_factory(framework: str) -> OpenAPIDecoratorFactory:
    """Create a decorator factory for the specified framework.

    Args:
        framework: The framework to create a factory for ('flask' or 'flask_restful')

    Returns:
        A decorator factory instance

    Raises:
        ValueError: If the framework is not supported

    """
    if framework == "flask":
        return FlaskOpenAPIDecoratorFactory()
    if framework == "flask_restful":
        return FlaskRestfulOpenAPIDecoratorFactory()
    msg = f"Unsupported framework: {framework}"
    raise ValueError(msg)
