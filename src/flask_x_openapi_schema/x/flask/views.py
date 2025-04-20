"""
Utilities for integrating Pydantic models with Flask.MethodView.
"""

from typing import Any, Dict, List, Type, get_type_hints

from flask import request
from flask.views import MethodView
from pydantic import BaseModel

from ...core.schema_generator import OpenAPISchemaGenerator


class OpenAPIMethodViewMixin:
    """
    A mixin class for Flask.MethodView to collect OpenAPI metadata.
    """

    @classmethod
    def register_to_blueprint(cls, blueprint, url, endpoint=None, **kwargs):
        """
        Register the MethodView to a blueprint and collect OpenAPI metadata.

        Args:
            blueprint: The Flask blueprint to register to
            url: The URL rule to register
            endpoint: The endpoint name (defaults to the class name)
            **kwargs: Additional arguments to pass to add_url_rule
        """
        view_func = cls.as_view(endpoint or cls.__name__.lower())
        blueprint.add_url_rule(url, view_func=view_func, **kwargs)

        # Store the URL and class for OpenAPI schema generation
        if not hasattr(blueprint, "_methodview_openapi_resources"):
            blueprint._methodview_openapi_resources = []

        blueprint._methodview_openapi_resources.append((cls, url))

        return view_func


def extract_pydantic_data(model_class: Type[BaseModel]) -> BaseModel:
    """
    Extract data from the request based on a Pydantic model.

    Args:
        model_class: The Pydantic model class to use for validation

    Returns:
        A Pydantic model instance with validated data

    Raises:
        ValidationError: If the data doesn't match the model
    """
    if request.is_json:
        data = request.get_json(silent=True) or {}
    elif request.form:
        data = request.form.to_dict()
    else:
        data = {}

    # Add query parameters
    if request.args:
        for key, value in request.args.items():
            if key not in data:
                data[key] = value

    # Validate with Pydantic and return the model instance
    return model_class(**data)


def extract_openapi_parameters_from_methodview(
    view_class: Type[MethodView], method: str, url: str
) -> List[Dict[str, Any]]:
    """
    Extract OpenAPI parameters from a MethodView class method.

    Args:
        view_class: The MethodView class
        method: The HTTP method (get, post, etc.)
        url: The URL rule

    Returns:
        List of OpenAPI parameter objects
    """
    from ...core.cache import get_parameter_prefixes

    parameters = []

    # Get the method function
    method_func = getattr(view_class, method.lower(), None)
    if not method_func:
        return parameters

    # Get type hints for the method
    type_hints = get_type_hints(method_func)

    # Get parameter prefixes from current configuration
    _, _, path_prefix, _ = get_parameter_prefixes()
    path_prefix_len = len(path_prefix) + 1  # +1 for the underscore

    # Extract path parameters from URL
    path_params = []
    for segment in url.split("/"):
        if segment.startswith("<") and segment.endswith(">"):
            # Handle Flask's converter syntax: <converter:name>
            if ":" in segment[1:-1]:
                _, name = segment[1:-1].split(":", 1)  # Ignore the converter part
            else:
                name = segment[1:-1]
            path_params.append(name)

    # Add path parameters
    for param_name in path_params:
        # Check if this is a prefixed parameter (e.g., _x_path_*)
        # If so, extract the actual parameter name
        actual_param_name = param_name
        if param_name.startswith(f"{path_prefix}_"):
            actual_param_name = param_name[path_prefix_len:]

        param_type = type_hints.get(param_name, str)
        param_schema = {"type": "string"}

        # Map Python types to OpenAPI types
        if param_type is int:
            param_schema = {"type": "integer"}
        elif param_type is float:
            param_schema = {"type": "number"}
        elif param_type is bool:
            param_schema = {"type": "boolean"}

        parameters.append(
            {
                "name": actual_param_name,
                "in": "path",
                "required": True,
                "schema": param_schema,
            }
        )

    # Check for request body in type hints
    for param_name, param_type in type_hints.items():
        # Skip path parameters and return type
        if param_name in path_params or param_name == "return":
            continue

        # Check if it's a Pydantic model
        if isinstance(param_type, type) and issubclass(param_type, BaseModel):
            # This is likely a request body
            # The actual parameter handling will be done by the decorator
            pass

    return parameters


class MethodViewOpenAPISchemaGenerator(OpenAPISchemaGenerator):
    """
    OpenAPI schema generator for Flask.MethodView classes.
    """

    def process_methodview_resources(self, blueprint):
        """
        Process MethodView resources registered to a blueprint.

        Args:
            blueprint: The Flask blueprint with registered MethodView resources
        """
        if not hasattr(blueprint, "_methodview_openapi_resources"):
            return

        for view_class, url in blueprint._methodview_openapi_resources:
            self._process_methodview(view_class, url, blueprint.url_prefix or "")

    def _register_models_from_method(self, method):
        """
        Register Pydantic models from method type hints.

        Args:
            method: The method to extract models from
        """
        # Get type hints for the method
        type_hints = get_type_hints(method)

        # Check each parameter for Pydantic models
        for param_name, param_type in type_hints.items():
            if param_name == "return":
                continue

            # Check if the parameter is a Pydantic model
            if isinstance(param_type, type) and issubclass(param_type, BaseModel):
                # Register the model
                self._register_model(param_type)

    def _process_methodview(self, view_class, url, url_prefix):
        """
        Process a MethodView class for OpenAPI schema generation.

        Args:
            view_class: The MethodView class
            url: The URL rule
            url_prefix: The URL prefix from the blueprint
        """
        # Get HTTP methods supported by the view
        methods = []
        for method in ["get", "post", "put", "delete", "patch"]:
            if hasattr(view_class, method):
                methods.append(method.upper())

        if not methods:
            return

        # Full URL path
        full_url = (url_prefix + url).replace("//", "/")

        # Get parameter prefixes from current configuration
        from ...core.cache import get_parameter_prefixes

        _, _, path_prefix, _ = get_parameter_prefixes()
        path_prefix_len = len(path_prefix) + 1  # +1 for the underscore

        # Convert Flask URL variables to OpenAPI path parameters
        path = full_url
        for segment in full_url.split("/"):
            if segment.startswith("<") and segment.endswith(">"):
                # Handle Flask's converter syntax: <converter:name>
                if ":" in segment[1:-1]:
                    _, name = segment[1:-1].split(":", 1)  # Ignore the converter part
                else:
                    name = segment[1:-1]

                # Remove prefix if present (e.g., _x_path_)
                actual_name = name
                if name.startswith(f"{path_prefix}_"):
                    actual_name = name[path_prefix_len:]

                # Replace with OpenAPI path parameter syntax
                path = path.replace(segment, "{" + actual_name + "}")

        # Process each method
        for method in methods:
            method_func = getattr(view_class, method.lower())

            # Get OpenAPI metadata from the method
            metadata = getattr(method_func, "_openapi_metadata", {})

            # If no metadata, try to generate some basic info
            if not metadata:
                metadata = {
                    "summary": method_func.__doc__.split("\n")[0]
                    if method_func.__doc__
                    else f"{method} {path}",
                    "description": method_func.__doc__ if method_func.__doc__ else "",
                }

                # Extract parameters
                parameters = extract_openapi_parameters_from_methodview(
                    view_class, method.lower(), url
                )
                if parameters:
                    metadata["parameters"] = parameters

            # Register Pydantic models from type hints
            self._register_models_from_method(method_func)

            # Add the path and method to the schema
            if path not in self.paths:
                self.paths[path] = {}

            self.paths[path][method.lower()] = metadata
