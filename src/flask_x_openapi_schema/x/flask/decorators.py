"""Decorators for adding OpenAPI metadata to Flask MethodView endpoints."""

from collections.abc import Callable
from typing import Any, TypeVar

from flask import request
from pydantic import BaseModel

from flask_x_openapi_schema.core.cache import make_cache_key
from flask_x_openapi_schema.core.config import ConventionalPrefixConfig
from flask_x_openapi_schema.i18n.i18n_string import I18nStr
from flask_x_openapi_schema.models.responses import OpenAPIMetaResponse


class FlaskOpenAPIDecorator:
    """OpenAPI metadata decorator for Flask MethodView."""

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
        """Initialize the decorator with OpenAPI metadata parameters."""
        # Store parameters for later use
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
        self.framework = "flask"

        # We'll initialize the base decorator when needed
        self.base_decorator = None

    def __call__(self, func):  # noqa: ANN001, ANN204
        """Apply the decorator to the function."""
        # Initialize the base decorator if needed
        if self.base_decorator is None:
            # Import here to avoid circular imports
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
        """Extract OpenAPI parameters from models."""
        # Create parameters for OpenAPI schema
        parameters = [
            {
                "name": param,
                "in": "path",
                "required": True,
                "schema": {"type": "string"},
            }
            for param in path_params
        ]

        # Add query parameters
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

                # Add description if available
                if "description" in field_schema:
                    param["description"] = field_schema["description"]

                parameters.append(param)

        return parameters

    def process_request_body(self, param_name: str, model: type[BaseModel], kwargs: dict[str, Any]) -> dict[str, Any]:  # noqa: PLR0915
        """Process request body parameters for Flask.

        Args:
            param_name: The parameter name to bind the model instance to
            model: The Pydantic model class to use for validation
            kwargs: The keyword arguments to update

        Returns:
            Updated kwargs dictionary with the model instance

        """
        import logging

        from flask_x_openapi_schema.core.cache import MODEL_CACHE
        from flask_x_openapi_schema.core.decorator_base import preprocess_request_data

        logger = logging.getLogger(__name__)
        logger.debug(f"Processing request body for {param_name} with model {model.__name__}")
        logger.debug(f"Request content type: {request.content_type}")
        logger.debug(f"Request is_json: {request.is_json}")

        # Skip processing if request is not JSON and not a form
        if not request.is_json and not request.form and not request.files:
            logger.warning(f"Request is not JSON or form, skipping request body processing for {param_name}")
            return kwargs

        # Get data from request (JSON or form)
        body_data = {}

        # Create cache key for this request

        if request.is_json:
            body_data = request.get_json(silent=True) or {}
            logger.debug(f"Request body data (JSON): {body_data}")

            # Create cache key based on model and body data
            cache_key = make_cache_key(id(model), body_data)

            # Try to create model instance directly from raw JSON
            if body_data:
                try:
                    model_instance = model.model_validate(body_data)
                    logger.debug(f"Created model instance directly from JSON for {param_name}")
                    kwargs[param_name] = model_instance
                    MODEL_CACHE.set(cache_key, model_instance)
                except Exception as e:
                    logger.warning(f"Failed to validate model from raw JSON: {e}")
                else:
                    return kwargs
        elif request.form:
            # Convert form data to dict
            body_data = dict(request.form.items())
            # Add files if present
            if request.files:
                for key, file in request.files.items():
                    body_data[key] = file
            logger.debug(f"Request body data (form): {body_data}")

            # Create cache key based on model and body data
            cache_key = make_cache_key(id(model), body_data)
        else:
            logger.debug("No JSON or form data found in request")
            cache_key = make_cache_key(id(model), {})

        # Check if we have a cached model instance
        cached_instance = MODEL_CACHE.get(cache_key)
        if cached_instance is not None:
            logger.debug(f"Using cached model instance for {param_name}")
            kwargs[param_name] = cached_instance
            return kwargs

        # Pre-process the body data to handle list fields correctly
        processed_body_data = preprocess_request_data(body_data, model)
        logger.debug(f"Processed body data: {processed_body_data}")

        # Try to create model instance
        try:
            # Try model_validate first (better handling of complex types)
            logger.debug(f"Attempting to validate model {model.__name__} with processed data")
            model_instance = model.model_validate(processed_body_data)
            logger.debug(f"Model validation successful for {param_name}")
        except Exception as e:
            # Log the validation error and try fallback approach
            logger.warning(f"Validation error: {e}. Falling back to manual construction.")

            # Filter data to only include fields in the model
            model_fields = model.model_fields
            filtered_body_data = {k: v for k, v in processed_body_data.items() if k in model_fields}
            logger.debug(f"Filtered body data: {filtered_body_data}")

            # Create instance using constructor
            try:
                model_instance = model(**filtered_body_data)
                logger.debug(f"Created model instance using constructor for {param_name}")
            except Exception as e2:
                logger.exception("Failed to create model instance e2", extra={"error": e2})
                # Return empty model instance as fallback
                try:
                    # Try to create an empty instance with default values
                    model_instance = model()
                    logger.warning(f"Created empty model instance for {param_name} as fallback")
                except Exception as e3:
                    logger.exception("Failed to create empty model instance e3", extra={"error": e3})
                    # Return kwargs unchanged if all attempts fail
                    return kwargs

        # Store in kwargs and cache
        kwargs[param_name] = model_instance
        MODEL_CACHE.set(cache_key, model_instance)
        logger.debug(f"Stored model instance for {param_name} in kwargs and cache")

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
        from flask_x_openapi_schema.core.cache import MODEL_CACHE

        # Extract query parameters from request
        query_data = {}
        model_fields = model.model_fields

        # Only extract fields that exist in the model
        for field_name in model_fields:
            if field_name in request.args:
                query_data[field_name] = request.args.get(field_name)

        # Create cache key for this request
        from flask_x_openapi_schema.core.cache import make_cache_key

        cache_key = make_cache_key(id(model), query_data)

        # Check if we have a cached model instance
        cached_instance = MODEL_CACHE.get(cache_key)
        if cached_instance is not None:
            kwargs[param_name] = cached_instance
            return kwargs

        # Create model instance
        model_instance = model(**query_data)

        # Store in kwargs and cache
        kwargs[param_name] = model_instance
        MODEL_CACHE.set(cache_key, model_instance)

        return kwargs

    def process_additional_params(self, kwargs: dict[str, Any], param_names: list[str]) -> dict[str, Any]:
        """Process additional framework-specific parameters.

        Args:
            kwargs: The keyword arguments to update
            param_names: List of parameter names that have been processed

        Returns:
            Updated kwargs dictionary

        """
        # No additional processing needed for Flask
        # Just log the parameters for debugging
        import logging

        logger = logging.getLogger(__name__)
        logger.debug(f"Processing additional parameters with kwargs keys: {list(kwargs.keys())}")
        logger.debug(f"Processed parameter names: {param_names}")
        return kwargs


