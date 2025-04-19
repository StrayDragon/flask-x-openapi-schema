"""
Decorators for adding OpenAPI metadata to Flask MethodView endpoints.
"""

from typing import Any, Dict, List, Optional, Type, Union

from flask import request
from pydantic import BaseModel

from ...core.config import ConventionalPrefixConfig
from ...i18n.i18n_string import I18nStr


class FlaskOpenAPIDecorator:
    """OpenAPI metadata decorator for Flask MethodView."""

    def __init__(
        self,
        summary: Optional[Union[str, I18nStr]] = None,
        description: Optional[Union[str, I18nStr]] = None,
        tags: Optional[List[str]] = None,
        operation_id: Optional[str] = None,
        request_body: Optional[Union[Type[BaseModel], Dict[str, Any]]] = None,
        responses: Optional[Dict[str, Any]] = None,
        parameters: Optional[List[Dict[str, Any]]] = None,
        deprecated: bool = False,
        security: Optional[List[Dict[str, List[str]]]] = None,
        external_docs: Optional[Dict[str, str]] = None,
        query_model: Optional[Type[BaseModel]] = None,
        path_params: Optional[List[str]] = None,
        auto_detect_params: bool = True,
        language: Optional[str] = None,
        prefix_config: Optional[ConventionalPrefixConfig] = None,
    ):
        """Initialize the decorator with OpenAPI metadata parameters."""
        # Store parameters for later use
        self.summary = summary
        self.description = description
        self.tags = tags
        self.operation_id = operation_id
        self.request_body = request_body
        self.responses = responses
        self.parameters = parameters
        self.deprecated = deprecated
        self.security = security
        self.external_docs = external_docs
        self.query_model = query_model
        self.path_params = path_params
        self.auto_detect_params = auto_detect_params
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
                request_body=self.request_body,
                responses=self.responses,
                parameters=self.parameters,
                deprecated=self.deprecated,
                security=self.security,
                external_docs=self.external_docs,
                query_model=self.query_model,
                path_params=self.path_params,
                auto_detect_params=self.auto_detect_params,
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
        """Process request body parameters for Flask."""
        from ...core.decorator_base import preprocess_request_data

        if request.is_json:
            # Direct Flask approach
            body_data = request.get_json(silent=True) or {}

            # Pre-process the body data to handle list fields correctly
            processed_body_data = preprocess_request_data(body_data, model)

            # Try to use model_validate first (better handling of complex types)
            try:
                model_instance = model.model_validate(processed_body_data)
                kwargs[param_name] = model_instance
            except Exception as e:
                # Log the validation error for debugging
                import logging

                logging.getLogger(__name__).debug(
                    f"Validation error: {e}. Falling back to manual construction."
                )

                # Fallback to the old approach if model_validate fails
                # Filter body data to only include fields in the model
                model_fields = model.model_fields
                filtered_body_data = {
                    k: v for k, v in processed_body_data.items() if k in model_fields
                }
                model_instance = model(**filtered_body_data)
                kwargs[param_name] = model_instance

        return kwargs

    def process_query_params(
        self, param_name: str, model: Type[BaseModel], kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process query parameters for Flask."""
        # Direct Flask approach
        query_data = {}
        model_fields = model.model_fields
        for field_name in model_fields:
            if field_name in request.args:
                query_data[field_name] = request.args.get(field_name)

        model_instance = model(**query_data)
        kwargs[param_name] = model_instance
        return kwargs

    def process_additional_params(
        self, kwargs: Dict[str, Any], param_names: List[str]
    ) -> Dict[str, Any]:
        """Process additional framework-specific parameters."""
        # No additional processing needed for Flask
        return kwargs


def openapi_metadata(
    *,
    summary: Optional[Union[str, I18nStr]] = None,
    description: Optional[Union[str, I18nStr]] = None,
    tags: Optional[List[str]] = None,
    operation_id: Optional[str] = None,
    request_body: Optional[Union[Type[BaseModel], Dict[str, Any]]] = None,
    responses: Optional[Dict[str, Any]] = None,
    parameters: Optional[List[Dict[str, Any]]] = None,
    deprecated: bool = False,
    security: Optional[List[Dict[str, List[str]]]] = None,
    external_docs: Optional[Dict[str, str]] = None,
    query_model: Optional[Type[BaseModel]] = None,
    path_params: Optional[List[str]] = None,
    # The following parameters are optional and can be automatically detected from the function signature
    auto_detect_params: bool = True,
    language: Optional[str] = None,
    prefix_config: Optional[ConventionalPrefixConfig] = None,
):
    """
    Decorator to add OpenAPI metadata to a Flask MethodView endpoint.

    This decorator does the following:
    1. Adds OpenAPI metadata to the function for documentation generation
    2. Automatically detects and binds request parameters to function parameters with special prefixes
    3. Preserves type annotations from Pydantic models for better IDE support
    4. Automatically converts BaseRespModel responses to Flask compatible responses

    Special parameter prefixes (automatically detected if auto_detect_params=True):
    - x_request_body: Binds the entire request body object (auto-detected from type annotation)
    - x_request_query: Binds the entire query parameters object (auto-detected from type annotation)
    - x_request_path_<param_name>: Binds a path parameter (auto-detected from parameter name)
    - x_request_file: Binds a file object (auto-detected from parameter name)

    These prefixes can be configured using configure_prefixes() function or the prefix_config parameter.

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
    decorator = FlaskOpenAPIDecorator(
        summary=summary,
        description=description,
        tags=tags,
        operation_id=operation_id,
        request_body=request_body,
        responses=responses,
        parameters=parameters,
        deprecated=deprecated,
        security=security,
        external_docs=external_docs,
        query_model=query_model,
        path_params=path_params,
        auto_detect_params=auto_detect_params,
        language=language,
        prefix_config=prefix_config,
    )
    return decorator