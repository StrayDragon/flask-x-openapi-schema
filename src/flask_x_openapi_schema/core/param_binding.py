"""Parameter binding strategies for OpenAPI decorators.

This module implements the Strategy pattern for parameter binding in OpenAPI decorators.
Each strategy handles a specific type of parameter binding (request body, query, path, file).

The module provides a unified way to extract and validate parameters from different sources
in HTTP requests, using Pydantic models for validation and type conversion.

Design Patterns:
    Strategy Pattern:
        Used to encapsulate different parameter binding algorithms and make them
        interchangeable. Each strategy implements a common interface
        (ParameterBindingStrategy) with a bind_parameter method.

    Factory Pattern:
        The ParameterBindingStrategyFactory creates appropriate binding strategies
        based on parameter type, decoupling client code from concrete strategy
        implementations.

    Dependency Injection:
        Framework-specific decorators are injected into strategies to handle
        framework-specific binding logic.

Thread Safety:
    All binding strategies are designed to be thread-safe, with no shared mutable state.
    Any caching is handled through thread-safe cache implementations.

Examples:
    Creating and using a request body binding strategy:

    ```python
    from flask_x_openapi_schema.core.param_binding import ParameterBindingStrategyFactory
    from pydantic import BaseModel


    class UserModel(BaseModel):
        name: str
        age: int


    # Create a body binding strategy
    strategy = ParameterBindingStrategyFactory.create_strategy("body")

    # Use the strategy to bind parameters
    kwargs = {}
    kwargs = strategy.bind_parameter(
        param_name="_x_body", model=UserModel, kwargs=kwargs, framework_decorator=flask_decorator
    )
    ```

"""

import contextlib
import json
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, TypeVar

from flask import request
from pydantic import BaseModel

from flask_x_openapi_schema.core.config import ConventionalPrefixConfig

logger = logging.getLogger(__name__)


def preprocess_request_data(data: dict[str, Any], model: type[Any]) -> dict[str, Any]:
    """Preprocess request data before validation.

    This function handles special cases like converting string representations of lists
    to actual lists, which is common when receiving data from form submissions.

    Args:
        data: The request data to preprocess
        model: The model class that will be used for validation

    Returns:
        The preprocessed data

    """
    if not isinstance(model, type) or not issubclass(model, BaseModel):
        return data

    processed_data = data.copy()

    model_fields = getattr(model, "model_fields", {})

    for field_name, field_value in data.items():
        if field_name not in model_fields:
            continue

        field_info = model_fields[field_name]
        field_type = field_info.annotation

        if (
            hasattr(field_type, "__origin__")
            and field_type.__origin__ is list
            and isinstance(field_value, str)
            and field_value
        ):
            try:
                parsed_value = json.loads(field_value)
                if isinstance(parsed_value, list):
                    processed_data[field_name] = parsed_value
                else:
                    processed_data[field_name] = [parsed_value]
            except json.JSONDecodeError:
                processed_data[field_name] = [field_value]

        elif (
            hasattr(field_type, "__origin__")
            and field_type.__origin__ is list
            and not isinstance(field_value, list)
            and field_value is not None
        ):
            processed_data[field_name] = [field_value]

    return processed_data


T = TypeVar("T")


class ParameterBindingStrategy(ABC):
    """Abstract base class for parameter binding strategies."""

    @abstractmethod
    def bind_parameter(
        self,
        param_name: str,
        model: type[BaseModel],
        kwargs: dict[str, Any],
        framework_decorator: Any,
    ) -> dict[str, Any]:
        """Bind a parameter to a function argument.

        Args:
            param_name: The parameter name to bind the model instance to
            model: The Pydantic model class to use for validation
            kwargs: The keyword arguments to update
            framework_decorator: The framework-specific decorator instance

        Returns:
            Updated kwargs dictionary with the model instance

        """


class RequestBodyBindingStrategy(ParameterBindingStrategy):
    """Strategy for binding request body parameters."""

    def bind_parameter(
        self,
        param_name: str,
        model: type[BaseModel],
        kwargs: dict[str, Any],
        framework_decorator: Any,
    ) -> dict[str, Any]:
        """Bind a request body parameter to a function argument.

        Args:
            param_name: The parameter name to bind the model instance to
            model: The Pydantic model class to use for validation
            kwargs: The keyword arguments to update
            framework_decorator: The framework-specific decorator instance

        Returns:
            Updated kwargs dictionary with the model instance

        """
        return framework_decorator.process_request_body(param_name, model, kwargs)


class QueryParameterBindingStrategy(ParameterBindingStrategy):
    """Strategy for binding query parameters."""

    def bind_parameter(
        self,
        param_name: str,
        model: type[BaseModel],
        kwargs: dict[str, Any],
        framework_decorator: Any,
    ) -> dict[str, Any]:
        """Bind query parameters to a function argument.

        Args:
            param_name: The parameter name to bind the model instance to
            model: The Pydantic model class to use for validation
            kwargs: The keyword arguments to update
            framework_decorator: The framework-specific decorator instance

        Returns:
            Updated kwargs dictionary with the model instance

        """
        return framework_decorator.process_query_params(param_name, model, kwargs)


