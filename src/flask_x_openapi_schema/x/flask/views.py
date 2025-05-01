"""Utilities for integrating Pydantic models with Flask.MethodView.

This module provides utilities for integrating Pydantic models with Flask.MethodView classes.
It includes classes and functions for collecting OpenAPI metadata from MethodView classes
and generating OpenAPI schema documentation.

Examples:
    Basic usage with Flask blueprint and MethodView:

    >>> from flask import Blueprint
    >>> from flask.views import MethodView
    >>> from flask_x_openapi_schema.x.flask import OpenAPIMethodViewMixin, openapi_metadata
    >>> from pydantic import BaseModel, Field
    >>>
    >>> class ItemResponse(BaseModel):
    ...     id: str = Field(..., description="Item ID")
    ...     name: str = Field(..., description="Item name")
    >>>
    >>> class ItemView(OpenAPIMethodViewMixin, MethodView):
    ...     @openapi_metadata(summary="Get an item")
    ...     def get(self, item_id: str):
    ...         return {"id": item_id, "name": "Example Item"}
    >>>
    >>> bp = Blueprint("items", __name__)
    >>> # Register the view to the blueprint
    >>> _ = ItemView.register_to_blueprint(bp, "/items/<item_id>")

"""

from typing import Any, get_type_hints

from flask.views import MethodView
from pydantic import BaseModel

from flask_x_openapi_schema.core.schema_generator import OpenAPISchemaGenerator


class OpenAPIMethodViewMixin:
    """A mixin class for Flask.MethodView to collect OpenAPI metadata.

    This mixin class adds OpenAPI schema generation capabilities to Flask's MethodView.
    It provides a method to register the view to a blueprint while collecting metadata
    for OpenAPI schema generation.

    Examples:
        >>> from flask import Blueprint
        >>> from flask.views import MethodView
        >>> from flask_x_openapi_schema.x.flask import OpenAPIMethodViewMixin, openapi_metadata
        >>> from pydantic import BaseModel, Field
        >>>
        >>> class ItemResponse(BaseModel):
        ...     id: str = Field(..., description="Item ID")
        ...     name: str = Field(..., description="Item name")
        >>>
        >>> class ItemView(OpenAPIMethodViewMixin, MethodView):
        ...     @openapi_metadata(summary="Get an item")
        ...     def get(self, item_id: str):
        ...         return {"id": item_id, "name": "Example Item"}
        >>>
        >>> bp = Blueprint("items", __name__)
        >>> # Register the view to the blueprint
        >>> _ = ItemView.register_to_blueprint(bp, "/items/<item_id>")

    """

    @classmethod
    def register_to_blueprint(cls, blueprint: Any, url: str, endpoint: str | None = None, **kwargs: Any) -> Any:
        """Register the MethodView to a blueprint and collect OpenAPI metadata.

        This method registers the view to a blueprint and stores metadata for
        OpenAPI schema generation.

        Args:
            blueprint: The Flask blueprint to register to
            url: The URL rule to register
            endpoint: The endpoint name (defaults to the class name)
            **kwargs: Additional arguments to pass to add_url_rule

        Returns:
            Any: The view function

        Examples:
            >>> from flask import Blueprint
            >>> from flask.views import MethodView
            >>> from flask_x_openapi_schema.x.flask import OpenAPIMethodViewMixin
            >>> class ItemView(OpenAPIMethodViewMixin, MethodView):
            ...     def get(self, item_id: str):
            ...         return {"id": item_id, "name": "Example Item"}
            >>> bp = Blueprint("items", __name__)
            >>> # Register the view to the blueprint
            >>> _ = ItemView.register_to_blueprint(bp, "/items/<item_id>")

        """
        view_func = cls.as_view(endpoint or cls.__name__.lower())
        blueprint.add_url_rule(url, view_func=view_func, **kwargs)

        if not hasattr(blueprint, "_methodview_openapi_resources"):
            blueprint._methodview_openapi_resources = []

        blueprint._methodview_openapi_resources.append((cls, url))

        return view_func


