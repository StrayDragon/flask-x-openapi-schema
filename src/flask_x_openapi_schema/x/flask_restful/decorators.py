"""Decorators for adding OpenAPI metadata to Flask-RESTful Resource endpoints.

This module provides decorators and utilities for adding OpenAPI metadata to Flask-RESTful
Resource class methods. It enables automatic parameter binding, request validation, and
OpenAPI schema generation for Flask-RESTful APIs.

The main decorator `openapi_metadata` can be applied to Resource methods to add OpenAPI
metadata and enable automatic parameter binding based on type annotations.

Examples:
    Basic usage with Flask-RESTful Resource:

    >>> from flask_restful import Resource
    >>> from flask_x_openapi_schema.x.flask_restful import openapi_metadata
    >>> from pydantic import BaseModel, Field
    >>>
    >>> class UserModel(BaseModel):
    ...     name: str = Field(..., description="User name")
    ...     age: int = Field(..., description="User age")
    >>>
    >>> class UserResource(Resource):
    ...     @openapi_metadata(summary="Create user", tags=["users"])
    ...     def post(self, _x_body: UserModel):
    ...         return {"name": _x_body.name, "age": _x_body.age}, 201

"""

import logging
from collections.abc import Callable
from typing import Any, TypeVar

from pydantic import BaseModel

from flask_x_openapi_schema.core.config import ConventionalPrefixConfig
from flask_x_openapi_schema.i18n.i18n_string import I18nStr
from flask_x_openapi_schema.models.responses import OpenAPIMetaResponse


