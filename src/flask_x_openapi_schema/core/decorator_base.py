"""Base classes and utilities for OpenAPI metadata decorators.

This module provides the core functionality for creating OpenAPI metadata decorators
that can be used with Flask and Flask-RESTful applications. It includes utilities for
parameter extraction, metadata generation, and request processing.

The main class is OpenAPIDecoratorBase, which serves as the foundation for framework-specific
decorator implementations. It handles parameter binding, metadata caching, and OpenAPI
schema generation.
"""

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

try:
    from typing import ParamSpec
except ImportError:
    from typing_extensions import ParamSpec

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

P = ParamSpec("P")
R = TypeVar("R")


logger = logging.getLogger(__name__)


def _extract_parameters_from_prefixes(
    signature: inspect.Signature,
    type_hints: dict[str, Any],
    config: ConventionalPrefixConfig | None = None,
) -> tuple[type[BaseModel] | None, type[BaseModel] | None, list[str]]:
    """Extract parameters based on prefix types from function signature.

    This function does not auto-detect parameters, but simply extracts them based on their prefixes.

    Args:
        signature: Function signature to extract parameters from.
        type_hints: Type hints dictionary from the function.
        config: Optional configuration object with custom prefixes.

    Returns:
        tuple: A tuple containing:
            * request_body (BaseModel or None): The request body model if found.
            * query_model (BaseModel or None): The query parameters model if found.
            * path_params (list of str): List of path parameter names.

    Examples:
        >>> from inspect import signature
        >>> from typing import get_type_hints
        >>> from pydantic import BaseModel
        >>> class QueryModel(BaseModel):
        ...     q: str
        >>> def example(_x_query_params: QueryModel, _x_path_id: str):
        ...     pass
        >>> sig = signature(example)
        >>> hints = get_type_hints(example)
        >>> body, query, path = _extract_parameters_from_prefixes(sig, hints)
        >>> body is None
        True
        >>> query.__name__
        'QueryModel'
        >>> path
        ['id']

    """
    import logging

    logger = logging.getLogger(__name__)

    prefixes = get_parameter_prefixes(config)
    logger.debug(f"Extracting parameters with prefixes={prefixes}, signature={signature}, type_hints={type_hints}")

    request_body = None
    query_model = None
    path_params = []

    body_prefix, query_prefix, path_prefix, _ = prefixes

    path_prefix_len = len(path_prefix) + 1

    skip_params = {"self", "cls"}

    for param_name in signature.parameters:
        if param_name in skip_params:
            continue

        if param_name.startswith(body_prefix):
            param_type = type_hints.get(param_name)
            if param_type and isinstance(param_type, type) and issubclass(param_type, BaseModel):
                request_body = param_type
                continue

        if param_name.startswith(query_prefix):
            param_type = type_hints.get(param_name)
            if param_type and isinstance(param_type, type) and issubclass(param_type, BaseModel):
                query_model = param_type
                continue

        if param_name.startswith(path_prefix):
            param_suffix = param_name[path_prefix_len:]

            path_params.append(param_suffix)

    result = (request_body, query_model, path_params)

    logger.debug(
        f"Extracted parameters: request_body={request_body}, query_model={query_model}, path_params={path_params}",
    )

    return result


def _process_i18n_value(value: str | I18nStr | None, language: str | None) -> str | None:
    """Process an I18nString value to get the string for the current language.

    Args:
        value: The value to process (string or I18nString).
        language: The language to use, or None to use the current language.

    Returns:
        str or None: The processed string value for the specified language,
            or the original string if the input is not an I18nStr.
            Returns None if the input value is None.

    Examples:
        >>> from flask_x_openapi_schema.i18n.i18n_string import I18nStr
        >>> _process_i18n_value("Hello", None)
        'Hello'
        >>> i18n_str = I18nStr({"en": "Hello", "zh": "你好"})
        >>> _process_i18n_value(i18n_str, "en")
        'Hello'
        >>> _process_i18n_value(i18n_str, "zh")
        '你好'
        >>> _process_i18n_value(None, "en") is None
        True

    """
    if value is None:
        return None

    current_lang = language or get_current_language()

    if isinstance(value, I18nStr):
        return value.get(current_lang)
    return value


