"""Base classes and utilities for OpenAPI metadata decorators."""

import contextlib
import inspect
import logging
from collections.abc import Callable
from functools import wraps
from typing import (
    Any,
    TypeVar,
    cast,
    get_type_hints,
)

from pydantic import BaseModel

# For Python 3.10+, use typing directly; for older versions, use typing_extensions
try:
    from typing import ParamSpec  # Python 3.10+
except ImportError:
    from typing_extensions import ParamSpec  # Python < 3.10

from flask_x_openapi_schema.i18n.i18n_string import I18nStr, get_current_language
from flask_x_openapi_schema.models.base import BaseRespModel
from flask_x_openapi_schema.models.responses import OpenAPIMetaResponse

from .cache import (
    FUNCTION_METADATA_CACHE,
    get_parameter_prefixes,
)
from .config import GLOBAL_CONFIG_HOLDER, ConventionalPrefixConfig
from .param_binding import ParameterProcessor
from .utils import _fix_references

# Type variables for function parameters and return type
P = ParamSpec("P")
R = TypeVar("R")

# Get logger for this module
logger = logging.getLogger(__name__)


def _extract_parameters_from_prefixes(
    signature: inspect.Signature,
    type_hints: dict[str, Any],
    config: ConventionalPrefixConfig | None = None,
) -> tuple[type[BaseModel] | None, type[BaseModel] | None, list[str]]:
    """Extract parameters based on prefix types from function signature.

    This function does not auto-detect parameters, but simply extracts them based on their prefixes.

    Args:
        signature: Function signature
        type_hints: Function type hints
        config: Optional configuration object with custom prefixes

    Returns:
        Tuple of (request_body, query_model, path_params)

    """
    # Debug information
    import logging

    logger = logging.getLogger(__name__)

    # Get parameter prefixes
    prefixes = get_parameter_prefixes(config)
    logger.debug(f"Extracting parameters with prefixes={prefixes}, signature={signature}, type_hints={type_hints}")

    request_body = None
    query_model = None
    path_params = []

    # Get parameter prefixes
    body_prefix, query_prefix, path_prefix, _ = prefixes

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
            if param_type and isinstance(param_type, type) and issubclass(param_type, BaseModel):
                request_body = param_type
                continue

        # Check for request_query parameter
        if param_name.startswith(query_prefix):
            param_type = type_hints.get(param_name)
            if param_type and isinstance(param_type, type) and issubclass(param_type, BaseModel):
                query_model = param_type
                continue

        # Check for request_path parameter
        if param_name.startswith(path_prefix):
            # Extract the path parameter name from the parameter name
            # Format: _x_path_<param_name>
            param_suffix = param_name[path_prefix_len:]
            # Use the full suffix as the parameter name
            path_params.append(param_suffix)

    result = (request_body, query_model, path_params)

    # Debug information
    logger.debug(
        f"Extracted parameters: request_body={request_body}, query_model={query_model}, path_params={path_params}",
    )

    return result