class FlaskRestfulOpenAPIDecorator:
    """OpenAPI metadata decorator for Flask-RESTful Resource.

    This class implements the decorator functionality for adding OpenAPI metadata
    to Flask-RESTful Resource methods. It handles parameter binding, request processing,
    and OpenAPI schema generation.

    Attributes:
        summary (str | I18nStr | None): A short summary of what the operation does.
        description (str | I18nStr | None): A verbose explanation of the operation behavior.
        tags (list[str] | None): A list of tags for API documentation control.
        operation_id (str | None): Unique string used to identify the operation.
        responses (OpenAPIMetaResponse | None): The responses the API can return.
        deprecated (bool): Declares this operation to be deprecated.
        security (list[dict[str, list[str]]] | None): Security mechanisms for this operation.
        external_docs (dict[str, str] | None): Additional external documentation.
        language (str | None): Language code to use for I18nString values.
        prefix_config (ConventionalPrefixConfig | None): Configuration for parameter prefixes.
        framework (str): The framework being used ('flask_restful').
        base_decorator (OpenAPIDecoratorBase | None): The base decorator instance.
        parsed_args (Any | None): Parsed arguments from request parser.

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
    ) -> None:
        """Initialize the decorator with OpenAPI metadata parameters.

        Args:
            summary: A short summary of what the operation does.
            description: A verbose explanation of the operation behavior.
            tags: A list of tags for API documentation control.
            operation_id: Unique string used to identify the operation.
            responses: The responses the API can return.
            deprecated: Declares this operation to be deprecated.
            security: A declaration of which security mechanisms can be used for this operation.
            external_docs: Additional external documentation.
            language: Language code to use for I18nString values.
            prefix_config: Configuration object for parameter prefixes.

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
        self.framework = "flask_restful"

        self.base_decorator = None
        self.parsed_args = None

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """Apply the decorator to the function.

        Args:
            func: The function to decorate.

        Returns:
            The decorated function.

        """
        if self.base_decorator is None:
            from flask_x_openapi_schema.core.decorator_base import OpenAPIDecoratorBase

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
            )
        return self.base_decorator(func)

    def extract_parameters_from_models(
        self,
        query_model: type[BaseModel] | None,
        path_params: list[str] | None,
    ) -> list[dict[str, Any]]:
        """Extract OpenAPI parameters from models.

        Converts Pydantic models and path parameters into OpenAPI parameter objects.

        Args:
            query_model: Pydantic model for query parameters.
            path_params: List of path parameter names.

        Returns:
            List of OpenAPI parameter objects.

        """
        parameters = []

        if path_params:
            parameters.extend(
                [
                    {
                        "name": param,
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                    }
                    for param in path_params
                ],
            )

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
        """Process request body parameters for Flask-RESTful.

        Args:
            param_name: The parameter name to bind the model instance to
            model: The Pydantic model class to use for validation
            kwargs: The keyword arguments to update

        Returns:
            Updated kwargs dictionary with the model instance

        """
        from flask_x_openapi_schema.core.request_extractors import ModelFactory, request_processor, safe_operation

        logger = logging.getLogger(__name__)
        logger.debug(f"Processing request body for {param_name} with model {model.__name__}")

        has_file_fields = self._check_for_file_fields(model)

        from flask import request

        if has_file_fields and request.files:
            model_instance = self._process_file_upload_model(model)
            kwargs[param_name] = model_instance
            return kwargs

        parser = self._get_or_create_parser(model)

        self.parsed_args = parser.parse_args()

        from flask import request

        json_model_instance = request_processor.process_request_data(request, model, param_name)

        if json_model_instance:
            logger.debug(f"Successfully created model instance from JSON for {param_name}")
            kwargs[param_name] = json_model_instance
            self.parsed_args = None
            return kwargs

        if self.parsed_args:
            try:
                from flask_x_openapi_schema.core.request_processing import preprocess_request_data

                processed_data = preprocess_request_data(self.parsed_args, model)

                model_instance = safe_operation(
                    lambda: ModelFactory.create_from_data(model, processed_data), fallback=None
                )

                if model_instance:
                    logger.debug(f"Successfully created model instance from reqparse for {param_name}")
                    kwargs[param_name] = model_instance
                    return kwargs
            except Exception:
                logger.exception("Error processing reqparse data")

        logger.warning(f"No valid request data found for {param_name}, creating default instance")

        try:
            model_instance = safe_operation(lambda: model(), fallback=None)
            if model_instance:
                logger.debug(f"Created empty model instance for {param_name}")
                kwargs[param_name] = model_instance
        except Exception:
            logger.exception("Failed to create default model instance")

        return kwargs

    def _check_for_file_fields(self, model: type[BaseModel]) -> bool:
        """Check if a model contains file upload fields.

        Args:
            model: The model to check

        Returns:
            True if the model has file fields, False otherwise

        """
        import inspect

        from flask_x_openapi_schema.models.file_models import FileField

        if not hasattr(model, "model_fields"):
            return False

        for field_info in model.model_fields.values():
            field_type = field_info.annotation
            if inspect.isclass(field_type) and issubclass(field_type, FileField):
                return True

        return False

    def _process_file_upload_model(self, model: type[BaseModel]) -> BaseModel:
        """Process a file upload model with form data and files.

        Args:
            model: The model class to instantiate

        Returns:
            An instance of the model with file data

        """
        import inspect

        from flask import request

        from flask_x_openapi_schema.models.file_models import FileField

        model_data = dict(request.form.items())

        for field_name, field_info in model.model_fields.items():
            field_type = field_info.annotation
            if inspect.isclass(field_type) and issubclass(field_type, FileField):
                if field_name in request.files:
                    model_data[field_name] = request.files[field_name]
                elif "file" in request.files and field_name == "file":
                    model_data[field_name] = request.files["file"]

        return model(**model_data)

    def _get_or_create_parser(self, model: type[BaseModel]) -> Any:
        """Create a parser for the model.

        Args:
            model: The model to create a parser for

        Returns:
            A RequestParser instance for the model

        """
        from flask_x_openapi_schema.x.flask_restful.utils import create_reqparse_from_pydantic

        return create_reqparse_from_pydantic(model=model)

    def _create_model_from_args(self, model: type[BaseModel], args: dict) -> BaseModel:
        """Create a model instance from parsed arguments.

        Args:
            model: The model class to instantiate
            args: The parsed arguments

        Returns:
            An instance of the model

        """
        from flask_x_openapi_schema.core.request_extractors import ModelFactory, safe_operation
        from flask_x_openapi_schema.core.request_processing import preprocess_request_data

        logger = logging.getLogger(__name__)
        logger.debug(f"Creating model instance for {model.__name__} from args")

        processed_data = preprocess_request_data(args, model)
        logger.debug("Processed data", extra={"processed_data": processed_data})

        model_instance = safe_operation(lambda: ModelFactory.create_from_data(model, processed_data), fallback=None)

        if model_instance:
            logger.debug("Successfully created model instance")
            return model_instance

        logger.warning("Failed to create model instance from args, creating empty instance")

        try:
            model_instance = model()
            logger.debug("Created empty model instance")
        except Exception as empty_err:
            logger.exception("Failed to create empty model instance")

            if hasattr(model, "model_json_schema"):
                schema = model.model_json_schema()
                required_fields = schema.get("required", [])
                default_data = {}

                for field in required_fields:
                    if field in model.model_fields:
                        field_info = model.model_fields[field]
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

                try:
                    model_instance = model.model_validate(default_data)
                    logger.debug("Created model instance with default values")
                except Exception:
                    logger.exception("Failed to create model instance with default values")
                else:
                    return model_instance

            error_msg = f"Failed to create instance of {model.__name__}"
            raise ValueError(error_msg) from empty_err
        else:
            return model_instance

    def process_query_params(self, param_name: str, model: type[BaseModel], kwargs: dict[str, Any]) -> dict[str, Any]:
        """Process query parameters for Flask-RESTful.

        Args:
            param_name: The parameter name to bind the model instance to.
            model: The Pydantic model class to use for validation.
            kwargs: The keyword arguments to update.

        Returns:
            Updated kwargs dictionary with the model instance.

        """
        logger = logging.getLogger(__name__)

        if self.parsed_args:
            model_instance = self._create_model_from_args(model, self.parsed_args)
            kwargs[param_name] = model_instance
            return kwargs

        parser = self._get_or_create_query_parser(model)

        self.parsed_args = parser.parse_args()

        try:
            model_instance = self._create_model_from_args(model, self.parsed_args)
            kwargs[param_name] = model_instance
        except Exception:
            logger.exception(f"Failed to create model instance for {param_name}")

            try:
                model_instance = model()
                logger.debug(f"Created empty model instance for {param_name}")
                kwargs[param_name] = model_instance
            except Exception:
                logger.exception(f"Failed to create empty model instance for {param_name}")

        return kwargs

    def _get_or_create_query_parser(self, model: type[BaseModel]) -> Any:
        """Create a query parser for the model.

        Args:
            model: The model to create a parser for

        Returns:
            A RequestParser instance for the model

        """
        from flask_x_openapi_schema.x.flask_restful.utils import create_reqparse_from_pydantic

        return create_reqparse_from_pydantic(model=model, location="args")

    def process_additional_params(self, kwargs: dict[str, Any], param_names: list[str]) -> dict[str, Any]:
        """Process additional framework-specific parameters.

        Args:
            kwargs: The keyword arguments to update.
            param_names: List of parameter names that have been processed.

        Returns:
            Updated kwargs dictionary.

        """
        if self.parsed_args:
            for arg_name, arg_value in self.parsed_args.items():
                if arg_name not in kwargs and arg_name not in param_names:
                    kwargs[arg_name] = arg_value
        return kwargs


