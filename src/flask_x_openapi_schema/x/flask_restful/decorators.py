"""
Decorators for adding OpenAPI metadata to Flask-RESTful Resource endpoints.
"""

from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union
from flask import request

from pydantic import BaseModel

from ...core.config import ConventionalPrefixConfig
from ...i18n.i18n_string import I18nStr
from ...models.responses import OpenAPIMetaResponse
from ...core.decorator_base import preprocess_request_data
import logging

# These caches have been moved to core.cache module
# and are now using ThreadSafeCache implementation


class FlaskRestfulOpenAPIDecorator:
    """OpenAPI metadata decorator for Flask-RESTful Resource."""

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
        self.framework = "flask_restful"

        # We'll initialize the base decorator when needed
        self.base_decorator = None
        self.parsed_args = None

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
        """Process request body parameters for Flask-RESTful.

        Args:
            param_name: The parameter name to bind the model instance to
            model: The Pydantic model class to use for validation
            kwargs: The keyword arguments to update

        Returns:
            Updated kwargs dictionary with the model instance
        """
        from flask import request
        from ...core.cache import MODEL_CACHE, make_cache_key

        # Check if this is a file upload model
        has_file_fields = self._check_for_file_fields(model)

        # Handle file upload models
        if has_file_fields and request.files:
            model_instance = self._process_file_upload_model(model)
            kwargs[param_name] = model_instance
            return kwargs

        # Standard handling for non-file models
        # Get or create reqparse parser
        parser = self._get_or_create_parser(model)

        # Parse arguments
        self.parsed_args = parser.parse_args()

        # Create cache key based on model and parsed arguments
        cache_key = make_cache_key(id(model), self.parsed_args)

        # Check for cached model instance
        cached_instance = MODEL_CACHE.get(cache_key)
        if cached_instance is not None:
            kwargs[param_name] = cached_instance
            return kwargs

        # Create model instance from parsed arguments
        model_instance = self._create_model_from_args(model, self.parsed_args)
        kwargs[param_name] = model_instance

        # Cache the model instance
        MODEL_CACHE.set(cache_key, model_instance)

        return kwargs

    def _check_for_file_fields(self, model: Type[BaseModel]) -> bool:
        """Check if a model contains file upload fields.

        Args:
            model: The model to check

        Returns:
            True if the model has file fields, False otherwise
        """
        import inspect
        from ...models.file_models import FileField

        if not hasattr(model, "model_fields"):
            return False

        for _, field_info in model.model_fields.items():
            field_type = field_info.annotation
            if inspect.isclass(field_type) and issubclass(field_type, FileField):
                return True

        return False

    def _process_file_upload_model(self, model: Type[BaseModel]) -> BaseModel:
        """Process a file upload model with form data and files.

        Args:
            model: The model class to instantiate

        Returns:
            An instance of the model with file data
        """
        from flask import request
        import inspect
        from ...models.file_models import FileField

        # Create model data from form and files
        model_data = {}

        # Add form data
        for field_name, field_value in request.form.items():
            model_data[field_name] = field_value

        # Add file data
        for field_name, field_info in model.model_fields.items():
            field_type = field_info.annotation
            if inspect.isclass(field_type) and issubclass(field_type, FileField):
                # Check if file exists in request
                if field_name in request.files:
                    model_data[field_name] = request.files[field_name]
                elif "file" in request.files and field_name == "file":
                    model_data[field_name] = request.files["file"]

        # Create and return model instance
        return model(**model_data)

    def _get_or_create_parser(self, model: Type[BaseModel]):
        """Get an existing parser or create a new one for the model.

        Args:
            model: The model to create a parser for

        Returns:
            A RequestParser instance for the model
        """
        from ..flask_restful.utils import create_reqparse_from_pydantic
        from ...core.cache import REQPARSE_CACHE

        # Use model's id as cache key
        model_id = id(model)

        # Check if we've already created a reqparse for this model
        if model_id in REQPARSE_CACHE:
            return REQPARSE_CACHE.get(model_id)

        # Create new parser
        parser = create_reqparse_from_pydantic(body_model=model, query_model=None)

        # Cache the parser
        REQPARSE_CACHE[model_id] = parser
        return parser

    def _create_model_from_args(self, model: Type[BaseModel], args: dict) -> BaseModel:
        """Create a model instance from parsed arguments.

        Args:
            model: The model class to instantiate
            args: The parsed arguments

        Returns:
            An instance of the model
        """

        logger = logging.getLogger(__name__)

        # First, try to use the raw JSON data if available
        if request.is_json:
            try:
                raw_json = request.get_json(silent=True)
                if raw_json and isinstance(raw_json, dict):
                    logger.debug("Using raw JSON data from request")

                    # Try to create model instance directly from raw JSON
                    try:
                        return model.model_validate(raw_json)
                    except Exception as e:
                        logger.warning(f"Failed to validate model from raw JSON: {e}")

                        # If validation fails, try to create using constructor
                        try:
                            # Only use fields that exist in the model
                            model_fields = model.model_fields
                            filtered_json = {
                                k: v for k, v in raw_json.items() if k in model_fields
                            }
                            return model(**filtered_json)
                        except Exception as e2:
                            logger.warning(
                                f"Failed to create model from raw JSON: {e2}"
                            )
                            # Continue with normal processing if this fails
            except Exception as e:
                logger.warning(f"Error accessing raw JSON data: {e}")

        # Process arguments using the core preprocess_request_data function
        # This ensures consistent handling across Flask and Flask-RESTful
        processed_data = preprocess_request_data(args, model)

        # Try to create model instance using model_validate first (better handling of complex types)
        try:
            logger.debug(
                f"Attempting to validate model {model.__name__} with processed data"
            )
            model_instance = model.model_validate(processed_data)
            logger.debug("Model validation successful")
            return model_instance
        except Exception as e:
            logger.warning(
                f"Validation error: {e}. Falling back to manual construction."
            )

            # Filter data to only include fields in the model
            try:
                model_fields = model.model_fields
                filtered_data = {
                    k: v for k, v in processed_data.items() if k in model_fields
                }
                logger.debug(f"Filtered data: {filtered_data}")

                # Create instance using constructor
                model_instance = model(**filtered_data)
                logger.debug("Created model instance using constructor")
                return model_instance
            except Exception as e2:
                logger.error(f"Failed to create model instance: {e2}")
                logger.error(f"Processed data: {processed_data}")

                # Try to create an empty instance with default values as last resort
                try:
                    model_instance = model()
                    logger.warning("Created empty model instance as fallback")
                    return model_instance
                except Exception as e3:
                    logger.error(f"Failed to create empty model instance: {e3}")
                    raise e2  # Raise the original error

    def process_query_params(
        self, param_name: str, model: Type[BaseModel], kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process query parameters for Flask-RESTful.

        Args:
            param_name: The parameter name to bind the model instance to
            model: The Pydantic model class to use for validation
            kwargs: The keyword arguments to update

        Returns:
            Updated kwargs dictionary with the model instance
        """
        from ...core.cache import MODEL_CACHE, make_cache_key

        # Skip if we already have parsed arguments
        if self.parsed_args:
            return kwargs

        # Get or create reqparse parser for query parameters
        parser = self._get_or_create_query_parser(model)

        # Parse arguments
        self.parsed_args = parser.parse_args()

        # Create cache key based on model and parsed arguments
        cache_key = make_cache_key(id(model), self.parsed_args)

        # Check for cached model instance
        cached_instance = MODEL_CACHE.get(cache_key)
        if cached_instance is not None:
            kwargs[param_name] = cached_instance
            return kwargs

        # Create model instance from parsed arguments
        model_instance = self._create_model_from_args(model, self.parsed_args)
        kwargs[param_name] = model_instance

        # Cache the model instance
        MODEL_CACHE.set(cache_key, model_instance)

        return kwargs

    def _get_or_create_query_parser(self, model: Type[BaseModel]):
        """Get an existing query parser or create a new one for the model.

        Args:
            model: The model to create a parser for

        Returns:
            A RequestParser instance for the model
        """
        from ..flask_restful.utils import create_reqparse_from_pydantic
        from ...core.cache import REQPARSE_CACHE

        # Create a unique key for query parsers
        model_id = (id(model), "query")

        # Check if we've already created a reqparse for this model
        if model_id in REQPARSE_CACHE:
            return REQPARSE_CACHE.get(model_id)

        # Create new parser
        parser = create_reqparse_from_pydantic(query_model=model, body_model=None)

        # Cache the parser
        REQPARSE_CACHE[model_id] = parser
        return parser

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
        # Add all parsed arguments to kwargs for regular parameters
        # This allows Flask-RESTful to access parameters directly without
        # requiring the use of the model instance
        if self.parsed_args:
            # Only add arguments that haven't been processed yet
            for arg_name, arg_value in self.parsed_args.items():
                if arg_name not in kwargs and arg_name not in param_names:
                    kwargs[arg_name] = arg_value
        return kwargs


# Define a type variable for the function
F = TypeVar("F", bound=Callable[..., Any])


def openapi_metadata(
    *,
    summary: Optional[Union[str, I18nStr]] = None,
    description: Optional[Union[str, I18nStr]] = None,
    tags: Optional[List[str]] = None,
    operation_id: Optional[str] = None,
    deprecated: bool = False,
    responses: Optional[OpenAPIMetaResponse] = None,
    security: Optional[List[Dict[str, List[str]]]] = None,
    external_docs: Optional[Dict[str, str]] = None,
    language: Optional[str] = None,
    prefix_config: Optional[ConventionalPrefixConfig] = None,
) -> Union[Callable[[F], F], F]:
    """
    Decorator to add OpenAPI metadata to a Flask-RESTful Resource endpoint.

    Args:
        summary: A short summary of what the operation does
        description: A verbose explanation of the operation behavior
        tags: A list of tags for API documentation control
        operation_id: Unique string used to identify the operation
        responses: The responses the API can return (**Optional**, auto detect by user response if pydanitc model input)
        security: A declaration of which security mechanisms can be used for this operation
        deprecated: Declares this operation to be deprecated
        external_docs: Additional external documentation
        language: Language code to use for I18nString values (default: current language)
        prefix_config: Configuration object for parameter prefixes

    Returns:
        The decorated function with OpenAPI metadata attached
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