# Define a type variable for the function
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
) -> Callable[[F], F]:
    """Decorator to add OpenAPI metadata to a Flask MethodView endpoint.

    This decorator adds OpenAPI metadata to a Flask MethodView endpoint and handles
    parameter binding for request data. It automatically binds request body, query parameters,
    path parameters, and file uploads to function parameters based on their type annotations
    and parameter name prefixes.

    :param summary: A short summary of what the operation does
    :type summary: Optional[Union[str, I18nStr]]
    :param description: A verbose explanation of the operation behavior
    :type description: Optional[Union[str, I18nStr]]
    :param tags: A list of tags for API documentation control
    :type tags: Optional[List[str]]
    :param operation_id: Unique string used to identify the operation
    :type operation_id: Optional[str]
    :param responses: The responses the API can return
    :type responses: Optional[OpenAPIMetaResponse]
    :param deprecated: Declares this operation to be deprecated
    :type deprecated: bool
    :param security: A declaration of which security mechanisms can be used for this operation
    :type security: Optional[List[Dict[str, List[str]]]]
    :param external_docs: Additional external documentation
    :type external_docs: Optional[Dict[str, str]]
    :param language: Language code to use for I18nString values (default: current language)
    :type language: Optional[str]
    :param prefix_config: Configuration object for parameter prefixes
    :type prefix_config: Optional[ConventionalPrefixConfig]
    :return: The decorated function with OpenAPI metadata attached
    :rtype: Callable[[F], F]

    Example:
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
        ...         # _x_body is automatically populated from the request JSON
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
    )