def _generate_openapi_metadata(
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
    """Generate OpenAPI metadata dictionary for API endpoints.

    Creates a dictionary containing OpenAPI metadata based on the provided parameters.
    Handles internationalization of strings and special processing for request bodies.

    Args:
        summary: Short summary of the endpoint, can be an I18nStr for localization.
        description: Detailed description of the endpoint, can be an I18nStr.
        tags: List of tags to categorize the endpoint.
        operation_id: Unique identifier for the operation.
        deprecated: Whether the endpoint is deprecated.
        security: Security requirements for the endpoint.
        external_docs: External documentation references.
        actual_request_body: Request body model or schema dictionary.
        responses: Response models configuration.
        language: Language code to use for I18nStr values.

    Returns:
        dict: OpenAPI metadata dictionary ready to be included in the schema.

    Examples:
        >>> from pydantic import BaseModel
        >>> from flask_x_openapi_schema.models.responses import OpenAPIMetaResponse
        >>> class User(BaseModel):
        ...     name: str
        >>> metadata = _generate_openapi_metadata(
        ...     summary="Create user",
        ...     description="Create a new user",
        ...     tags=["users"],
        ...     operation_id="createUser",
        ...     deprecated=False,
        ...     security=None,
        ...     external_docs=None,
        ...     actual_request_body=User,
        ...     responses=None,
        ...     language=None,
        ... )
        >>> "summary" in metadata
        True
        >>> "tags" in metadata
        True

    """
    import logging

    logger = logging.getLogger(__name__)
    logger.debug(f"Generating OpenAPI metadata with request_body={actual_request_body}")
    metadata: dict[str, Any] = {}

    current_lang = language or get_current_language()

    if summary is not None:
        metadata["summary"] = _process_i18n_value(summary, current_lang)
    if description is not None:
        metadata["description"] = _process_i18n_value(description, current_lang)

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

    if actual_request_body:
        logger.debug(f"Processing request body: {actual_request_body}")
        if isinstance(actual_request_body, type) and issubclass(actual_request_body, BaseModel):
            logger.debug(f"Request body is a Pydantic model: {actual_request_body.__name__}")

            is_multipart = False
            has_file_fields = False

            if hasattr(actual_request_body, "model_config"):
                config = getattr(actual_request_body, "model_config", {})
                if isinstance(config, dict) and config.get("json_schema_extra", {}).get("multipart/form-data", False):
                    is_multipart = True
            elif hasattr(actual_request_body, "Config") and hasattr(actual_request_body.Config, "json_schema_extra"):
                config_extra = getattr(actual_request_body.Config, "json_schema_extra", {})
                is_multipart = config_extra.get("multipart/form-data", False)

            if hasattr(actual_request_body, "model_fields"):
                for field_info in actual_request_body.model_fields.values():
                    field_schema = getattr(field_info, "json_schema_extra", None)
                    if field_schema is not None and field_schema.get("format") == "binary":
                        has_file_fields = True
                        break

            content_type = "multipart/form-data" if (is_multipart or has_file_fields) else "application/json"
            logger.debug(f"Using content type: {content_type}")

            metadata["requestBody"] = {
                "content": {content_type: {"schema": {"$ref": f"#/components/schemas/{actual_request_body.__name__}"}}},
                "required": True,
            }
            logger.debug(f"Added requestBody to metadata: {metadata['requestBody']}")
        else:
            logger.debug(f"Request body is a dict: {actual_request_body}")
            metadata["requestBody"] = actual_request_body

    if responses:
        metadata["responses"] = responses.to_openapi_dict()

    return metadata


def _handle_response(result: Any) -> Any:
    """Handle response conversion for BaseRespModel instances.

    Converts BaseRespModel instances to HTTP responses. Handles both direct model
    returns and tuple returns with status codes.

    Args:
        result: Function result to process.

    Returns:
        Any: Processed result ready for Flask response handling.
            - If result is a BaseRespModel, returns result.to_response()
            - If result is a tuple with a BaseRespModel as first element, processes accordingly
            - Otherwise returns the original result unchanged

    Examples:
        >>> from flask_x_openapi_schema.models.base import BaseRespModel
        >>> class TestResponse(BaseRespModel):
        ...     def to_response(self, status_code=200):
        ...         return {"data": "test"}, status_code
        >>> resp = TestResponse()
        >>> _handle_response(resp)
        ({'data': 'test'}, 200)
        >>> _handle_response((resp, 201))
        ({'data': 'test'}, 201)
        >>> _handle_response("plain string")
        'plain string'

    """
    if isinstance(result, BaseRespModel):
        return result.to_response()
    if isinstance(result, tuple) and len(result) >= 1 and isinstance(result[0], BaseRespModel):
        model = result[0]
        if len(result) >= 2 and isinstance(result[1], int):  # noqa: PLR2004
            return model.to_response(result[1])

        return model.to_response()

    return result


def _detect_file_parameters(
    param_names: list[str],
    func_annotations: dict[str, Any],
    config: ConventionalPrefixConfig | None = None,
) -> list[dict[str, Any]]:
    """Detect file parameters from function signature.

    Identifies parameters that represent file uploads based on naming conventions
    and type annotations. Uses the request_file_prefix from the configuration to
    identify file parameters.

    Args:
        param_names: List of parameter names from the function signature.
        func_annotations: Function type annotations dictionary.
        config: Optional configuration object with custom prefixes.

    Returns:
        list: List of dictionaries containing file parameter metadata for OpenAPI schema.
            Each dictionary includes name, location (in), required status, type, and description.

    Examples:
        >>> from flask_x_openapi_schema.core.config import ConventionalPrefixConfig
        >>> config = ConventionalPrefixConfig()
        >>> names = ["_x_file_profile_image", "other_param"]
        >>> annotations = {"_x_file_profile_image": str}
        >>> params = _detect_file_parameters(names, annotations, config)
        >>> len(params)
        1
        >>> params[0]["name"]
        'image'
        >>> params[0]["type"]
        'file'

    """
    file_params = []

    prefix_config = config or GLOBAL_CONFIG_HOLDER.get()
    file_prefix = prefix_config.request_file_prefix
    file_prefix_len = len(file_prefix) + 1

    for param_name in param_names:
        if not param_name.startswith(file_prefix):
            continue

        param_type = func_annotations.get(param_name)

        param_suffix = param_name[file_prefix_len:]
        file_param_name = param_suffix.split("_", 1)[1] if "_" in param_suffix else "file"

        file_description = f"File upload for {file_param_name}"

        if param_type and isinstance(param_type, type) and issubclass(param_type, BaseModel):  # noqa: SIM102
            if hasattr(param_type, "model_fields") and "file" in param_type.model_fields:
                field_info = param_type.model_fields["file"]
                if field_info.description:
                    file_description = field_info.description

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
    """Base class for OpenAPI metadata decorators.

    This class provides the foundation for framework-specific OpenAPI metadata decorators.
    It handles parameter extraction, metadata generation, and request processing in a
    framework-agnostic way, delegating framework-specific operations to subclasses.

    The decorator adds OpenAPI metadata to API endpoint functions and handles parameter
    binding between HTTP requests and function parameters based on naming conventions.

    Attributes:
        summary (str or I18nStr): Short summary of the endpoint.
        description (str or I18nStr): Detailed description of the endpoint.
        tags (list): List of tags to categorize the endpoint.
        operation_id (str): Unique identifier for the operation.
        responses (OpenAPIMetaResponse): Response models configuration.
        deprecated (bool): Whether the endpoint is deprecated.
        security (list): Security requirements for the endpoint.
        external_docs (dict): External documentation references.
        language (str): Language code to use for I18nStr values.
        prefix_config (ConventionalPrefixConfig): Configuration for parameter prefixes.
        framework (str): Framework name ('flask' or 'flask_restful').
        framework_decorator: Framework-specific decorator instance.

    """

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
        """Initialize the decorator with OpenAPI metadata parameters.

        Args:
            summary: Short summary of the endpoint, can be an I18nStr for localization.
            description: Detailed description of the endpoint, can be an I18nStr.
            tags: List of tags to categorize the endpoint.
            operation_id: Unique identifier for the operation.
            responses: Response models configuration.
            deprecated: Whether the endpoint is deprecated. Defaults to False.
            security: Security requirements for the endpoint.
            external_docs: External documentation references.
            language: Language code to use for I18nStr values.
            prefix_config: Configuration for parameter prefixes.
            framework: Framework name ('flask' or 'flask_restful'). Defaults to "flask".

        """
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

        self.framework_decorator = None

    def _initialize_framework_decorator(self) -> None:
        """Initialize the framework-specific decorator.

        This method uses lazy loading to avoid circular imports. It creates the appropriate
        framework-specific decorator based on the 'framework' attribute.

        Raises:
            ValueError: If an unsupported framework is specified.

        """
        if self.framework_decorator is None:
            if self.framework == "flask":
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

        @wraps(func)
        def cached_wrapper(*args, **kwargs) -> Any:
            signature = cached_data["signature"]
            param_names = cached_data["param_names"]

            for param_name in param_names:
                if param_name not in kwargs and param_name in signature.parameters:
                    param = signature.parameters[param_name]
                    if param.default is param.empty and param_name in cached_data["type_hints"]:
                        param_type = cached_data["type_hints"][param_name]
                        if isinstance(param_type, type) and issubclass(param_type, BaseModel):
                            kwargs[param_name] = param_type()

            return self._process_request(func, cached_data, *args, **kwargs)

        cached_wrapper._openapi_metadata = cached_data["metadata"]
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
        _cache_key: tuple,
        actual_request_body: type[BaseModel] | dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Generate OpenAPI metadata for an endpoint.

        This method delegates to the module-level _generate_openapi_metadata function
        using the decorator's attributes.

        Args:
            _cache_key: Cache key for metadata (not used in simplified cache system).
            actual_request_body: Request body model or dict.

        Returns:
            dict: OpenAPI metadata dictionary ready to be included in the schema.

        """
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

        if actual_query_model or actual_path_params:
            model_parameters = self._get_or_generate_model_parameters(actual_query_model, actual_path_params)
            if model_parameters:
                logger.debug(f"Added parameters to metadata: {model_parameters}")
                openapi_parameters.extend(model_parameters)

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
        model_parameters = []

        if path_params:
            model_parameters.extend(self._generate_path_parameters(path_params))

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
            fixed_schema = _fix_references(field_schema)
            param = {
                "name": field_name,
                "in": "query",
                "required": field_name in required,
                "schema": fixed_schema,
            }

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

        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            return self._process_request(func, cached_data, *args, **kwargs)

        wrapper._openapi_metadata = metadata

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
        self._initialize_framework_decorator()

        if func in FUNCTION_METADATA_CACHE:
            cached_data = FUNCTION_METADATA_CACHE[func]
            return self._create_cached_wrapper(func, cached_data)

        signature = inspect.signature(func)
        param_names = list(signature.parameters.keys())

        type_hints = get_type_hints(func)

        actual_request_body, actual_query_model, actual_path_params = self._extract_parameters(signature, type_hints)

        logger.debug(
            f"Generating metadata with request_body={actual_request_body}, query_model={actual_query_model}, path_params={actual_path_params}",
        )

        cache_key = self._generate_metadata_cache_key(actual_request_body, actual_query_model, actual_path_params)

        metadata = self._get_or_generate_metadata(cache_key, actual_request_body)

        func_annotations = get_type_hints(func)
        openapi_parameters = self._generate_openapi_parameters(
            actual_query_model, actual_path_params, param_names, func_annotations
        )

        if any(param.get("in") == "formData" for param in openapi_parameters):
            metadata["consumes"] = ["multipart/form-data"]

        if openapi_parameters:
            metadata["parameters"] = openapi_parameters

        func._openapi_metadata = metadata

        param_types = {}

        if (
            actual_request_body
            and isinstance(actual_request_body, type)
            and issubclass(actual_request_body, BaseModel)
            and hasattr(actual_request_body, "model_fields")
        ):
            param_types.update(
                {field_name: field.annotation for field_name, field in actual_request_body.model_fields.items()}
            )

        if actual_query_model and hasattr(actual_query_model, "model_fields"):
            param_types.update(
                {field_name: field.annotation for field_name, field in actual_query_model.model_fields.items()}
            )

        existing_hints = get_type_hints(func)
        merged_hints = {**existing_hints, **param_types}

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

        return self._create_function_wrapper(func, cached_data, metadata, merged_hints)

    def _process_request(self, func: Callable[P, R], cached_data: dict[str, Any], *args, **kwargs) -> Any:
        """Process a request using cached metadata.

        This method uses the ParameterProcessor to handle parameter binding using the Strategy pattern.
        It extracts parameters from the request context, binds them to function parameters,
        and handles model validation and conversion.

        Args:
            func: The decorated function to call.
            cached_data: Cached metadata and other information about the function.
            args: Positional arguments to the function.
            kwargs: Keyword arguments to the function.

        Returns:
            Any: The result of calling the function with bound parameters,
                processed by _handle_response if needed.

        """
        signature = cached_data["signature"]
        param_names = cached_data.get("param_names", [])

        from flask import request

        has_request_context = False
        with contextlib.suppress(RuntimeError):
            has_request_context = bool(request)

        if has_request_context and request.method == "POST" and request.is_json:
            json_data = request.get_json(silent=True)

            if json_data:
                for param_name in param_names:
                    if param_name in signature.parameters and param_name.startswith("_x_body"):
                        param_type = cached_data["type_hints"].get(param_name)
                        if param_type and isinstance(param_type, type) and issubclass(param_type, BaseModel):
                            with contextlib.suppress(Exception):
                                model_instance = param_type.model_validate(json_data)
                                kwargs[param_name] = model_instance

        for param_name in param_names:
            if param_name not in kwargs and param_name in signature.parameters:
                param = signature.parameters[param_name]
                if param.default is param.empty and param_name in cached_data["type_hints"]:
                    param_type = cached_data["type_hints"][param_name]
                    if isinstance(param_type, type) and issubclass(param_type, BaseModel):
                        if has_request_context and param_name.startswith("_x_body") and request.is_json:
                            json_data = request.get_json(silent=True)
                            if json_data:
                                with contextlib.suppress(Exception):
                                    kwargs[param_name] = param_type.model_validate(json_data)
                                    continue

                        with contextlib.suppress(Exception):
                            kwargs[param_name] = param_type()

        parameter_processor = ParameterProcessor(
            prefix_config=self.prefix_config,
            framework_decorator=self.framework_decorator,
        )

        kwargs = parameter_processor.process_parameters(func, cached_data, args, kwargs)

        sig_params = signature.parameters
        valid_kwargs = {k: v for k, v in kwargs.items() if k in sig_params}

        for param_name, param in sig_params.items():
            if param_name not in valid_kwargs and param.default is param.empty:
                if param_name in {"self", "cls"}:
                    continue

                if param_name in cached_data["type_hints"]:
                    param_type = cached_data["type_hints"][param_name]
                    if isinstance(param_type, type) and issubclass(param_type, BaseModel):
                        if has_request_context and param_name.startswith("_x_body") and request.is_json:
                            json_data = request.get_json(silent=True)
                            if json_data:
                                with contextlib.suppress(Exception):
                                    valid_kwargs[param_name] = param_type.model_validate(json_data)
                                    continue

                        if hasattr(param_type, "model_json_schema"):
                            schema = param_type.model_json_schema()
                            required_fields = schema.get("required", [])
                            default_data = {}
                            for field in required_fields:
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

        result = func(*args, **valid_kwargs)

        return _handle_response(result)