F = TypeVar("F", bound=Callable[..., Any])


def openapi_metadata(
    *,
    summary: str | I18nStr | None = None,
    description: str | I18nStr | None = None,
    tags: list[str] | None = None,
    operation_id: str | None = None,
    deprecated: bool = False,
    responses: OpenAPIMetaResponse | None = None,
    security: list[dict[str, list[str]]] | None = None,
    external_docs: dict[str, str] | None = None,
    language: str | None = None,
    prefix_config: ConventionalPrefixConfig | None = None,
) -> Callable[[F], F] | F:
    """Decorator to add OpenAPI metadata to a Flask-RESTful Resource endpoint.

    This decorator adds OpenAPI metadata to a Flask-RESTful Resource endpoint and handles
    parameter binding for request data. It automatically binds request body, query parameters,
    path parameters, and file uploads to function parameters based on their type annotations
    and parameter name prefixes.

    Args:
        summary: A short summary of what the operation does.
        description: A verbose explanation of the operation behavior.
        tags: A list of tags for API documentation control.
        operation_id: Unique string used to identify the operation.
        deprecated: Declares this operation to be deprecated.
        responses: The responses the API can return.
        security: A declaration of which security mechanisms can be used for this operation.
        external_docs: Additional external documentation.
        language: Language code to use for I18nString values (default: current language).
        prefix_config: Configuration object for parameter prefixes.

    Returns:
        The decorated function with OpenAPI metadata attached.

    Examples:
        >>> from flask_restful import Resource
        >>> from flask_x_openapi_schema.x.flask_restful import openapi_metadata
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
        >>> class ItemResource(Resource):
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
    return FlaskRestfulOpenAPIDecorator(
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