def _process_i18n_value(value: str | I18nStr | None, language: str | None) -> str | None:
    """Process an I18nString value to get the string for the current language.

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


def _generate_openapi_metadata(  # noqa: D417
    summary: str | I18nStr | None,
    description: str | I18nStr | None,
    tags: list[str] | None,
    operation_id: str | None,
    deprecated: bool,
    security: list[dict[str, list[str]]] | None,
    external_docs: dict[str, str] | None,
    actual_request_body: type[BaseModel] | dict[str, Any] | None,
    responses: OpenAPIMetaResponse | None,
    language: str | None,
) -> dict[str, Any]:
    """Generate OpenAPI metadata dictionary.

    Args:
        Various parameters for OpenAPI metadata

    Returns:
        OpenAPI metadata dictionary

    """
    # Debug information
    import logging

    logger = logging.getLogger(__name__)
    logger.debug(f"Generating OpenAPI metadata with request_body={actual_request_body}")
    metadata: dict[str, Any] = {}

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
        logger.debug(f"Processing request body: {actual_request_body}")
        if isinstance(actual_request_body, type) and issubclass(actual_request_body, BaseModel):
            # It's a Pydantic model
            logger.debug(f"Request body is a Pydantic model: {actual_request_body.__name__}")
            # Check if the model has a Config with multipart/form-data flag
            is_multipart = False
            has_file_fields = False

            # Check model config for multipart/form-data flag
            if hasattr(actual_request_body, "model_config"):
                config = getattr(actual_request_body, "model_config", {})
                if isinstance(config, dict) and config.get("json_schema_extra", {}).get("multipart/form-data", False):
                    is_multipart = True
            elif hasattr(actual_request_body, "Config") and hasattr(actual_request_body.Config, "json_schema_extra"):
                config_extra = getattr(actual_request_body.Config, "json_schema_extra", {})
                is_multipart = config_extra.get("multipart/form-data", False)

            # Check if model has any file fields
            if hasattr(actual_request_body, "model_fields"):
                for field_info in actual_request_body.model_fields.values():
                    field_schema = getattr(field_info, "json_schema_extra", None)
                    if field_schema is not None and field_schema.get("format") == "binary":
                        has_file_fields = True
                        break

            # If model has file fields or is explicitly marked as multipart/form-data, use multipart/form-data
            content_type = "multipart/form-data" if (is_multipart or has_file_fields) else "application/json"
            logger.debug(f"Using content type: {content_type}")

            metadata["requestBody"] = {
                "content": {content_type: {"schema": {"$ref": f"#/components/schemas/{actual_request_body.__name__}"}}},
                "required": True,
            }
            logger.debug(f"Added requestBody to metadata: {metadata['requestBody']}")
        else:
            # It's a dict
            logger.debug(f"Request body is a dict: {actual_request_body}")
            metadata["requestBody"] = actual_request_body

    # Handle responses
    if responses:
        metadata["responses"] = responses.to_openapi_dict()

    return metadata


def _handle_response(result: Any) -> Any:
    """Handle response conversion for BaseRespModel instances.

    Args:
        result: Function result

    Returns:
        Processed result

    """
    if isinstance(result, BaseRespModel):
        # Convert the model to a response
        return result.to_response()
    if isinstance(result, tuple) and len(result) >= 1 and isinstance(result[0], BaseRespModel):
        # Handle tuple returns with status code
        model = result[0]
        if len(result) >= 2 and isinstance(result[1], int):  # noqa: PLR2004
            # Return with status code
            return model.to_response(result[1])
        # Return without status code
        return model.to_response()

    # Return the original result if it's not a BaseRespModel
    return result


def _detect_file_parameters(
    param_names: list[str],
    func_annotations: dict[str, Any],
    config: ConventionalPrefixConfig | None = None,
) -> list[dict[str, Any]]:
    """Detect file parameters from function signature.

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
        file_param_name = param_suffix.split("_", 1)[1] if "_" in param_suffix else "file"

        # Check if the parameter is a Pydantic model with a file field
        file_description = f"File upload for {file_param_name}"

        if param_type and isinstance(param_type, type) and issubclass(param_type, BaseModel):  # noqa: SIM102
            if hasattr(param_type, "model_fields") and "file" in param_type.model_fields:
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
            },
        )

    return file_params


