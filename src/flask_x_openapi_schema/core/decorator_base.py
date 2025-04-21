"""
Base classes and utilities for OpenAPI metadata decorators.
"""

import inspect
from collections.abc import Callable
from functools import wraps
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
    get_type_hints,
)

from flask import request
from pydantic import BaseModel

# For Python 3.10+, use typing directly; for older versions, use typing_extensions
try:
    from typing import ParamSpec  # Python 3.10+
except ImportError:
    from typing_extensions import ParamSpec  # Python < 3.10

from ..i18n.i18n_string import I18nStr, get_current_language
from ..models.base import BaseRespModel
from ..models.responses import OpenAPIMetaResponse
from .cache import (
    FUNCTION_METADATA_CACHE,
    METADATA_CACHE,
    OPENAPI_PARAMS_CACHE,
    PARAM_DETECTION_CACHE,
    extract_param_types,
    get_parameter_prefixes,
)
from .utils import _fix_references
from .config import ConventionalPrefixConfig, GLOBAL_CONFIG_HOLDER

# Type variables for function parameters and return type
P = ParamSpec("P")
R = TypeVar("R")


def preprocess_request_data(
    data: Dict[str, Any], model: Type[BaseModel]
) -> Dict[str, Any]:
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
            if (
                isinstance(field_value, str)
                and field_value.startswith("[")
                and field_value.endswith("]")
            ):
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


