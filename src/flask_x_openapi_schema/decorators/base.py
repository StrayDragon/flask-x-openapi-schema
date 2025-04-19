"""
Base classes and utilities for OpenAPI metadata decorators.
"""

import inspect
import threading
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache, wraps
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar, Union, cast, get_type_hints

from flask import request
from pydantic import BaseModel

# For Python 3.10+, use typing directly; for older versions, use typing_extensions
try:
    from typing import ParamSpec  # Python 3.10+
except ImportError:
    from typing_extensions import ParamSpec  # Python < 3.10

from ..i18n.i18n_string import I18nStr, get_current_language
from ..models.base import BaseRespModel

# Type variables for function parameters and return type
P = ParamSpec("P")
R = TypeVar("R")


@dataclass(frozen=True)
class ConventionalPrefixConfig:
    """Configuration class for OpenAPI parameter prefixes.

    This class holds configuration settings for parameter prefixes used in
    binding request data to function parameters.

    Attributes:
        request_body_prefix: Prefix for request body parameters
        request_query_prefix: Prefix for query parameters
        request_path_prefix: Prefix for path parameters
        request_file_prefix: Prefix for file parameters
    """

    request_body_prefix: str = "x_request_body"
    request_query_prefix: str = "x_request_query"
    request_path_prefix: str = "x_request_path"
    request_file_prefix: str = "x_request_file"


# Default parameter prefixes
DEFAULT_BODY_PREFIX = "x_request_body"
DEFAULT_QUERY_PREFIX = "x_request_query"
DEFAULT_PATH_PREFIX = "x_request_path"
DEFAULT_FILE_PREFIX = "x_request_file"

# Global configuration instance with thread safety
class ThreadSafeConfig:
    """Thread-safe configuration holder."""

    def __init__(self):
        self._config = ConventionalPrefixConfig(
            request_body_prefix=DEFAULT_BODY_PREFIX,
            request_query_prefix=DEFAULT_QUERY_PREFIX,
            request_path_prefix=DEFAULT_PATH_PREFIX,
            request_file_prefix=DEFAULT_FILE_PREFIX,
        )
        self._lock = threading.RLock()

    def get(self) -> ConventionalPrefixConfig:
        """Get the current configuration."""
        with self._lock:
            return ConventionalPrefixConfig(
                request_body_prefix=self._config.request_body_prefix,
                request_query_prefix=self._config.request_query_prefix,
                request_path_prefix=self._config.request_path_prefix,
                request_file_prefix=self._config.request_file_prefix,
            )

    def set(self, config: ConventionalPrefixConfig) -> None:
        """Set a new configuration."""
        with self._lock:
            self._config = ConventionalPrefixConfig(
                request_body_prefix=config.request_body_prefix,
                request_query_prefix=config.request_query_prefix,
                request_path_prefix=config.request_path_prefix,
                request_file_prefix=config.request_file_prefix,
            )

    def reset(self) -> None:
        """Reset to default configuration."""
        with self._lock:
            self._config = ConventionalPrefixConfig(
                request_body_prefix=DEFAULT_BODY_PREFIX,
                request_query_prefix=DEFAULT_QUERY_PREFIX,
                request_path_prefix=DEFAULT_PATH_PREFIX,
                request_file_prefix=DEFAULT_FILE_PREFIX,
            )


# Create a singleton instance
GLOBAL_CONFIG_HOLDER = ThreadSafeConfig()


def configure_prefixes(config: ConventionalPrefixConfig) -> None:
    """Configure global parameter prefixes.

    Args:
        config: Configuration object with parameter prefixes
    """
    # Update the configuration in a thread-safe manner
    GLOBAL_CONFIG_HOLDER.set(config)

    # Clear the parameter prefix cache to ensure fresh values
    _get_parameter_prefixes.cache_clear()