def extract_openapi_parameters_from_methodview(
    view_class: type[MethodView],
    method: str,
    url: str,
) -> list[dict[str, Any]]:
    """Extract OpenAPI parameters from a MethodView class method.

    Analyzes a MethodView class method to extract path parameters and their types
    for OpenAPI schema generation.

    Args:
        view_class: The MethodView class
        method: The HTTP method (get, post, etc.)
        url: The URL rule

    Returns:
        list[dict[str, Any]]: List of OpenAPI parameter objects

    """
    from flask_x_openapi_schema.core.cache import get_parameter_prefixes

    parameters = []

    method_func = getattr(view_class, method.lower(), None)
    if not method_func:
        return parameters

    type_hints = get_type_hints(method_func)

    _, _, path_prefix, _ = get_parameter_prefixes()
    path_prefix_len = len(path_prefix) + 1

    path_params = []
    for segment in url.split("/"):
        if segment.startswith("<") and segment.endswith(">"):
            if ":" in segment[1:-1]:
                _, name = segment[1:-1].split(":", 1)
            else:
                name = segment[1:-1]
            path_params.append(name)

    for param_name in path_params:
        actual_param_name = param_name
        if param_name.startswith(f"{path_prefix}_"):
            actual_param_name = param_name[path_prefix_len:]

        param_type = type_hints.get(param_name, str)
        param_schema = {"type": "string"}

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
            },
        )

    for param_name, param_type in type_hints.items():
        if param_name in path_params or param_name == "return":
            continue

        if isinstance(param_type, type) and issubclass(param_type, BaseModel):
            pass

    return parameters


