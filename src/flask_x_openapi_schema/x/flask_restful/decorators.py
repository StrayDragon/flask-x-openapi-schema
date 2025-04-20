"""
Decorators for adding OpenAPI metadata to Flask-RESTful Resource endpoints.
"""

from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union

from pydantic import BaseModel

from ...core.config import ConventionalPrefixConfig
from ...i18n.i18n_string import I18nStr

# Cache for reqparse objects
_REQPARSE_CACHE = {}

# Cache for model instances
_MODEL_INSTANCE_CACHE = {}


class FlaskRestfulOpenAPIDecorator:
    """OpenAPI metadata decorator for Flask-RESTful Resource."""

    def __init__(
        self,
        summary: Optional[Union[str, I18nStr]] = None,
        description: Optional[Union[str, I18nStr]] = None,
        tags: Optional[List[str]] = None,
        operation_id: Optional[str] = None,
        responses: Optional[Dict[str, Any]] = None,
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
        """Process request body parameters for Flask-RESTful."""
        from ..flask_restful.utils import create_reqparse_from_pydantic

        # Check if we've already created a reqparse for this model
        if id(model) in _REQPARSE_CACHE:
            parser = _REQPARSE_CACHE[model]
        else:
            # Flask-RESTful approach using reqparse
            parser = create_reqparse_from_pydantic(body_model=model, query_model=None)
            # Cache the parser for future use (limit cache size to prevent memory issues)
            if len(_REQPARSE_CACHE) > 100:
                _REQPARSE_CACHE.clear()
            _REQPARSE_CACHE[id(model)] = parser

        self.parsed_args = parser.parse_args()

        # Create a cache key based on the parsed arguments
        cache_key = (id(model), str(frozenset(self.parsed_args.items())))

        # Check if we've already created a model instance for these arguments
        if cache_key in _MODEL_INSTANCE_CACHE:
            model_instance = _MODEL_INSTANCE_CACHE[cache_key]
            kwargs[param_name] = model_instance
            return kwargs

        # Create from parsed arguments
        body_data = {}
        model_fields = model.model_fields
        for field_name in model_fields:
            if field_name in self.parsed_args:
                body_data[field_name] = self.parsed_args[field_name]

        model_instance = model(**body_data)
        kwargs[param_name] = model_instance

        # Cache the model instance for future use (limit cache size to prevent memory issues)
        if len(_MODEL_INSTANCE_CACHE) > 1000:
            _MODEL_INSTANCE_CACHE.clear()
        _MODEL_INSTANCE_CACHE[cache_key] = model_instance

        return kwargs

    def process_query_params(
        self, param_name: str, model: Type[BaseModel], kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process query parameters for Flask-RESTful."""
        from ..flask_restful.utils import create_reqparse_from_pydantic

        if not self.parsed_args:
            # Check if we've already created a reqparse for this model
            if id(model) in _REQPARSE_CACHE:
                parser = _REQPARSE_CACHE[model]
            else:
                # Flask-RESTful approach using reqparse
                parser = create_reqparse_from_pydantic(
                    query_model=model, body_model=None
                )
                # Cache the parser for future use (limit cache size to prevent memory issues)
                if len(_REQPARSE_CACHE) > 100:
                    _REQPARSE_CACHE.clear()
                _REQPARSE_CACHE[id(model)] = parser

            self.parsed_args = parser.parse_args()

            # Create a cache key based on the parsed arguments
            cache_key = (id(model), str(frozenset(self.parsed_args.items())))

            # Check if we've already created a model instance for these arguments
            if cache_key in _MODEL_INSTANCE_CACHE:
                model_instance = _MODEL_INSTANCE_CACHE[cache_key]
                kwargs[param_name] = model_instance
                return kwargs

            # Create from parsed arguments
            query_data = {}
            model_fields = model.model_fields
            for field_name in model_fields:
                if field_name in self.parsed_args:
                    query_data[field_name] = self.parsed_args[field_name]

            model_instance = model(**query_data)
            kwargs[param_name] = model_instance

            # Cache the model instance for future use (limit cache size to prevent memory issues)
            if len(_MODEL_INSTANCE_CACHE) > 1000:
                _MODEL_INSTANCE_CACHE.clear()
            _MODEL_INSTANCE_CACHE[cache_key] = model_instance

        return kwargs

    def process_additional_params(
        self, kwargs: Dict[str, Any], param_names: List[str]
    ) -> Dict[str, Any]:
        """Process additional framework-specific parameters."""
        # Add all parsed arguments to kwargs for regular parameters
        if self.parsed_args:
            for arg_name, arg_value in self.parsed_args.items():
                if arg_name not in kwargs:
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
    responses: Optional[Dict[str, Any]] = None,
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