def reset_prefixes() -> None:
    """Reset parameter prefixes to default values."""
    # Reset the configuration in a thread-safe manner
    GLOBAL_CONFIG_HOLDER.reset()

    # Clear the parameter prefix cache to ensure fresh values
    _get_parameter_prefixes.cache_clear()


@lru_cache(maxsize=128)
def _get_parameter_prefixes(config: Optional[ConventionalPrefixConfig] = None) -> Tuple[str, str, str, str]:
    """
    Get parameter prefixes from config or global defaults.

    Args:
        config: Optional configuration object with custom prefixes

    Returns:
        Tuple of (body_prefix, query_prefix, path_prefix, file_prefix)
    """
    prefix_config = config or GLOBAL_CONFIG_HOLDER.get()
    return (
        prefix_config.request_body_prefix,
        prefix_config.request_query_prefix,
        prefix_config.request_path_prefix,
        prefix_config.request_file_prefix
    )


def _detect_parameters(
    signature: inspect.Signature,
    type_hints: Dict[str, Any],
    config: Optional[ConventionalPrefixConfig] = None,
) -> Tuple[Optional[Type[BaseModel]], Optional[Type[BaseModel]], List[str]]:
    """
    Detect request parameters from function signature.

    Args:
        signature: Function signature
        type_hints: Function type hints
        config: Optional configuration object with custom prefixes

    Returns:
        Tuple of (detected_request_body, detected_query_model, detected_path_params)
    """
    detected_request_body = None
    detected_query_model = None
    detected_path_params = []

    # Get parameter prefixes (cached)
    body_prefix, query_prefix, path_prefix, _ = _get_parameter_prefixes(config)

    # Precompute path prefix length to avoid repeated calculations
    path_prefix_len = len(path_prefix) + 1  # +1 for the underscore

    # Skip these parameter names
    skip_params = {"self", "cls"}

    # Look for parameters with special prefixes
    for param_name in signature.parameters:
        # Skip 'self' and 'cls' parameters
        if param_name in skip_params:
            continue

        # Check for request_body parameter
        if param_name.startswith(body_prefix):
            param_type = type_hints.get(param_name)
            if (
                param_type
                and isinstance(param_type, type)
                and issubclass(param_type, BaseModel)
            ):
                detected_request_body = param_type
                continue

        # Check for request_query parameter
        if param_name.startswith(query_prefix):
            param_type = type_hints.get(param_name)
            if (
                param_type
                and isinstance(param_type, type)
                and issubclass(param_type, BaseModel)
            ):
                detected_query_model = param_type
                continue

        # Check for request_path parameter
        if param_name.startswith(path_prefix):
            # Extract the path parameter name from the parameter name
            # Format: x_request_path_<param_name>
            param_suffix = param_name[path_prefix_len:]
            if "_" in param_suffix:
                path_param_name = param_suffix.split("_", 1)[1]
                detected_path_params.append(path_param_name)

    return detected_request_body, detected_query_model, detected_path_params


def _process_i18n_value(
    value: Optional[Union[str, I18nStr]], language: Optional[str]
) -> Optional[str]:
    """
    Process an I18nString value to get the string for the current language.

    Args:
        value: The value to process (string or I18nString)
        language: The language to use, or None to use the current language

    Returns:
        The processed string value
    """
    if value is None:
        return None

    current_lang = language or get_current_language()

    if isinstance(value, I18nStr):
        return value.get(current_lang)
    return value


