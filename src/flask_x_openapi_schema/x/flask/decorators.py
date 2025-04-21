"""
Decorators for adding OpenAPI metadata to Flask MethodView endpoints.
"""

from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union

from flask import request
from pydantic import BaseModel

from ...core.config import ConventionalPrefixConfig
from ...i18n.i18n_string import I18nStr
from ...models.responses import OpenAPIMetaResponse


class FlaskOpenAPIDecorator:
    """OpenAPI metadata decorator for Flask MethodView."""

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
    ):
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

    def __call__(self, func):
        """Apply the decorator to the function."""
        # Initialize the base decorator if needed
        if self.base_decorator is None:
            # Import here to avoid circular imports
            from ...core.decorator_base import OpenAPIDecoratorBase

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
        self, query_model: Optional[Type[BaseModel]], path_params: Optional[List[str]]
    ) -> List[Dict[str, Any]]:
        """Extract OpenAPI parameters from models."""
        # Create parameters for OpenAPI schema
        parameters = []

        # Add path parameters
        if path_params:
            for param in path_params:
                parameters.append(
                    {
                        "name": param,
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                    }
                )

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

    def process_request_body(
        self, param_name: str, model: Type[BaseModel], kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process request body parameters for Flask.

        Args:
            param_name: The parameter name to bind the model instance to
            model: The Pydantic model class to use for validation
            kwargs: The keyword arguments to update

        Returns:
            Updated kwargs dictionary with the model instance
        """
        from ...core.decorator_base import preprocess_request_data
        from ...core.cache import MODEL_CACHE
        import logging

        logger = logging.getLogger(__name__)
        logger.debug(
            f"Processing request body for {param_name} with model {model.__name__}"
        )
        logger.debug(f"Request content type: {request.content_type}")
        logger.debug(f"Request is_json: {request.is_json}")

        # Skip processing if request is not JSON and not a form
        if not request.is_json and not request.form and not request.files:
            logger.warning(
                f"Request is not JSON or form, skipping request body processing for {param_name}"
            )
            return kwargs

        # Get data from request (JSON or form)
        body_data = {}
        if request.is_json:
            body_data = request.get_json(silent=True) or {}
        elif request.form:
            # Convert form data to dict
            body_data = {key: value for key, value in request.form.items()}
            # Add files if present
            if request.files:
                for key, file in request.files.items():
                    body_data[key] = file
        logger.debug(f"Request body data: {body_data}")

        # Create cache key for this request
        from ...core.cache import make_cache_key

        cache_key = make_cache_key(id(model), body_data)

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
            logger.debug(
                f"Attempting to validate model {model.__name__} with processed data"
            )
            model_instance = model.model_validate(processed_body_data)
            logger.debug(f"Model validation successful for {param_name}")
        except Exception as e:
            # Log the validation error and try fallback approach
            logger.warning(
                f"Validation error: {e}. Falling back to manual construction."
            )

            # Filter data to only include fields in the model
            model_fields = model.model_fields
            filtered_body_data = {
                k: v for k, v in processed_body_data.items() if k in model_fields
            }
            logger.debug(f"Filtered body data: {filtered_body_data}")

            # Create instance using constructor
            try:
                model_instance = model(**filtered_body_data)
                logger.debug(
                    f"Created model instance using constructor for {param_name}"
                )
            except Exception as e2:
                logger.error(f"Failed to create model instance: {e2}")
                # Return empty model instance as fallback
                try:
                    # Try to create an empty instance with default values
                    model_instance = model()
                    logger.warning(
                        f"Created empty model instance for {param_name} as fallback"
                    )
                except Exception as e3:
                    logger.error(f"Failed to create empty model instance: {e3}")
                    # Return kwargs unchanged if all attempts fail
                    return kwargs

        # Store in kwargs and cache
        kwargs[param_name] = model_instance
        MODEL_CACHE.set(cache_key, model_instance)
        logger.debug(f"Stored model instance for {param_name} in kwargs and cache")

        return kwargs

    def process_query_params(
        self, param_name: str, model: Type[BaseModel], kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process query parameters for Flask.

        Args:
            param_name: The parameter name to bind the model instance to
            model: The Pydantic model class to use for validation
            kwargs: The keyword arguments to update

        Returns:
            Updated kwargs dictionary with the model instance
        """
        from ...core.cache import MODEL_CACHE

        # Extract query parameters from request
        query_data = {}
        model_fields = model.model_fields

        # Only extract fields that exist in the model
        for field_name in model_fields:
            if field_name in request.args:
                query_data[field_name] = request.args.get(field_name)

        # Create cache key for this request
        from ...core.cache import make_cache_key

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

    def process_additional_params(
        self, kwargs: Dict[str, Any], param_names: List[str]
    ) -> Dict[str, Any]:
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
        logger.debug(
            f"Processing additional parameters with kwargs keys: {list(kwargs.keys())}"
        )
        logger.debug(f"Processed parameter names: {param_names}")
        return kwargs


# Define a type variable for the function
F = TypeVar("F", bound=Callable[..., Any])


def openapi_metadata(
    *,
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
) -> Callable[[F], F]:
    """
    Decorator to add OpenAPI metadata to a Flask MethodView endpoint.

    Args:
        summary: A short summary of what the operation does
        description: A verbose explanation of the operation behavior
        tags: A list of tags for API documentation control
        operation_id: Unique string used to identify the operation
        responses: The responses the API can return (**Optional**, auto detect by user response if pydanitc model input)
        deprecated: Declares this operation to be deprecated
        security: A declaration of which security mechanisms can be used for this operation
        external_docs: Additional external documentation
        language: Language code to use for I18nString values (default: current language)
        prefix_config: Configuration object for parameter prefixes

    Returns:
        The decorated function with OpenAPI metadata attached
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