class PathParameterBindingStrategy(ParameterBindingStrategy):
    """Strategy for binding path parameters."""

    def __init__(self, prefix_config: ConventionalPrefixConfig | None = None) -> None:
        """Initialize the strategy with prefix configuration.

        Args:
            prefix_config: Optional configuration object with custom prefixes

        """
        self.prefix_config = prefix_config
        from flask_x_openapi_schema.core.cache import get_parameter_prefixes

        _, _, path_prefix, _ = get_parameter_prefixes(prefix_config)
        self.path_prefix_len = len(path_prefix) + 1

    def bind_parameter(
        self,
        param_name: str,
        _model: type[BaseModel],
        kwargs: dict[str, Any],
        _framework_decorator: Any,
    ) -> dict[str, Any]:
        """Bind path parameters to a function argument.

        Args:
            param_name: The parameter name to bind the value to
            model: Not used for path parameters
            kwargs: The keyword arguments to update
            framework_decorator: Not used for path parameters

        Returns:
            Updated kwargs dictionary with the path parameter value

        """
        param_suffix = param_name[self.path_prefix_len :]
        if param_suffix in kwargs:
            kwargs[param_name] = kwargs[param_suffix]
        return kwargs


class FileParameterBindingStrategy(ParameterBindingStrategy):
    """Strategy for binding file parameters."""

    def __init__(
        self, prefix_config: ConventionalPrefixConfig | None = None, type_hints: dict[str, Any] | None = None
    ) -> None:
        """Initialize the strategy with prefix configuration.

        Args:
            prefix_config: Optional configuration object with custom prefixes
            type_hints: Function type hints

        """
        self.prefix_config = prefix_config
        self.type_hints = type_hints or {}
        from flask_x_openapi_schema.core.cache import get_parameter_prefixes

        _, _, _, file_prefix = get_parameter_prefixes(prefix_config)
        self.file_prefix_len = len(file_prefix) + 1

    def bind_parameter(
        self,
        param_name: str,
        _model: type[BaseModel],
        kwargs: dict[str, Any],
        _framework_decorator: Any,
    ) -> dict[str, Any]:
        """Bind file parameters to a function argument.

        Args:
            param_name: The parameter name to bind the file to
            model: Not used directly
            kwargs: The keyword arguments to update
            framework_decorator: Not used for file parameters

        Returns:
            Updated kwargs dictionary with the file parameter value

        """
        param_type = self.type_hints.get(param_name)

        is_pydantic_model = (
            param_type
            and isinstance(param_type, type)
            and issubclass(param_type, BaseModel)
            and hasattr(param_type, "model_fields")
            and "file" in param_type.model_fields
        )

        param_suffix = param_name[self.file_prefix_len :]

        if param_suffix == "":
            file_param_name = "file"

        elif param_suffix.startswith("_"):
            file_param_name = param_suffix[1:]
        else:
            file_param_name = param_suffix

        if file_param_name in request.files:
            file_obj = request.files[file_param_name]
            if is_pydantic_model:
                model_data = dict(request.form.items())

                model_data["file"] = file_obj

                kwargs[param_name] = param_type(**model_data)
            else:
                kwargs[param_name] = file_obj

        elif "file" in request.files:
            file_obj = request.files["file"]
            if is_pydantic_model:
                model_data = {}

                for field_name, field_value in request.form.items():
                    model_data[field_name] = field_value

                model_data["file"] = file_obj

                kwargs[param_name] = param_type(**model_data)
            else:
                kwargs[param_name] = file_obj

        elif len(request.files) == 1:
            file_obj = next(iter(request.files.values()))
            if is_pydantic_model:
                model_data = {}

                for field_name, field_value in request.form.items():
                    model_data[field_name] = field_value

                model_data["file"] = file_obj

                kwargs[param_name] = param_type(**model_data)
            else:
                kwargs[param_name] = file_obj

        return kwargs