def _generate_openapi_metadata(
    summary: Optional[Union[str, I18nStr]],
    description: Optional[Union[str, I18nStr]],
    tags: Optional[List[str]],
    operation_id: Optional[str],
    deprecated: bool,
    security: Optional[List[Dict[str, List[str]]]],
    external_docs: Optional[Dict[str, str]],
    actual_request_body: Optional[Union[Type[BaseModel], Dict[str, Any]]],
    responses: Optional[Dict[str, Any]],
    _parameters: Optional[List[Dict[str, Any]]],
    _actual_query_model: Optional[Type[BaseModel]],
    _actual_path_params: Optional[List[str]],
    language: Optional[str],
) -> Dict[str, Any]:
    """
    Generate OpenAPI metadata dictionary.

    Args:
        Various parameters for OpenAPI metadata

    Returns:
        OpenAPI metadata dictionary
    """
    metadata: Dict[str, Any] = {}

    # Use the specified language or get the current language
    current_lang = language or get_current_language()

    # Handle I18nString fields
    if summary is not None:
        metadata["summary"] = _process_i18n_value(summary, current_lang)
    if description is not None:
        metadata["description"] = _process_i18n_value(description, current_lang)

    # Add other metadata fields if provided
    if tags:
        metadata["tags"] = tags
    if operation_id:
        metadata["operationId"] = operation_id
    if deprecated:
        metadata["deprecated"] = deprecated
    if security:
        metadata["security"] = security
    if external_docs:
        metadata["externalDocs"] = external_docs

    # Handle request body
    if actual_request_body:
        if isinstance(actual_request_body, type) and issubclass(
            actual_request_body, BaseModel
        ):
            # It's a Pydantic model
            metadata["requestBody"] = {
                "content": {
                    "application/json": {
                        "schema": {
                            "$ref": f"#/components/schemas/{actual_request_body.__name__}"
                        }
                    }
                },
                "required": True,
            }
        else:
            # It's a dict
            metadata["requestBody"] = actual_request_body

    # Handle responses
    if responses:
        metadata["responses"] = responses

    return metadata


def _handle_response(result: Any) -> Any:
    """
    Handle response conversion for BaseRespModel instances.

    Args:
        result: Function result

    Returns:
        Processed result
    """
    if isinstance(result, BaseRespModel):
        # Convert the model to a response
        return result.to_response()
    elif (
        isinstance(result, tuple)
        and len(result) >= 1
        and isinstance(result[0], BaseRespModel)
    ):
        # Handle tuple returns with status code
        model = result[0]
        if len(result) >= 2 and isinstance(result[1], int):
            # Return with status code
            return model.to_response(result[1])
        else:
            # Return without status code
            return model.to_response()

    # Return the original result if it's not a BaseRespModel
    return result


def _detect_file_parameters(
    param_names: List[str],
    func_annotations: Dict[str, Any],
    config: Optional[ConventionalPrefixConfig] = None,
) -> List[Dict[str, Any]]:
    """
    Detect file parameters from function signature.

    Args:
        param_names: List of parameter names
        func_annotations: Function type annotations
        config: Optional configuration object with custom prefixes

    Returns:
        List of file parameters for OpenAPI schema
    """
    file_params = []

    # Use custom prefix if provided, otherwise use default
    prefix_config = config or GLOBAL_CONFIG_HOLDER.get()
    file_prefix = prefix_config.request_file_prefix
    file_prefix_len = len(file_prefix) + 1  # +1 for the underscore

    for param_name in param_names:
        if not param_name.startswith(file_prefix):
            continue

        # Get the parameter type annotation
        param_type = func_annotations.get(param_name)

        # Extract the file parameter name
        param_suffix = param_name[file_prefix_len:]
        if "_" in param_suffix:
            file_param_name = param_suffix.split("_", 1)[1]
        else:
            file_param_name = "file"

        # Check if the parameter is a Pydantic model with a file field
        file_description = f"File upload for {file_param_name}"

        if (
            param_type
            and isinstance(param_type, type)
            and issubclass(param_type, BaseModel)
        ):
            if (
                hasattr(param_type, "model_fields")
                and "file" in param_type.model_fields
            ):
                field_info = param_type.model_fields["file"]
                if field_info.description:
                    file_description = field_info.description

        # Add file parameter to OpenAPI schema
        file_params.append(
            {
                "name": file_param_name,
                "in": "formData",
                "required": True,
                "type": "file",
                "description": file_description,
            }
        )

    return file_params