def _extract_parameters_from_prefixes(
    signature: inspect.Signature,
    type_hints: Dict[str, Any],
    config: Optional[ConventionalPrefixConfig] = None,
) -> Tuple[Optional[Type[BaseModel]], Optional[Type[BaseModel]], List[str]]:
    """
    Extract parameters based on prefix types from function signature.
    This function does not auto-detect parameters, but simply extracts them based on their prefixes.
    Results are cached based on the function signature and type hints.

    Args:
        signature: Function signature
        type_hints: Function type hints
        config: Optional configuration object with custom prefixes

    Returns:
        Tuple of (request_body, query_model, path_params)
    """
    # Create a cache key based on signature, type hints, and config prefixes
    # We use the signature's string representation and a frozenset of type hints items
    # For config, we use the actual prefix values rather than the object identity
    prefixes = get_parameter_prefixes(config)
    cache_key = (
        str(signature),
        str(frozenset(type_hints.items())),
        prefixes,  # Use the actual prefix values for caching
    )

    # Debug information
    import logging

    logger = logging.getLogger(__name__)
    logger.debug(
        f"Extracting parameters with prefixes={prefixes}, signature={signature}, type_hints={type_hints}"
    )

    # Check if we've already cached this extraction
    if cache_key in PARAM_DETECTION_CACHE:
        cached_result = PARAM_DETECTION_CACHE[cache_key]
        logger.debug(f"Using cached result: {cached_result}")
        return cached_result

    request_body = None
    query_model = None
    path_params = []

    # Get parameter prefixes (cached)
    body_prefix, query_prefix, path_prefix, _ = get_parameter_prefixes(config)

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
                request_body = param_type
                continue

        # Check for request_query parameter
        if param_name.startswith(query_prefix):
            param_type = type_hints.get(param_name)
            if (
                param_type
                and isinstance(param_type, type)
                and issubclass(param_type, BaseModel)
            ):
                query_model = param_type
                continue

        # Check for request_path parameter
        if param_name.startswith(path_prefix):
            # Extract the path parameter name from the parameter name
            # Format: _x_path_<param_name>
            param_suffix = param_name[path_prefix_len:]
            # Use the full suffix as the parameter name
            path_params.append(param_suffix)

    # Cache the result (limit cache size to prevent memory issues)
    if len(PARAM_DETECTION_CACHE) > 1000:  # Limit cache size
        PARAM_DETECTION_CACHE.clear()

    result = (request_body, query_model, path_params)
    PARAM_DETECTION_CACHE[cache_key] = result

    # Debug information
    logger.debug(
        f"Extracted parameters: request_body={request_body}, query_model={query_model}, path_params={path_params}"
    )

    return result


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
    responses: Optional[OpenAPIMetaResponse],
    language: Optional[str],
) -> Dict[str, Any]:
    """
    Generate OpenAPI metadata dictionary.

    Args:
        Various parameters for OpenAPI metadata

    Returns:
        OpenAPI metadata dictionary
    """
    # Debug information
    import logging

    logger = logging.getLogger(__name__)
    logger.debug(f"Generating OpenAPI metadata with request_body={actual_request_body}")
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
        logger.debug(f"Processing request body: {actual_request_body}")
        if isinstance(actual_request_body, type) and issubclass(
            actual_request_body, BaseModel
        ):
            # It's a Pydantic model
            logger.debug(
                f"Request body is a Pydantic model: {actual_request_body.__name__}"
            )
            # Check if the model has a Config with multipart/form-data flag
            is_multipart = False
            has_file_fields = False

            # Check model config for multipart/form-data flag
            if hasattr(actual_request_body, "model_config"):
                config = getattr(actual_request_body, "model_config", {})
                if isinstance(config, dict) and config.get("json_schema_extra", {}).get(
                    "multipart/form-data", False
                ):
                    is_multipart = True
            elif hasattr(actual_request_body, "Config") and hasattr(
                actual_request_body.Config, "json_schema_extra"
            ):
                config_extra = getattr(
                    actual_request_body.Config, "json_schema_extra", {}
                )
                is_multipart = config_extra.get("multipart/form-data", False)

            # Check if model has any file fields
            if hasattr(actual_request_body, "model_fields"):
                for field_name, field_info in actual_request_body.model_fields.items():
                    field_schema = getattr(field_info, "json_schema_extra", None)
                    if (
                        field_schema is not None
                        and field_schema.get("format") == "binary"
                    ):
                        has_file_fields = True
                        break

            # If model has file fields or is explicitly marked as multipart/form-data, use multipart/form-data
            content_type = (
                "multipart/form-data"
                if (is_multipart or has_file_fields)
                else "application/json"
            )
            logger.debug(f"Using content type: {content_type}")

            metadata["requestBody"] = {
                "content": {
                    content_type: {
                        "schema": {
                            "$ref": f"#/components/schemas/{actual_request_body.__name__}"
                        }
                    }
                },
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


# This function has been moved to the framework-specific decorators


class OpenAPIDecoratorBase:
    """Base class for OpenAPI metadata decorators."""

    def __init__(
        self,
        summary: Optional[Union[str, I18nStr]] = None,
        description: Optional[Union[str, I18nStr]] = None,
        tags: Optional[List[str]] = None,
        operation_id: Optional[str] = None,
        responses: Optional[OpenAPIMetaResponse] = None,
        deprecated: bool = False,
        security: Optional[List[Dict[str, List[str]]]] = None,
        external_docs: Optional[Dict[str, str]] = None,
        language: Optional[str] = None,
        prefix_config: Optional[ConventionalPrefixConfig] = None,
        framework: str = "flask",
    ):
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

    def __call__(self, func: Callable[P, R]) -> Callable[P, R]:
        """Apply the decorator to the function."""
        # Initialize the framework-specific decorator if needed
        if self.framework_decorator is None:
            if self.framework == "flask":
                # Import here to avoid circular imports
                from ..x.flask.decorators import FlaskOpenAPIDecorator

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
                from ..x.flask_restful.decorators import FlaskRestfulOpenAPIDecorator

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
                raise ValueError(f"Unsupported framework: {self.framework}")

        # Check if we've already decorated this function
        if func in FUNCTION_METADATA_CACHE:
            cached_data = FUNCTION_METADATA_CACHE[func]

            # Debug information
            import logging

            logger = logging.getLogger(__name__)
            logger.debug(f"Using cached metadata for function {func.__name__}")
            logger.debug(f"Cached metadata: {cached_data['metadata']}")

            # Create a wrapper function that reuses the cached metadata
            @wraps(func)
            def cached_wrapper(*args, **kwargs):
                return self._process_request(func, cached_data, *args, **kwargs)

            # Copy cached metadata and annotations
            cached_wrapper._openapi_metadata = cached_data["metadata"]  # type: ignore
            cached_wrapper.__annotations__ = cached_data["annotations"]

            return cast(Callable[P, R], cached_wrapper)

        # Get the function signature to find parameters with special prefixes
        signature = inspect.signature(func)
        param_names = list(signature.parameters.keys())

        # Get type hints from the function
        type_hints = get_type_hints(func)

        # Extract parameters based on prefixes
        extracted_request_body = None
        extracted_query_model = None
        extracted_path_params = []

        # Use helper function to extract parameters based on prefixes (cached)
        extracted_request_body, extracted_query_model, extracted_path_params = (
            _extract_parameters_from_prefixes(signature, type_hints, self.prefix_config)
        )

        # Use extracted parameters
        actual_request_body = extracted_request_body
        actual_query_model = extracted_query_model
        actual_path_params = extracted_path_params

        # Generate OpenAPI metadata using helper function
        # Create a cache key for metadata
        cache_key = (
            str(self.summary),
            str(self.description),
            str(self.tags) if self.tags else None,
            self.operation_id,
            self.deprecated,
            str(self.security) if self.security else None,
            str(self.external_docs) if self.external_docs else None,
            id(actual_request_body)
            if isinstance(actual_request_body, type)
            else str(actual_request_body),
            str(self.responses) if self.responses else None,
            id(actual_query_model) if actual_query_model else None,
            str(actual_path_params) if actual_path_params else None,
            self.language,
        )

        # Debug information
        import logging

        logger = logging.getLogger(__name__)
        logger.debug(
            f"Generating metadata with request_body={actual_request_body}, query_model={actual_query_model}, path_params={actual_path_params}"
        )

        # Check if we've already generated metadata for these parameters
        if cache_key in METADATA_CACHE:
            metadata = METADATA_CACHE[cache_key]
        else:
            # Generate metadata
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
                language=self.language,
            )

            # Cache the result (limit cache size to prevent memory issues)
            if len(METADATA_CACHE) > 1000:
                METADATA_CACHE.clear()
            METADATA_CACHE[cache_key] = metadata

        # Initialize parameters list
        openapi_parameters = []

        # Add parameters from query_model and path_params
        if actual_query_model or actual_path_params:
            # Create a cache key for parameters
            cache_key = (
                id(actual_query_model),
                tuple(sorted(actual_path_params)) if actual_path_params else None,
            )
            if cache_key in OPENAPI_PARAMS_CACHE:
                model_parameters = OPENAPI_PARAMS_CACHE[cache_key]
            else:
                # Create parameters for OpenAPI schema
                model_parameters = []

                # Add path parameters
                if actual_path_params:
                    for param in actual_path_params:
                        model_parameters.append(
                            {
                                "name": param,
                                "in": "path",
                                "required": True,
                                "schema": {"type": "string"},
                            }
                        )

                # Add query parameters
                if actual_query_model:
                    schema = actual_query_model.model_json_schema()
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

                        model_parameters.append(param)

                # Cache the parameters (limit cache size to prevent memory issues)
                if len(OPENAPI_PARAMS_CACHE) > 1000:  # Limit cache size
                    OPENAPI_PARAMS_CACHE.clear()
                OPENAPI_PARAMS_CACHE[cache_key] = model_parameters

            # Add parameters to metadata
            if model_parameters:
                metadata["parameters"] = model_parameters
                logger.debug(f"Added parameters to metadata: {model_parameters}")

            openapi_parameters.extend(model_parameters)

        # Add file parameters based on function signature
        file_params = []
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

        # Extract parameter types for type annotations (cached)
        param_types = extract_param_types(
            request_body_model=actual_request_body
            if isinstance(actual_request_body, type)
            and issubclass(actual_request_body, BaseModel)
            else None,
            query_model=actual_query_model,
        )

        # Get existing type hints
        existing_hints = get_type_hints(func)
        # Merge with new type hints from Pydantic models
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

        # Create a wrapper function that handles parameter binding
        @wraps(func)
        def wrapper(*args, **kwargs):
            return self._process_request(func, cached_data, *args, **kwargs)

        # Copy OpenAPI metadata to the wrapper
        wrapper._openapi_metadata = metadata  # type: ignore

        # Add type hints to the wrapper function
        wrapper.__annotations__ = merged_hints

        return cast(Callable[P, R], wrapper)

    def _process_request(
        self, func: Callable[P, R], cached_data: Dict[str, Any], *args, **kwargs
    ) -> Any:
        """Process a request using cached metadata."""
        # Extract cached data
        signature = cached_data["signature"]
        param_names = cached_data["param_names"]
        type_hints = cached_data["type_hints"]
        actual_request_body = cached_data["actual_request_body"]
        actual_query_model = cached_data["actual_query_model"]
        actual_path_params = cached_data["actual_path_params"]

        # Request-specific caching is handled by the framework-specific implementations

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
            body_prefix, query_prefix, path_prefix, file_prefix = (
                get_parameter_prefixes(self.prefix_config)
            )

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
                        kwargs = self.framework_decorator.process_request_body(
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
                        kwargs = self.framework_decorator.process_query_params(
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
                        if param_suffix in kwargs:
                            kwargs[param_name] = kwargs[param_suffix]

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

                    # Handle _x_file (default to 'file' parameter)
                    if param_suffix == "":
                        file_param_name = "file"
                    # Handle _x_file_XXX (extract XXX as parameter name)
                    elif param_suffix.startswith("_"):
                        file_param_name = param_suffix[1:]
                    else:
                        file_param_name = param_suffix

                    # Check if the file exists in request.files
                    if file_param_name in request.files:
                        file_obj = request.files[file_param_name]
                        if is_pydantic_model:
                            # Create a Pydantic model instance with the file and other form data
                            model_data = {}
                            # Add form data to model_data
                            for field_name, field_value in request.form.items():
                                model_data[field_name] = field_value
                            # Add file to model_data
                            model_data["file"] = file_obj
                            # Create model instance
                            kwargs[param_name] = param_type(**model_data)
                        else:
                            # Just pass the file directly
                            kwargs[param_name] = file_obj
                    else:
                        # If the specific file name is not found, try fallbacks
                        # First try 'file' as a common default
                        if "file" in request.files:
                            file_obj = request.files["file"]
                            if is_pydantic_model:
                                # Create a Pydantic model instance with the file and other form data
                                model_data = {}
                                # Add form data to model_data
                                for field_name, field_value in request.form.items():
                                    model_data[field_name] = field_value
                                # Add file to model_data
                                model_data["file"] = file_obj
                                # Create model instance
                                kwargs[param_name] = param_type(**model_data)
                            else:
                                # Just pass the file directly
                                kwargs[param_name] = file_obj
                        # If there's only one file, use that as a last resort
                        elif len(request.files) == 1:
                            file_obj = next(iter(request.files.values()))
                            if is_pydantic_model:
                                # Create a Pydantic model instance with the file and other form data
                                model_data = {}
                                # Add form data to model_data
                                for field_name, field_value in request.form.items():
                                    model_data[field_name] = field_value
                                # Add file to model_data
                                model_data["file"] = file_obj
                                # Create model instance
                                kwargs[param_name] = param_type(**model_data)
                            else:
                                # Just pass the file directly
                                kwargs[param_name] = file_obj

            # Process any additional framework-specific parameters
            kwargs = self.framework_decorator.process_additional_params(
                kwargs, param_names
            )

        # Filter out any kwargs that are not in the function signature
        # Get the function signature parameters once
        sig_params = signature.parameters
        valid_kwargs = {k: v for k, v in kwargs.items() if k in sig_params}

        # Call the original function with filtered kwargs
        result = func(*args, **valid_kwargs)

        # Handle response conversion using helper function
        return _handle_response(result)
