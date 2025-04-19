"""
Decorators for adding OpenAPI metadata to Flask-RESTful Resource endpoints.
"""

from typing import Any, Dict, List, Optional, Type, Union

from pydantic import BaseModel

from .base import OpenAPIDecoratorBase
from ..i18n.i18n_string import I18nStr

# Check if Flask-RESTful is available
try:
    from ..restful_utils import (
        create_reqparse_from_pydantic,
        extract_openapi_parameters_from_pydantic,
    )
    HAS_FLASK_RESTFUL = True
except ImportError:
    # Define placeholder functions for when Flask-RESTful is not available
    def create_reqparse_from_pydantic(*_args, **_kwargs):
        raise ImportError(
            "Flask-RESTful is not installed. Install with 'pip install flask-x-openapi-schema[restful]'"
        )

    def extract_openapi_parameters_from_pydantic(*_args, **_kwargs):
        raise ImportError(
            "Flask-RESTful is not installed. Install with 'pip install flask-x-openapi-schema[restful]'"
        )

    HAS_FLASK_RESTFUL = False


class FlaskRestfulOpenAPIDecorator(OpenAPIDecoratorBase):
    """OpenAPI metadata decorator for Flask-RESTful Resource."""

    def __init__(self, *args, **kwargs):
        """Initialize the decorator and check if Flask-RESTful is available."""
        super().__init__(*args, **kwargs)
        if not HAS_FLASK_RESTFUL:
            raise ImportError(
                "Flask-RESTful is not installed. Install with 'pip install flask-x-openapi-schema[restful]'"
            )
        self.parsed_args = None

    def extract_parameters_from_models(
        self, query_model: Optional[Type[BaseModel]], path_params: Optional[List[str]]
    ) -> List[Dict[str, Any]]:
        """Extract OpenAPI parameters from models."""
        return extract_openapi_parameters_from_pydantic(
            query_model=query_model, path_params=path_params
        )

    def process_request_body(
        self, param_name: str, model: Type[BaseModel], kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process request body parameters for Flask-RESTful."""
        # Flask-RESTful approach using reqparse
        parser = create_reqparse_from_pydantic(
            body_model=model, query_model=None
        )
        self.parsed_args = parser.parse_args()

        # Create from parsed arguments
        body_data = {}
        model_fields = model.model_fields
        for field_name in model_fields:
            if field_name in self.parsed_args:
                body_data[field_name] = self.parsed_args[field_name]

        model_instance = model(**body_data)
        kwargs[param_name] = model_instance
        return kwargs

    def process_query_params(
        self, param_name: str, model: Type[BaseModel], kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process query parameters for Flask-RESTful."""
        if not self.parsed_args:
            # Flask-RESTful approach using reqparse
            parser = create_reqparse_from_pydantic(
                query_model=model, body_model=None
            )
            self.parsed_args = parser.parse_args()

            # Create from parsed arguments
            query_data = {}
            model_fields = model.model_fields
            for field_name in model_fields:
                if field_name in self.parsed_args:
                    query_data[field_name] = self.parsed_args[field_name]

            model_instance = model(**query_data)
            kwargs[param_name] = model_instance
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


def openapi_metadata(*args, **kwargs):
    """
    Decorator to add OpenAPI metadata to a Flask-RESTful Resource endpoint.

    This decorator does the following:
    1. Adds OpenAPI metadata to the function for documentation generation
    2. Automatically detects and binds request parameters to function parameters with special prefixes
    3. Preserves type annotations from Pydantic models for better IDE support
    4. Automatically converts BaseRespModel responses to Flask-RESTful compatible responses

    Special parameter prefixes (automatically detected if auto_detect_params=True):
    - x_request_body: Binds the entire request body object (auto-detected from type annotation)
    - x_request_query: Binds the entire query parameters object (auto-detected from type annotation)
    - x_request_path_<param_name>: Binds a path parameter (auto-detected from parameter name)
    - x_request_file: Binds a file object (auto-detected from parameter name)

    Args:
        summary: A short summary of what the operation does
        description: A verbose explanation of the operation behavior
        tags: A list of tags for API documentation control
        operation_id: Unique string used to identify the operation
        request_body: The request body schema (Pydantic model or dict)
        responses: The responses the API can return
        parameters: Parameters that are sent with the request
        deprecated: Declares this operation to be deprecated
        security: A declaration of which security mechanisms can be used for this operation
        external_docs: Additional external documentation
        query_model: Pydantic model for query parameters (optional if auto-detected)
        path_params: List of path parameter names (optional if auto-detected)
        auto_detect_params: Whether to automatically detect parameters from function signature
        language: Language code to use for I18nString values (default: current language)
        prefix_config: Configuration object for parameter prefixes

    Returns:
        The decorated function with OpenAPI metadata attached and type annotations preserved
    """
    # Handle both @openapi_metadata and @openapi_metadata() usage
    if len(args) == 1 and callable(args[0]) and not kwargs:
        # Called as @openapi_metadata without arguments
        return FlaskRestfulOpenAPIDecorator()(args[0])
    else:
        # Called as @openapi_metadata(...) with arguments
        return FlaskRestfulOpenAPIDecorator(**kwargs)