class ParameterBindingStrategyFactory:
    """Factory for creating parameter binding strategies.

    This factory implements the Factory Method pattern to create appropriate
    binding strategies based on parameter type. It centralizes the creation logic
    and makes it easy to add new parameter types in the future.

    Examples:
        ```python
        body_strategy = ParameterBindingStrategyFactory.create_strategy("body")


        config = ConventionalPrefixConfig(request_path_prefix="custom_path")
        path_strategy = ParameterBindingStrategyFactory.create_strategy("path", config)


        type_hints = {"_x_file_upload": FileUploadModel}
        file_strategy = ParameterBindingStrategyFactory.create_strategy(
            "file", prefix_config=None, type_hints=type_hints
        )


        kwargs = {}
        kwargs = body_strategy.bind_parameter(
            param_name="_x_body", model=RequestModel, kwargs=kwargs, framework_decorator=flask_decorator
        )
        ```

    """

    @staticmethod
    def create_strategy(
        param_type: str,
        prefix_config: ConventionalPrefixConfig | None = None,
        type_hints: dict[str, Any] | None = None,
    ) -> ParameterBindingStrategy:
        """Create a parameter binding strategy based on parameter type.

        Args:
            param_type: The type of parameter ('body', 'query', 'path', 'file')
            prefix_config: Optional configuration object with custom prefixes
            type_hints: Function type hints (needed for file parameters)

        Returns:
            A parameter binding strategy instance

        Raises:
            ValueError: If the parameter type is not supported

        """
        if param_type == "body":
            return RequestBodyBindingStrategy()
        if param_type == "query":
            return QueryParameterBindingStrategy()
        if param_type == "path":
            return PathParameterBindingStrategy(prefix_config)
        if param_type == "file":
            return FileParameterBindingStrategy(prefix_config, type_hints)
        msg = f"Unsupported parameter type: {param_type}"
        raise ValueError(msg)


class ParameterProcessor:
    """Processor for handling parameter binding using strategies.

    This class implements the Facade pattern, providing a simplified interface
    to the parameter binding system. It coordinates the use of different binding
    strategies based on parameter types and handles the overall parameter processing
    workflow.

    The processor uses the Strategy pattern via the ParameterBindingStrategyFactory
    to create and apply appropriate binding strategies for different parameter types.
    """

    def __init__(
        self,
        prefix_config: ConventionalPrefixConfig | None = None,
        framework_decorator: Any = None,
    ) -> None:
        """Initialize the parameter processor.

        Args:
            prefix_config: Optional configuration object with custom prefixes
            framework_decorator: The framework-specific decorator instance that
                                handles framework-specific binding logic

        """
        self.prefix_config = prefix_config
        self.framework_decorator = framework_decorator
        from flask_x_openapi_schema.core.cache import get_parameter_prefixes

        self.prefixes = get_parameter_prefixes(prefix_config)
        self.body_prefix, self.query_prefix, self.path_prefix, self.file_prefix = self.prefixes

    def process_parameters(
        self,
        _func: Callable[..., Any],
        cached_data: dict[str, Any],
        _args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> dict[str, Any]:
        """Process all parameters for a request.

        This method coordinates the binding of different parameter types:
        1. Request body parameters (from JSON request body)
        2. Query parameters (from URL query string)
        3. Path parameters (from URL path segments)
        4. File parameters (from multipart/form-data uploads)

        It uses the appropriate binding strategy for each parameter type and
        delegates to the framework-specific decorator for additional processing.

        Args:
            func: The decorated function
            cached_data: Cached metadata and other information including:
                         - param_names: List of parameter names
                         - type_hints: Function type hints
                         - actual_request_body: Request body model
                         - actual_query_model: Query parameters model
                         - actual_path_params: Path parameters
            args: Positional arguments to the function
            kwargs: Keyword arguments to the function

        Returns:
            Updated kwargs dictionary with bound parameters

        """
        param_names = cached_data["param_names"]
        type_hints = cached_data["type_hints"]
        actual_request_body = cached_data["actual_request_body"]
        actual_query_model = cached_data["actual_query_model"]
        actual_path_params = cached_data["actual_path_params"]

        has_request_context = False
        with contextlib.suppress(RuntimeError):
            has_request_context = bool(request)

        if not has_request_context:
            return kwargs

        skip_params = {"self", "cls"}

        if actual_request_body and isinstance(actual_request_body, type) and issubclass(actual_request_body, BaseModel):
            strategy = ParameterBindingStrategyFactory.create_strategy("body")
            for param_name in param_names:
                if param_name in skip_params:
                    continue

                if param_name.startswith(self.body_prefix):
                    kwargs = strategy.bind_parameter(param_name, actual_request_body, kwargs, self.framework_decorator)
                    break

        if actual_query_model:
            strategy = ParameterBindingStrategyFactory.create_strategy("query")
            for param_name in param_names:
                if param_name in skip_params:
                    continue

                if param_name.startswith(self.query_prefix):
                    kwargs = strategy.bind_parameter(param_name, actual_query_model, kwargs, self.framework_decorator)
                    break

        if actual_path_params:
            strategy = ParameterBindingStrategyFactory.create_strategy("path", self.prefix_config)
            for param_name in param_names:
                if param_name in skip_params:
                    continue

                if param_name.startswith(self.path_prefix):
                    kwargs = strategy.bind_parameter(param_name, None, kwargs, None)

        strategy = ParameterBindingStrategyFactory.create_strategy("file", self.prefix_config, type_hints)
        for param_name in param_names:
            if param_name in skip_params:
                continue

            if param_name.startswith(self.file_prefix):
                kwargs = strategy.bind_parameter(param_name, None, kwargs, None)

        return self.framework_decorator.process_additional_params(kwargs, param_names)
