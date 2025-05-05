"""Decorators for adding OpenAPI metadata to Flask MethodView endpoints.

This module provides decorators that can be used to add OpenAPI metadata to Flask MethodView
endpoints. The decorators handle parameter binding for request data, including request body,
query parameters, path parameters, and file uploads.
"""

import io
import json
from collections.abc import Callable
from typing import Any, TypeVar

from flask import request
from pydantic import BaseModel
from werkzeug.datastructures import FileStorage

from flask_x_openapi_schema import get_logger
from flask_x_openapi_schema.core.config import ConventionalPrefixConfig
from flask_x_openapi_schema.core.decorator_base import OpenAPIDecoratorBase
from flask_x_openapi_schema.core.request_extractors import ModelFactory, request_processor
from flask_x_openapi_schema.core.request_processing import preprocess_request_data
from flask_x_openapi_schema.i18n.i18n_string import I18nStr
from flask_x_openapi_schema.models.base import BaseErrorResponse
from flask_x_openapi_schema.models.content_types import RequestContentTypes
from flask_x_openapi_schema.models.responses import OpenAPIMetaResponse


class FlaskOpenAPIDecorator:
    """OpenAPI metadata decorator for Flask MethodView.

    This class implements a decorator that adds OpenAPI metadata to Flask MethodView
    endpoints and handles parameter binding for request data.
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
        content_type: str | None = None,
        request_content_types: Any = None,
        response_content_types: Any = None,
        content_type_resolver: Callable | None = None,
    ) -> None:
        """Initialize the decorator with OpenAPI metadata parameters.

        Args:
            summary: A short summary of what the operation does
            description: A verbose explanation of the operation behavior
            tags: A list of tags for API documentation control
            operation_id: Unique string used to identify the operation
            responses: The responses the API can return
            deprecated: Declares this operation to be deprecated
            security: A declaration of which security mechanisms can be used for this operation
            external_docs: Additional external documentation
            language: Language code to use for I18nString values
            prefix_config: Configuration object for parameter prefixes
            content_type: Custom content type for request body. If None, will be auto-detected.
            request_content_types: Multiple content types for request body.
            response_content_types: Multiple content types for response body.
            content_type_resolver: Function to determine content type based on request.


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
        self.content_type = content_type
        self.request_content_types = request_content_types
        self.response_content_types = response_content_types
        self.content_type_resolver = content_type_resolver
        self.framework = "flask"
        self.default_error_response = responses.default_error_response if responses else BaseErrorResponse

        self.base_decorator = None

    def __call__(self, func: Callable) -> Callable:
        """Apply the decorator to the function.

        Args:
            func: The function to decorate

        Returns:
            The decorated function

        """
        if self.base_decorator is None:
            self.base_decorator = OpenAPIDecoratorBase(
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
                framework=self.framework,
                content_type=self.content_type,
                request_content_types=self.request_content_types,
                response_content_types=self.response_content_types,
                content_type_resolver=self.content_type_resolver,
            )
        return self.base_decorator(func)

    def extract_parameters_from_models(
        self,
        query_model: type[BaseModel] | None,
        path_params: list[str] | None,
    ) -> list[dict[str, Any]]:
        """Extract OpenAPI parameters from models.

        Args:
            query_model: The query parameter model
            path_params: List of path parameter names

        Returns:
            List of OpenAPI parameter objects

        """
        parameters = [
            {
                "name": param,
                "in": "path",
                "required": True,
                "schema": {"type": "string"},
            }
            for param in path_params
        ]

        if query_model:
            schema = query_model.model_json_schema()
            properties = schema.get("properties", {})
            required = schema.get("required", [])

            for field_name, field_schema in properties.items():
                param = {
                    "name": field_name,
                    "in": "query",
                    "required": field_name in required,
                    "schema": field_schema,
                }

                if "description" in field_schema:
                    param["description"] = field_schema["description"]

                parameters.append(param)

        return parameters

    def process_request_body(self, param_name: str, model: type[BaseModel], kwargs: dict[str, Any]) -> dict[str, Any]:
        """Process request body parameters for Flask.

        Args:
            param_name: The parameter name to bind the model instance to
            model: The Pydantic model class to use for validation
            kwargs: The keyword arguments to update

        Returns:
            Updated kwargs dictionary with the model instance

        """
        logger = get_logger(__name__)
        logger.debug(f"Processing request body for {param_name} with model {model.__name__}")

        actual_content_type = request.content_type or ""
        logger.debug(f"Actual request content type: {actual_content_type}")

        if self.content_type_resolver and hasattr(request, "args"):
            try:
                resolved_content_type = self.content_type_resolver(request)
                if resolved_content_type:
                    logger.debug(f"Resolved content type using resolver: {resolved_content_type}")
                    self.content_type = resolved_content_type
            except Exception:
                logger.exception("Error resolving content type")

        mapped_model = None
        if self.request_content_types:
            if isinstance(self.request_content_types, RequestContentTypes):
                if self.request_content_types.default_content_type:
                    self.content_type = self.request_content_types.default_content_type
                    logger.debug(f"Using default content type from RequestContentTypes: {self.content_type}")

                if self.request_content_types.content_type_resolver and hasattr(request, "args"):
                    try:
                        resolved_content_type = self.request_content_types.content_type_resolver(request)
                        if resolved_content_type:
                            logger.debug(
                                f"Resolved content type using RequestContentTypes resolver: {resolved_content_type}"
                            )
                            self.content_type = resolved_content_type
                    except Exception:
                        logger.exception("Error resolving content type from RequestContentTypes")

                for content_type, content_model in self.request_content_types.content_types.items():
                    if content_type in actual_content_type:
                        if isinstance(content_model, type) and issubclass(content_model, BaseModel):
                            logger.debug(
                                f"Found matching model for content type {content_type}: {content_model.__name__}"
                            )
                            mapped_model = content_model
                            self.content_type = content_type
                            break

                if (
                    not mapped_model
                    and self.content_type
                    and self.content_type in self.request_content_types.content_types
                ):
                    content_model = self.request_content_types.content_types[self.content_type]
                    if isinstance(content_model, type) and issubclass(content_model, BaseModel):
                        logger.debug(
                            f"Using mapped model for content type {self.content_type}: {content_model.__name__}"
                        )
                        mapped_model = content_model

        if mapped_model:
            model = mapped_model

        if self.content_type or actual_content_type:
            effective_content_type = self.content_type or actual_content_type
            logger.debug(f"Using effective content type: {effective_content_type}")

            if "multipart/form-data" in effective_content_type:
                if request.files:
                    logger.debug(f"Processing multipart/form-data with files: {list(request.files.keys())}")

                    model_data = dict(request.form.items())
                    for field_name in model.model_fields:
                        if field_name in request.files:
                            model_data[field_name] = request.files[field_name]

                    try:
                        processed_data = preprocess_request_data(model_data, model)
                        model_instance = ModelFactory.create_from_data(model, processed_data)
                        kwargs[param_name] = model_instance
                    except Exception:
                        logger.exception("Failed to create model instance from multipart data")
                    else:
                        return kwargs

            elif any(
                binary_type in effective_content_type
                for binary_type in ["image/", "audio/", "video/", "application/octet-stream"]
            ):
                logger.debug(f"Processing binary content type: {effective_content_type}")

                try:
                    raw_data = request.get_data()
                    file_name = (
                        request.headers.get("Content-Disposition", "").split("filename=")[-1].strip('"') or "file"
                    )
                    file_obj = FileStorage(
                        stream=io.BytesIO(raw_data),
                        filename=file_name,
                        content_type=effective_content_type,
                    )

                    if hasattr(model, "model_fields") and "file" in model.model_fields:
                        model_data = {"file": file_obj}
                        from flask_x_openapi_schema.core.request_processing import preprocess_request_data

                        processed_data = preprocess_request_data(model_data, model)
                        model_instance = ModelFactory.create_from_data(model, processed_data)
                        kwargs[param_name] = model_instance
                        return kwargs

                    model_instance = model()
                    model_instance._raw_data = raw_data
                    kwargs[param_name] = model_instance
                except Exception:
                    logger.exception("Failed to process binary content")
                else:
                    return kwargs

            elif "multipart/mixed" in effective_content_type:
                logger.debug("Processing multipart/mixed content type")

                try:
                    boundary = request.content_type.split("boundary=")[-1].strip()
                    parts = request.get_data().decode("latin1").split(f"--{boundary}")

                    parsed_parts = {}
                    for part in parts:
                        if not part.strip() or part.strip() == "--":
                            continue

                        if "\r\n\r\n" in part:
                            headers_str, content = part.split("\r\n\r\n", 1)
                            headers = {}
                            for header_line in headers_str.split("\r\n"):
                                if ":" in header_line:
                                    key, value = header_line.split(":", 1)
                                    headers[key.strip().lower()] = value.strip()

                            content_type = headers.get("content-type", "")
                            if "application/json" in content_type:
                                try:
                                    parsed_parts["json"] = json.loads(content)
                                except Exception:
                                    parsed_parts["json"] = content
                            elif any(
                                binary_type in content_type
                                for binary_type in ["image/", "audio/", "video/", "application/octet-stream"]
                            ):
                                parsed_parts["binary"] = content.encode("latin1")
                            else:
                                parsed_parts["text"] = content

                    if parsed_parts:
                        model_instance = model()
                        for key, value in parsed_parts.items():
                            if hasattr(model, key):
                                setattr(model_instance, key, value)
                        kwargs[param_name] = model_instance
                        return kwargs
                except Exception:
                    logger.exception("Failed to process multipart/mixed content")

        model_instance = request_processor.process_request_data(request, model, param_name)

        if model_instance:
            kwargs[param_name] = model_instance
            return kwargs

        logger.warning(f"No valid request data found for {param_name}, creating default instance")

        json_data = request.get_json(silent=True)

        if json_data:
            try:
                model_instance = model.model_validate(json_data)
                kwargs[param_name] = model_instance
            except Exception as e:
                logger.exception(f"Failed to create model instance from JSON for {param_name}", exc_info=e)
            else:
                return kwargs

        try:
            model_instance = model()
            kwargs[param_name] = model_instance
        except Exception:
            logger.exception("Failed to create empty model instance")

        return kwargs

    def process_query_params(self, param_name: str, model: type[BaseModel], kwargs: dict[str, Any]) -> dict[str, Any]:
        """Process query parameters for Flask.

        Args:
            param_name: The parameter name to bind the model instance to
            model: The Pydantic model class to use for validation
            kwargs: The keyword arguments to update

        Returns:
            Updated kwargs dictionary with the model instance

        """
        query_data = {}
        model_fields = model.model_fields

        for field_name in model_fields:
            if field_name in request.args:
                query_data[field_name] = request.args.get(field_name)

        model_instance = model(**query_data)

        kwargs[param_name] = model_instance

        return kwargs

    def process_additional_params(self, kwargs: dict[str, Any], param_names: list[str]) -> dict[str, Any]:
        """Process additional framework-specific parameters.

        Args:
            kwargs: The keyword arguments to update
            param_names: List of parameter names that have been processed

        Returns:
            Updated kwargs dictionary

        """
        logger = get_logger(__name__)
        logger.debug(f"Processing additional parameters with kwargs keys: {list(kwargs.keys())}")
        logger.debug(f"Processed parameter names: {param_names}")
        return kwargs