def _preprocess_request_data(data: Dict[str, Any], model: Type[BaseModel]) -> Dict[str, Any]:
    """
    Pre-process request data to handle list fields and other complex types correctly.

    Args:
        data: The request data to process
        model: The Pydantic model to use for type information

    Returns:
        Processed data that can be validated by Pydantic
    """
    if not hasattr(model, "model_fields"):
        return data

    result = {}

    # Process each field based on its type annotation
    for field_name, field_info in model.model_fields.items():
        if field_name not in data:
            continue

        field_value = data[field_name]
        field_type = field_info.annotation

        # Handle list fields
        origin = getattr(field_type, "__origin__", None)
        if origin is list or origin is List:
            # If the value is a string that looks like a JSON array, parse it
            if isinstance(field_value, str) and field_value.startswith('[') and field_value.endswith(']'):
                try:
                    import json
                    result[field_name] = json.loads(field_value)
                    continue
                except json.JSONDecodeError:
                    pass

            # If it's already a list, use it as is
            if isinstance(field_value, list):
                result[field_name] = field_value
            else:
                # Try to convert to a list if possible
                try:
                    result[field_name] = [field_value]
                except Exception:
                    # If conversion fails, keep the original value
                    result[field_name] = field_value
        else:
            # For non-list fields, keep the original value
            result[field_name] = field_value

    # Add any fields from the original data that weren't processed
    for key, value in data.items():
        if key not in result:
            result[key] = value

    return result


def _extract_param_types(
    request_body_model: Optional[Type[BaseModel]],
    query_model: Optional[Type[BaseModel]],
) -> Dict[str, Any]:
    """
    Extract parameter types from Pydantic models for type annotations.

    Args:
        request_body_model: Request body Pydantic model
        query_model: Query parameters Pydantic model

    Returns:
        Dictionary of parameter types
    """
    param_types = {}

    # Add types from request_body if it's a Pydantic model
    if request_body_model and hasattr(request_body_model, "model_fields"):
        # Get field types from the Pydantic model
        param_types.update(
            {
                field_name: field.annotation
                for field_name, field in request_body_model.model_fields.items()
            }
        )

    # Add types from query_model if it's a Pydantic model
    if query_model and hasattr(query_model, "model_fields"):
        param_types.update(
            {
                field_name: field.annotation
                for field_name, field in query_model.model_fields.items()
            }
        )

    return param_types