class OpenAPIDecoratorBase:
    """Base class for OpenAPI metadata decorators."""

    def __init__(
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
        framework: str = "flask",
    ) -> None:
        """Initialize the decorator with OpenAPI metadata parameters."""
        self.summary = summary
        self.description = description
        self.tags = tags
        self.operation_id = operation_id
        self.responses = responses
        self.deprecated = deprecated
        self.security = security
        self.external_docs = external_docs
        self.language = language
        self.prefix_config = prefix_config
        self.framework = framework

        # Framework-specific decorator
        self.framework_decorator = None

        # We'll initialize the framework-specific decorator when needed
        # to avoid circular imports

    def _initialize_framework_decorator(self) -> None:
        """Initialize the framework-specific decorator.

        This method uses lazy loading to avoid circular imports.
        """
        if self.framework_decorator is None:
            if self.framework == "flask":
                # Import here to avoid circular imports
                from flask_x_openapi_schema.x.flask.decorators import FlaskOpenAPIDecorator

                self.framework_decorator = FlaskOpenAPIDecorator(
                    summary=self.summary,
                    description=self.description,
                    tags=self.tags,
                    operation_id=self.operation_id,
                    responses=self.responses,
                    deprecated=self.deprecated,
                    security=self.security,
                    external_docs=self.external_docs,
                    language=self.language,
                    prefix_config=self.prefix_config,
                )
            elif self.framework == "flask_restful":
                # Import here to avoid circular imports
                from flask_x_openapi_schema.x.flask_restful.decorators import FlaskRestfulOpenAPIDecorator

                self.framework_decorator = FlaskRestfulOpenAPIDecorator(
                    summary=self.summary,
                    description=self.description,
                    tags=self.tags,
                    operation_id=self.operation_id,
                    responses=self.responses,
                    deprecated=self.deprecated,
                    security=self.security,
                    external_docs=self.external_docs,
                    language=self.language,
                    prefix_config=self.prefix_config,
                )
            else:
                msg = f"Unsupported framework: {self.framework}"
                raise ValueError(msg)

    def _create_cached_wrapper(self, func: Callable[P, R], cached_data: dict[str, Any]) -> Callable[P, R]:
        """Create a wrapper function that reuses cached metadata.

        Args:
            func: The decorated function
            cached_data: Cached metadata and other information

        Returns:
            A wrapper function that reuses cached metadata

        """
        logger.debug(f"Using cached metadata for function {func.__name__}")
        logger.debug(f"Cached metadata: {cached_data['metadata']}")

        # Create a wrapper function that reuses the cached metadata
        @wraps(func)
        def cached_wrapper(*args, **kwargs):  # noqa: ANN202
            # Initialize required parameters with empty model instances if needed
            signature = cached_data["signature"]
            param_names = cached_data["param_names"]

            # Create empty model instances for required parameters that are missing
            for param_name in param_names:
                if param_name not in kwargs and param_name in signature.parameters:
                    param = signature.parameters[param_name]
                    if param.default is param.empty and param_name in cached_data["type_hints"]:
                        param_type = cached_data["type_hints"][param_name]
                        if isinstance(param_type, type) and issubclass(param_type, BaseModel):
                            kwargs[param_name] = param_type()

            return self._process_request(func, cached_data, *args, **kwargs)

        # Copy cached metadata and annotations
        cached_wrapper._openapi_metadata = cached_data["metadata"]  # noqa: SLF001
        cached_wrapper.__annotations__ = cached_data["annotations"]

        return cast("Callable[P, R]", cached_wrapper)

    def _extract_parameters(
        self, signature: inspect.Signature, type_hints: dict[str, Any]
    ) -> tuple[type[BaseModel] | None, type[BaseModel] | None, list[str]]:
        """Extract parameters from function signature.

        Args:
            signature: Function signature
            type_hints: Function type hints

        Returns:
            Tuple of (request_body, query_model, path_params)

        """
        # Use helper function to extract parameters based on prefixes (cached)
        return _extract_parameters_from_prefixes(
            signature,
            type_hints,
            self.prefix_config,
        )

    def _generate_metadata_cache_key(
        self,
        actual_request_body: type[BaseModel] | dict[str, Any] | None,
        actual_query_model: type[BaseModel] | None,
        actual_path_params: list[str],
    ) -> tuple:
        """Generate a cache key for metadata.

        Args:
            actual_request_body: Request body model or dict
            actual_query_model: Query parameters model
            actual_path_params: Path parameters

        Returns:
            A cache key for metadata

        """
        return (
            str(self.summary),
            str(self.description),
            str(self.tags) if self.tags else None,
            self.operation_id,
            self.deprecated,
            str(self.security) if self.security else None,
            str(self.external_docs) if self.external_docs else None,
            id(actual_request_body) if isinstance(actual_request_body, type) else str(actual_request_body),
            str(self.responses) if self.responses else None,
            id(actual_query_model) if actual_query_model else None,
            str(actual_path_params) if actual_path_params else None,
            self.language,
        )

    def _get_or_generate_metadata(
        self,
        _cache_key: tuple,  # Not used in simplified cache system
        actual_request_body: type[BaseModel] | dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Generate OpenAPI metadata.

        Args:
            _cache_key: Cache key for metadata (not used in simplified cache system)
            actual_request_body: Request body model or dict

        Returns:
            OpenAPI metadata dictionary

        """
        # Generate metadata
        return _generate_openapi_metadata(
            summary=self.summary,
            description=self.description,
            tags=self.tags,
            operation_id=self.operation_id,
            deprecated=self.deprecated,
            security=self.security,
            external_docs=self.external_docs,
            actual_request_body=actual_request_body,
            responses=self.responses,
            language=self.language,
        )

    def _generate_openapi_parameters(
        self,
        actual_query_model: type[BaseModel] | None,
        actual_path_params: list[str],
        param_names: list[str],
        func_annotations: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Generate OpenAPI parameters.

        This method generates OpenAPI parameters from query models, path parameters,
        and file parameters. It uses caching to avoid regenerating parameters for
        the same models and parameters.

        Args:
            actual_query_model: Query parameters model
            actual_path_params: Path parameters
            param_names: Function parameter names
            func_annotations: Function type annotations

        Returns:
            List of OpenAPI parameters

        """
        openapi_parameters = []

        # Add parameters from query_model and path_params
        if actual_query_model or actual_path_params:
            model_parameters = self._get_or_generate_model_parameters(actual_query_model, actual_path_params)
            if model_parameters:
                logger.debug(f"Added parameters to metadata: {model_parameters}")
                openapi_parameters.extend(model_parameters)

        # Add file parameters based on function signature
        file_params = _detect_file_parameters(param_names, func_annotations, self.prefix_config)
        if file_params:
            openapi_parameters.extend(file_params)

        return openapi_parameters

    def _get_or_generate_model_parameters(
        self,
        query_model: type[BaseModel] | None,
        path_params: list[str],
    ) -> list[dict[str, Any]]:
        """Generate parameters from models and path parameters.

        This method is extracted from _generate_openapi_parameters to improve readability.
        It generates parameters from query models and path parameters.

        Args:
            query_model: Query parameters model
            path_params: Path parameters

        Returns:
            List of OpenAPI parameters

        """
        # Create parameters for OpenAPI schema
        model_parameters = []

        # Add path parameters
        if path_params:
            model_parameters.extend(self._generate_path_parameters(path_params))

        # Add query parameters
        if query_model:
            model_parameters.extend(self._generate_query_parameters(query_model))

        return model_parameters

    def _generate_path_parameters(self, path_params: list[str]) -> list[dict[str, Any]]:
        """Generate OpenAPI parameters for path parameters.

        Args:
            path_params: List of path parameter names

        Returns:
            List of OpenAPI parameters for path parameters

        """
        return [
            {
                "name": param,
                "in": "path",
                "required": True,
                "schema": {"type": "string"},
            }
            for param in path_params
        ]

    def _generate_query_parameters(self, query_model: type[BaseModel]) -> list[dict[str, Any]]:
        """Generate OpenAPI parameters for query parameters.

        Args:
            query_model: Query parameters model

        Returns:
            List of OpenAPI parameters for query parameters

        """
        parameters = []
        schema = query_model.model_json_schema()
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        for field_name, field_schema in properties.items():
            # Fix references in field_schema
            fixed_schema = _fix_references(field_schema)
            param = {
                "name": field_name,
                "in": "query",
                "required": field_name in required,
                "schema": fixed_schema,
            }

            # Add description if available
            if "description" in field_schema:
                param["description"] = field_schema["description"]

            parameters.append(param)

        return parameters

    def _create_function_wrapper(
        self,
        func: Callable[P, R],
        cached_data: dict[str, Any],
        metadata: dict[str, Any],
        merged_hints: dict[str, Any],
    ) -> Callable[P, R]:
        """Create a wrapper function for the decorated function.

        Args:
            func: The decorated function
            cached_data: Cached metadata and other information
            metadata: OpenAPI metadata
            merged_hints: Merged type hints

        Returns:
            A wrapper function

        """

        # Create a wrapper function that handles parameter binding
        @wraps(func)
        def wrapper(*args, **kwargs):  # noqa: ANN202
            return self._process_request(func, cached_data, *args, **kwargs)

        # Copy OpenAPI metadata to the wrapper
        wrapper._openapi_metadata = metadata  # noqa: SLF001

        # Add type hints to the wrapper function
        wrapper.__annotations__ = merged_hints

        return cast("Callable[P, R]", wrapper)

    def __call__(self, func: Callable[P, R]) -> Callable[P, R]:
        """Apply the decorator to the function.

        This method has been refactored to use smaller, more focused methods.

        Args:
            func: The function to decorate

        Returns:
            The decorated function

        """
        # Initialize the framework-specific decorator if needed
        self._initialize_framework_decorator()

        # Check if we've already decorated this function
        if func in FUNCTION_METADATA_CACHE:
            cached_data = FUNCTION_METADATA_CACHE[func]
            return self._create_cached_wrapper(func, cached_data)

        # Get the function signature to find parameters with special prefixes
        signature = inspect.signature(func)
        param_names = list(signature.parameters.keys())

        # Get type hints from the function
        type_hints = get_type_hints(func)

        # Extract parameters based on prefixes
        actual_request_body, actual_query_model, actual_path_params = self._extract_parameters(signature, type_hints)

        # Generate OpenAPI metadata
        logger.debug(
            f"Generating metadata with request_body={actual_request_body}, query_model={actual_query_model}, path_params={actual_path_params}",  # noqa: E501
        )

        # Create a cache key for metadata
        cache_key = self._generate_metadata_cache_key(actual_request_body, actual_query_model, actual_path_params)

        # Get or generate metadata
        metadata = self._get_or_generate_metadata(cache_key, actual_request_body)

        # Generate OpenAPI parameters
        func_annotations = get_type_hints(func)
        openapi_parameters = self._generate_openapi_parameters(
            actual_query_model, actual_path_params, param_names, func_annotations
        )

        # If we have file parameters, set the consumes property to multipart/form-data
        if any(param.get("in") == "formData" for param in openapi_parameters):
            metadata["consumes"] = ["multipart/form-data"]

        # Add parameters to metadata
        if openapi_parameters:
            metadata["parameters"] = openapi_parameters

        # Attach metadata to the function
        func._openapi_metadata = metadata  # noqa: SLF001

        # Extract parameter types for type annotations
        param_types = {}

        # Add types from request_body if it's a Pydantic model
        if (
            actual_request_body
            and isinstance(actual_request_body, type)
            and issubclass(actual_request_body, BaseModel)
            and hasattr(actual_request_body, "model_fields")
        ):
            param_types.update(
                {field_name: field.annotation for field_name, field in actual_request_body.model_fields.items()}
            )

        # Add types from query_model if it's a Pydantic model
        if actual_query_model and hasattr(actual_query_model, "model_fields"):
            param_types.update(
                {field_name: field.annotation for field_name, field in actual_query_model.model_fields.items()}
            )

        # Get existing type hints and merge with new type hints from Pydantic models
        existing_hints = get_type_hints(func)
        merged_hints = {**existing_hints, **param_types}

        # Cache the metadata and other information for future use
        cached_data = {
            "metadata": metadata,
            "annotations": merged_hints,
            "signature": signature,
            "param_names": param_names,
            "type_hints": type_hints,
            "actual_request_body": actual_request_body,
            "actual_query_model": actual_query_model,
            "actual_path_params": actual_path_params,
        }
        FUNCTION_METADATA_CACHE[func] = cached_data

        # Create and return the wrapper function
        return self._create_function_wrapper(func, cached_data, metadata, merged_hints)

    def _process_request(self, func: Callable[P, R], cached_data: dict[str, Any], *args, **kwargs) -> Any:  # noqa: PLR0915
        """Process a request using cached metadata.

        This method uses the ParameterProcessor to handle parameter binding using the Strategy pattern.

        Args:
            func: The decorated function
            cached_data: Cached metadata and other information
            args: Positional arguments to the function
            kwargs: Keyword arguments to the function

        Returns:
            The result of calling the function with bound parameters

        """
        # Extract signature for filtering kwargs
        signature = cached_data["signature"]
        param_names = cached_data.get("param_names", [])

        # Check if we're in a request context
        from flask import request

        has_request_context = False
        with contextlib.suppress(RuntimeError):
            has_request_context = bool(request)

        # If in request context and it's a POST request, try to create model directly from JSON data
        if has_request_context and request.method == "POST" and request.is_json:
            json_data = request.get_json(silent=True)

            if json_data:
                # Find request body parameters
                for param_name in param_names:
                    if param_name in signature.parameters and param_name.startswith("_x_body"):
                        param_type = cached_data["type_hints"].get(param_name)
                        if param_type and isinstance(param_type, type) and issubclass(param_type, BaseModel):
                            with contextlib.suppress(Exception):
                                # Create model instance directly from JSON data
                                model_instance = param_type.model_validate(json_data)
                                kwargs[param_name] = model_instance

        # Create empty model instances for required parameters that are missing
        for param_name in param_names:
            if param_name not in kwargs and param_name in signature.parameters:
                param = signature.parameters[param_name]
                if param.default is param.empty and param_name in cached_data["type_hints"]:
                    param_type = cached_data["type_hints"][param_name]
                    if isinstance(param_type, type) and issubclass(param_type, BaseModel):
                        # If it's a request body parameter and we have JSON data, try to create model instance
                        if has_request_context and param_name.startswith("_x_body") and request.is_json:
                            json_data = request.get_json(silent=True)
                            if json_data:
                                with contextlib.suppress(Exception):
                                    kwargs[param_name] = param_type.model_validate(json_data)
                                    continue

                        # Otherwise create empty instance
                        with contextlib.suppress(Exception):
                            kwargs[param_name] = param_type()

        # Use the parameter processor to handle parameter binding
        parameter_processor = ParameterProcessor(
            prefix_config=self.prefix_config,
            framework_decorator=self.framework_decorator,
        )

        # Process all parameters
        kwargs = parameter_processor.process_parameters(func, cached_data, args, kwargs)

        # Filter out any kwargs that are not in the function signature
        sig_params = signature.parameters
        valid_kwargs = {k: v for k, v in kwargs.items() if k in sig_params}

        # Check if any required parameters are missing
        for param_name, param in sig_params.items():
            if param_name not in valid_kwargs and param.default is param.empty:
                # Skip self and cls parameters
                if param_name in {"self", "cls"}:
                    continue

                # Try to create a default instance for missing parameters
                if param_name in cached_data["type_hints"]:
                    param_type = cached_data["type_hints"][param_name]
                    if isinstance(param_type, type) and issubclass(param_type, BaseModel):
                        # If it's a request body parameter and we have JSON data, try to create model instance
                        if has_request_context and param_name.startswith("_x_body") and request.is_json:
                            json_data = request.get_json(silent=True)
                            if json_data:
                                with contextlib.suppress(Exception):
                                    valid_kwargs[param_name] = param_type.model_validate(json_data)
                                    continue

                        # For required models, we need to provide default values
                        if hasattr(param_type, "model_json_schema"):
                            schema = param_type.model_json_schema()
                            required_fields = schema.get("required", [])
                            default_data = {}
                            for field in required_fields:
                                # Provide sensible defaults based on field type
                                if field in param_type.model_fields:
                                    field_info = param_type.model_fields[field]
                                    if field_info.annotation is str:
                                        default_data[field] = ""
                                    elif field_info.annotation is int:
                                        default_data[field] = 0
                                    elif field_info.annotation is float:
                                        default_data[field] = 0.0
                                    elif field_info.annotation is bool:
                                        default_data[field] = False
                                    else:
                                        default_data[field] = None

                            with contextlib.suppress(Exception):
                                valid_kwargs[param_name] = param_type.model_validate(default_data)
                        else:
                            with contextlib.suppress(Exception):
                                valid_kwargs[param_name] = param_type()

        # Call the original function with filtered kwargs
        result = func(*args, **valid_kwargs)

        # Handle response conversion using helper function
        return _handle_response(result)