F = TypeVar("F", bound=Callable[..., Any])


def openapi_metadata(
    *,
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
    content_type: str | None = None,
    request_content_types: Any = None,
    response_content_types: Any = None,
    content_type_resolver: Callable | None = None,
) -> Callable[[F], F]:
    """Decorator to add OpenAPI metadata to a Flask MethodView endpoint.

    This decorator adds OpenAPI metadata to a Flask MethodView endpoint and handles
    parameter binding for request data. It automatically binds request body, query parameters,
    path parameters, and file uploads to function parameters based on their type annotations
    and parameter name prefixes.

    Args:
        summary: A short summary of what the operation does
        description: A verbose explanation of the operation behavior
        tags: A list of tags for API documentation control
        operation_id: Unique string used to identify the operation
        responses: The responses the API can return
        deprecated: Declares this operation to be deprecated
        security: A declaration of which security mechanisms can be used for this operation
        external_docs: Additional external documentation
        language: Language code to use for I18nString values (default: current language)
        prefix_config: Configuration object for parameter prefixes
        content_type: Custom content type for request body. If None, will be auto-detected.
        request_content_types: Multiple content types for request body.
        response_content_types: Multiple content types for response body.
        content_type_resolver: Function to determine content type based on request.


    Returns:
        The decorated function with OpenAPI metadata attached

    Examples:
        >>> from flask.views import MethodView
        >>> from flask_x_openapi_schema.x.flask import openapi_metadata
        >>> from flask_x_openapi_schema import OpenAPIMetaResponse, OpenAPIMetaResponseItem
        >>> from pydantic import BaseModel, Field
        >>>
        >>> class ItemRequest(BaseModel):
        ...     name: str = Field(..., description="Item name")
        ...     price: float = Field(..., description="Item price")
        >>>
        >>> class ItemResponse(BaseModel):
        ...     id: str = Field(..., description="Item ID")
        ...     name: str = Field(..., description="Item name")
        ...     price: float = Field(..., description="Item price")
        >>>
        >>> class ItemView(MethodView):
        ...     @openapi_metadata(
        ...         summary="Create a new item",
        ...         description="Create a new item with the provided information",
        ...         tags=["items"],
        ...         operation_id="createItem",
        ...         responses=OpenAPIMetaResponse(
        ...             responses={
        ...                 "201": OpenAPIMetaResponseItem(model=ItemResponse, description="Item created successfully"),
        ...                 "400": OpenAPIMetaResponseItem(description="Invalid request data"),
        ...             }
        ...         ),
        ...     )
        ...     def post(self, _x_body: ItemRequest):
        ...         item = {"id": "123", "name": _x_body.name, "price": _x_body.price}
        ...         return item, 201

    """
    return FlaskOpenAPIDecorator(
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
        content_type=content_type,
        request_content_types=request_content_types,
        response_content_types=response_content_types,
        content_type_resolver=content_type_resolver,
    )