class OpenAPIDecoratorBase(ABC):
    """Base class for OpenAPI metadata decorators."""

    def __init__(
        self,
        summary: Optional[Union[str, I18nStr]] = None,
        description: Optional[Union[str, I18nStr]] = None,
        tags: Optional[List[str]] = None,
        operation_id: Optional[str] = None,
        request_body: Optional[Union[Type[BaseModel], Dict[str, Any]]] = None,
        responses: Optional[Dict[str, Any]] = None,
        parameters: Optional[List[Dict[str, Any]]] = None,
        deprecated: bool = False,
        security: Optional[List[Dict[str, List[str]]]] = None,
        external_docs: Optional[Dict[str, str]] = None,
        query_model: Optional[Type[BaseModel]] = None,
        path_params: Optional[List[str]] = None,
        auto_detect_params: bool = True,
        language: Optional[str] = None,
        prefix_config: Optional[ConventionalPrefixConfig] = None,
    ):
        """Initialize the decorator with OpenAPI metadata parameters."""
        self.summary = summary
        self.description = description
        self.tags = tags
        self.operation_id = operation_id
        self.request_body = request_body
        self.responses = responses
        self.parameters = parameters
        self.deprecated = deprecated
        self.security = security
        self.external_docs = external_docs
        self.query_model = query_model
        self.path_params = path_params
        self.auto_detect_params = auto_detect_params
        self.language = language
        self.prefix_config = prefix_config

    def __call__(self, func: Callable[P, R]) -> Callable[P, R]:
        """Apply the decorator to the function."""
        # Get the function signature to find parameters with special prefixes
        signature = inspect.signature(func)
        param_names = list(signature.parameters.keys())

        # Get type hints from the function
        type_hints = get_type_hints(func)

        # Auto-detect parameters if enabled
        detected_request_body = None
        detected_query_model = None
        detected_path_params = []

        if self.auto_detect_params:
            # Use helper function to detect parameters
            detected_request_body, detected_query_model, detected_path_params = (
                _detect_parameters(signature, type_hints, self.prefix_config)
            )

        # Use detected parameters if not explicitly provided
        actual_request_body = self.request_body
        if actual_request_body is None and detected_request_body is not None:
            actual_request_body = detected_request_body

        actual_query_model = self.query_model
        if actual_query_model is None and detected_query_model is not None:
            actual_query_model = detected_query_model

        actual_path_params = self.path_params
        if actual_path_params is None and detected_path_params:
            actual_path_params = detected_path_params

        # Generate OpenAPI metadata using helper function
        metadata = _generate_openapi_metadata(
            summary=self.summary,
            description=self.description,
            tags=self.tags,
            operation_id=self.operation_id,
            deprecated=self.deprecated,
            security=self.security,
            external_docs=self.external_docs,
            actual_request_body=actual_request_body,
            responses=self.responses,
            _parameters=self.parameters,
            _actual_query_model=actual_query_model,
            _actual_path_params=actual_path_params,
            language=self.language,
        )

        # Handle parameters from the parameters argument
        openapi_parameters = self.parameters or []

        # Add parameters from query_model and path_params
        if actual_query_model or actual_path_params:
            model_parameters = self.extract_parameters_from_models(
                query_model=actual_query_model, path_params=actual_path_params
            )
            openapi_parameters.extend(model_parameters)

        # Add file parameters based on function signature
        file_params = []
        if self.auto_detect_params:
            # Get function annotations
            func_annotations = get_type_hints(func)
            file_params = _detect_file_parameters(
                param_names, func_annotations, self.prefix_config
            )

        # If we have file parameters, set the consumes property to multipart/form-data
        if file_params:
            metadata["consumes"] = ["multipart/form-data"]
            openapi_parameters.extend(file_params)

        if openapi_parameters:
            metadata["parameters"] = openapi_parameters

        # Attach metadata to the function
        func._openapi_metadata = metadata  # type: ignore

        # Extract parameter types for type annotations
        param_types = _extract_param_types(
            request_body_model=actual_request_body
            if isinstance(actual_request_body, type)
            and issubclass(actual_request_body, BaseModel)
            else None,
            query_model=actual_query_model,
        )

        # Create a wrapper function that handles parameter binding
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check if we're in a request context
            has_request_context = False
            try:
                has_request_context = bool(request)
            except RuntimeError:
                # Not in a request context, skip request-dependent processing
                pass

            if has_request_context:
                # Process special parameters that depend on request context
                # Skip 'self' and 'cls' parameters
                skip_params = {"self", "cls"}

                # Get parameter prefixes (cached)
                body_prefix, query_prefix, path_prefix, file_prefix = _get_parameter_prefixes(self.prefix_config)

                # Precompute prefix lengths for path and file parameters
                path_prefix_len = len(path_prefix) + 1  # +1 for the underscore
                file_prefix_len = len(file_prefix) + 1  # +1 for the underscore

                # Process request body parameters
                if (
                    actual_request_body
                    and isinstance(actual_request_body, type)
                    and issubclass(actual_request_body, BaseModel)
                ):
                    for param_name in param_names:
                        if param_name in skip_params:
                            continue

                        if param_name.startswith(body_prefix):
                            # Process request body
                            kwargs = self.process_request_body(
                                param_name, actual_request_body, kwargs
                            )
                            break  # Only process the first request body parameter

                # Process query parameters
                if actual_query_model:
                    for param_name in param_names:
                        if param_name in skip_params:
                            continue

                        if param_name.startswith(query_prefix):
                            # Process query parameters
                            kwargs = self.process_query_params(
                                param_name, actual_query_model, kwargs
                            )
                            break  # Only process the first query parameter

                # Process path parameters
                if actual_path_params:
                    for param_name in param_names:
                        if param_name in skip_params:
                            continue

                        if param_name.startswith(path_prefix):
                            # Extract the path parameter name
                            param_suffix = param_name[path_prefix_len:]
                            if "_" in param_suffix:
                                path_param_name = param_suffix.split("_", 1)[1]
                                if path_param_name in kwargs:
                                    kwargs[param_name] = kwargs[path_param_name]

                # Process file parameters
                for param_name in param_names:
                    if param_name in skip_params:
                        continue

                    if param_name.startswith(file_prefix):
                        # Get the parameter type annotation
                        param_type = type_hints.get(param_name)

                        # Check if the parameter is a Pydantic model
                        is_pydantic_model = (
                            param_type
                            and isinstance(param_type, type)
                            and issubclass(param_type, BaseModel)
                            and hasattr(param_type, "model_fields")
                            and "file" in param_type.model_fields
                        )

                        # Extract the file parameter name
                        param_suffix = param_name[file_prefix_len:]
                        if "_" in param_suffix:
                            file_param_name = param_suffix.split("_", 1)[1]
                            if file_param_name in request.files:
                                file_obj = request.files[file_param_name]
                                if is_pydantic_model:
                                    # Create a Pydantic model instance with the file
                                    kwargs[param_name] = param_type(file=file_obj)
                                else:
                                    # Just pass the file directly
                                    kwargs[param_name] = file_obj
                        else:
                            # If no specific file name is provided, use 'file' as the default
                            if "file" in request.files:
                                file_obj = request.files["file"]
                                if is_pydantic_model:
                                    # Create a Pydantic model instance with the file
                                    kwargs[param_name] = param_type(file=file_obj)
                                else:
                                    # Just pass the file directly
                                    kwargs[param_name] = file_obj
                            # If there's only one file, use that
                            elif len(request.files) == 1:
                                file_obj = next(iter(request.files.values()))
                                if is_pydantic_model:
                                    # Create a Pydantic model instance with the file
                                    kwargs[param_name] = param_type(file=file_obj)
                                else:
                                    # Just pass the file directly
                                    kwargs[param_name] = file_obj

                # Process any additional framework-specific parameters
                kwargs = self.process_additional_params(kwargs, param_names)

            # Filter out any kwargs that are not in the function signature
            # Get the function signature parameters once
            sig_params = signature.parameters
            valid_kwargs = {k: v for k, v in kwargs.items() if k in sig_params}

            # Call the original function with filtered kwargs
            result = func(*args, **valid_kwargs)

            # Handle response conversion using helper function
            return _handle_response(result)

        # Copy OpenAPI metadata to the wrapper
        wrapper._openapi_metadata = metadata  # type: ignore

        # Add type hints to the wrapper function
        if param_types:
            # Get existing type hints
            existing_hints = get_type_hints(func)
            # Merge with new type hints from Pydantic models
            merged_hints = {**existing_hints, **param_types}
            # Apply the merged type hints to the wrapper
            wrapper.__annotations__ = merged_hints

        return cast(Callable[P, R], wrapper)

    @abstractmethod
    def extract_parameters_from_models(
        self, query_model: Optional[Type[BaseModel]], path_params: Optional[List[str]]
    ) -> List[Dict[str, Any]]:
        """Extract OpenAPI parameters from models."""
        pass

    @abstractmethod
    def process_request_body(
        self, param_name: str, model: Type[BaseModel], kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process request body parameters."""
        pass

    @abstractmethod
    def process_query_params(
        self, param_name: str, model: Type[BaseModel], kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process query parameters."""
        pass

    @abstractmethod
    def process_additional_params(
        self, kwargs: Dict[str, Any], param_names: List[str]
    ) -> Dict[str, Any]:
        """Process additional framework-specific parameters."""
        pass