class MethodViewOpenAPISchemaGenerator(OpenAPISchemaGenerator):
    """OpenAPI schema generator for Flask.MethodView classes.

    This class extends the base OpenAPISchemaGenerator to provide specific functionality
    for generating OpenAPI schema from Flask.MethodView classes. It processes MethodView
    resources registered to blueprints and extracts metadata for OpenAPI schema generation.
    """

    def process_methodview_resources(self, blueprint: Any) -> None:
        """Process MethodView resources registered to a blueprint.

        Extracts OpenAPI metadata from MethodView classes registered to a blueprint
        and adds them to the OpenAPI schema.

        Args:
            blueprint: The Flask blueprint with registered MethodView resources

        """
        if not hasattr(blueprint, "_methodview_openapi_resources"):
            return

        for view_class, url in blueprint._methodview_openapi_resources:
            self._process_methodview(view_class, url, blueprint.url_prefix or "")

    def _register_models_from_method(self, method: Any) -> None:
        """Register Pydantic models from method type hints.

        Extracts Pydantic models from method type hints and registers them
        in the OpenAPI schema components.

        Args:
            method: The method to extract models from

        """
        type_hints = get_type_hints(method)

        for param_name, param_type in type_hints.items():
            if param_name == "return":
                continue

            if isinstance(param_type, type) and issubclass(param_type, BaseModel):
                self._register_model(param_type)

        metadata = getattr(method, "_openapi_metadata", {})
        if "responses" in metadata and hasattr(metadata["responses"], "responses"):
            for response_item in metadata["responses"].responses.values():
                if response_item.model:
                    self._register_model(response_item.model)

    def _process_methodview(self, view_class: Any, url: str, url_prefix: str) -> None:
        """Process a MethodView class for OpenAPI schema generation.

        Extracts metadata from a MethodView class and adds it to the OpenAPI schema.
        Processes HTTP methods, path parameters, request bodies, and responses.

        Args:
            view_class: The MethodView class
            url: The URL rule
            url_prefix: The URL prefix from the blueprint

        """
        methods = [
            method.upper() for method in ["get", "post", "put", "delete", "patch"] if hasattr(view_class, method)
        ]

        if not methods:
            return

        full_url = (url_prefix + url).replace("//", "/")

        from flask_x_openapi_schema.core.cache import get_parameter_prefixes

        _, _, path_prefix, _ = get_parameter_prefixes()
        path_prefix_len = len(path_prefix) + 1

        path = full_url
        for segment in full_url.split("/"):
            if segment.startswith("<") and segment.endswith(">"):
                if ":" in segment[1:-1]:
                    _, name = segment[1:-1].split(":", 1)
                else:
                    name = segment[1:-1]

                actual_name = name
                if name.startswith(f"{path_prefix}_"):
                    actual_name = name[path_prefix_len:]

                path = path.replace(segment, "{" + actual_name + "}")

        for method in methods:
            method_func = getattr(view_class, method.lower())

            metadata = getattr(method_func, "_openapi_metadata", {})

            path_parameters = extract_openapi_parameters_from_methodview(view_class, method.lower(), url)

            if not metadata:
                metadata = {
                    "summary": method_func.__doc__.split("\n")[0] if method_func.__doc__ else f"{method} {path}",
                    "description": method_func.__doc__ if method_func.__doc__ else "",
                }

                if path_parameters:
                    metadata["parameters"] = path_parameters

            elif path_parameters:
                if "parameters" in metadata:
                    existing_path_param_names = [p["name"] for p in metadata["parameters"] if p.get("in") == "path"]
                    new_path_params = [p for p in path_parameters if p["name"] not in existing_path_param_names]
                    metadata["parameters"].extend(new_path_params)
                else:
                    metadata["parameters"] = path_parameters

            self._register_models_from_method(method_func)

            type_hints = get_type_hints(method_func)
            for param_name, param_type in type_hints.items():
                if param_name == "return":
                    continue

                if isinstance(param_type, type) and issubclass(param_type, BaseModel):
                    is_file_upload = False
                    has_binary_fields = False

                    if hasattr(param_type, "model_config"):
                        config = getattr(param_type, "model_config", {})
                        if isinstance(config, dict) and config.get("json_schema_extra", {}).get(
                            "multipart/form-data",
                            False,
                        ):
                            is_file_upload = True
                    elif hasattr(param_type, "Config") and hasattr(param_type.Config, "json_schema_extra"):
                        config_extra = getattr(param_type.Config, "json_schema_extra", {})
                        is_file_upload = config_extra.get("multipart/form-data", False)

                    if hasattr(param_type, "model_fields"):
                        for field_info in param_type.model_fields.values():
                            field_schema = getattr(field_info, "json_schema_extra", None)
                            if field_schema is not None and field_schema.get("format") == "binary":
                                has_binary_fields = True
                                break

                    if is_file_upload or has_binary_fields:
                        if "requestBody" in metadata and "content" in metadata["requestBody"]:
                            if "application/json" in metadata["requestBody"]["content"]:
                                schema = metadata["requestBody"]["content"]["application/json"]["schema"]
                                metadata["requestBody"]["content"] = {"multipart/form-data": {"schema": schema}}

                            elif not metadata["requestBody"]["content"]:
                                metadata["requestBody"]["content"] = {
                                    "multipart/form-data": {
                                        "schema": {"$ref": f"#/components/schemas/{param_type.__name__}"},
                                    },
                                }

                        elif "requestBody" not in metadata:
                            metadata["requestBody"] = {
                                "content": {
                                    "multipart/form-data": {
                                        "schema": {"$ref": f"#/components/schemas/{param_type.__name__}"},
                                    },
                                },
                                "required": True,
                            }

                        if "parameters" in metadata:
                            metadata["parameters"] = [p for p in metadata["parameters"] if p["in"] in ["path", "query"]]

            if "responses" in metadata and hasattr(metadata["responses"], "to_openapi_dict"):
                if hasattr(metadata["responses"], "responses"):
                    for response_item in metadata["responses"].responses.values():
                        if response_item.model:
                            self._register_model(response_item.model)

                            if hasattr(response_item.model, "model_fields"):
                                for field_info in response_item.model.model_fields.values():
                                    field_type = field_info.annotation

                                    if hasattr(field_type, "__origin__") and field_type.__origin__ is not None:
                                        args = getattr(field_type, "__args__", [])
                                        for arg in args:
                                            if hasattr(arg, "__members__"):
                                                self._register_model(arg)
                                    elif hasattr(field_type, "__members__"):
                                        self._register_model(field_type)

                metadata["responses"] = metadata["responses"].to_openapi_dict()

            if path not in self.paths:
                self.paths[path] = {}

            self.paths[path][method.lower()] = metadata
