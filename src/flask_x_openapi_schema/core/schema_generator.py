"""
OpenAPI Schema Generator for API documentation.

This module provides the main class for generating OpenAPI schemas from Flask-RESTful resources.
It handles scanning resources, extracting metadata, and generating a complete OpenAPI schema.
"""

import re
import threading
from functools import lru_cache
from typing import Any, Dict, List, Optional, Set, Type, get_type_hints

from flask import Blueprint
from flask_x_openapi_schema._opt_deps._flask_restful import Resource
from pydantic import BaseModel

from ..i18n.i18n_model import I18nBaseModel
from ..i18n.i18n_string import I18nStr, get_current_language
from .config import get_openapi_config
from .utils import pydantic_to_openapi_schema, process_i18n_dict, process_i18n_value


class OpenAPISchemaGenerator:
    """
    Generator for OpenAPI schemas from Flask-RESTful resources.

    This class scans Flask-RESTful resources and generates OpenAPI schemas based on
    the resource methods, docstrings, and type annotations.
    """

    def __init__(
        self,
        title: Optional[str] = None,
        version: Optional[str] = None,
        description: Optional[str] = None,
        language: Optional[str] = None,
    ):
        """
        Initialize the OpenAPI schema generator.

        Args:
            title: The title of the API (default: from config)
            version: The version of the API (default: from config)
            description: The description of the API (default: from config)
            language: The language to use for internationalized strings (default: current language)
        """
        # Get defaults from config if not provided
        config = get_openapi_config()

        # Handle I18nString for title and description
        self.title = title if title is not None else config.title
        if isinstance(self.title, I18nStr):
            self.title = self.title.get(language)

        self.version = version if version is not None else config.version

        self.description = (
            description if description is not None else config.description
        )
        if isinstance(self.description, I18nStr):
            self.description = self.description.get(language)

        self.language = language or get_current_language()

        # Initialize data structures
        self.paths: Dict[str, Dict[str, Any]] = {}
        self.components: Dict[str, Dict[str, Any]] = {
            "schemas": {},
            "securitySchemes": config.security_schemes.copy()
            if config.security_schemes
            else {},
        }
        self.tags: List[Dict[str, str]] = []
        self._registered_models: Set[Type[BaseModel]] = set()

        # Thread safety locks
        self._lock = threading.RLock()  # Main lock for coordinating access
        self._paths_lock = threading.RLock()
        self._components_lock = threading.RLock()
        self._tags_lock = threading.RLock()
        self._models_lock = threading.RLock()

    def add_security_scheme(self, name: str, scheme: dict[str, Any]) -> None:
        """
        Add a security scheme to the OpenAPI schema.

        Args:
            name: The name of the security scheme
            scheme: The security scheme definition
        """
        with self._components_lock:
            self.components["securitySchemes"][name] = scheme

    def add_tag(self, name: str, description: str = "") -> None:
        """
        Add a tag to the OpenAPI schema.

        Args:
            name: The name of the tag
            description: The description of the tag
        """
        with self._tags_lock:
            self.tags.append({"name": name, "description": description})

    def scan_blueprint(self, blueprint: Blueprint) -> None:
        """
        Scan a Flask blueprint for API resources and add them to the schema.

        Args:
            blueprint: The Flask blueprint to scan
        """
        # Get all resources registered to the blueprint
        if not hasattr(blueprint, "resources"):
            return

        for resource, urls, _ in blueprint.resources:
            self._process_resource(resource, urls, blueprint.url_prefix)

    def _process_resource(
        self, resource: type[Resource], urls: tuple[str], prefix: Optional[str] = None
    ) -> None:
        """
        Process a Flask-RESTful resource and add its endpoints to the schema.

        Args:
            resource: The Flask-RESTful resource class
            urls: The URLs registered for the resource
            prefix: The URL prefix for the resource
        """
        for url in urls:
            full_url = f"{prefix or ''}{url}"
            # Convert Flask URL parameters to OpenAPI parameters
            openapi_path = self._convert_flask_path_to_openapi_path(full_url)

            # Process HTTP methods and build operations
            http_methods = [
                "get",
                "post",
                "put",
                "delete",
                "patch",
                "head",
                "options",
            ]

            operations = {}
            for method_name in http_methods:
                if hasattr(resource, method_name):
                    method = getattr(resource, method_name)
                    operation = self._build_operation_from_method(method, resource)

                    # Add parameters from URL
                    path_params = self._extract_path_parameters(full_url)
                    if path_params:
                        if "parameters" not in operation:
                            operation["parameters"] = []

                        # Add path parameters without duplicates
                        existing_param_names = {
                            p["name"]
                            for p in operation["parameters"]
                            if p["in"] == "path"
                        }
                        for param in path_params:
                            if param["name"] not in existing_param_names:
                                operation["parameters"].append(param)
                                existing_param_names.add(param["name"])

                    operations[method_name] = operation

            # Update paths in a thread-safe manner
            with self._paths_lock:
                # Initialize path item if it doesn't exist
                if openapi_path not in self.paths:
                    self.paths[openapi_path] = {}

                # Add all operations at once
                for method_name, operation in operations.items():
                    self.paths[openapi_path][method_name] = operation

    def _convert_flask_path_to_openapi_path(self, flask_path: str) -> str:
        """
        Convert a Flask URL path to an OpenAPI path.

        Args:
            flask_path: The Flask URL path

        Returns:
            The OpenAPI path
        """
        from .cache import get_parameter_prefixes

        # Get parameter prefixes from current configuration
        _, _, path_prefix, _ = get_parameter_prefixes()
        path_prefix_len = len(path_prefix) + 1  # +1 for the underscore

        # Replace Flask's <converter:param> with OpenAPI's {param}
        # and remove any prefix from the parameter name
        def replace_param(match):
            param_name = match.group(1)

            # Remove prefix if present (e.g., _x_path_)
            if param_name.startswith(f"{path_prefix}_"):
                param_name = param_name[path_prefix_len:]

            return f"{{{param_name}}}"

        return re.sub(r"<(?:[^:>]+:)?([^>]+)>", replace_param, flask_path)

    def _extract_path_parameters(self, flask_path: str) -> list[dict[str, Any]]:
        """
        Extract path parameters from a Flask URL path.

        Args:
            flask_path: The Flask URL path

        Returns:
            A list of OpenAPI parameter objects
        """
        from .cache import get_parameter_prefixes

        # Get parameter prefixes from current configuration
        _, _, path_prefix, _ = get_parameter_prefixes()
        path_prefix_len = len(path_prefix) + 1  # +1 for the underscore

        parameters = []
        # Match Flask's <converter:param> or <param>
        for match in re.finditer(r"<(?:([^:>]+):)?([^>]+)>", flask_path):
            converter, param_name = match.groups()

            # Remove prefix if present (e.g., _x_path_)
            actual_param_name = param_name
            if param_name.startswith(f"{path_prefix}_"):
                actual_param_name = param_name[path_prefix_len:]

            param = {
                "name": actual_param_name,
                "in": "path",
                "required": True,
                "schema": self._get_schema_for_converter(converter or "string"),
            }
            parameters.append(param)
        return parameters

    def _get_schema_for_converter(self, converter: str) -> dict[str, Any]:
        """
        Get an OpenAPI schema for a Flask URL converter.

        Args:
            converter: The Flask URL converter

        Returns:
            An OpenAPI schema object
        """
        # Map Flask URL converters to OpenAPI types
        converter_map = {
            "string": {"type": "string"},
            "int": {"type": "integer"},
            "float": {"type": "number", "format": "float"},
            "path": {"type": "string"},
            "uuid": {"type": "string", "format": "uuid"},
            "any": {"type": "string"},
        }
        return converter_map.get(converter, {"type": "string"})

    @lru_cache(maxsize=128)
    def _get_operation_id(self, resource_name: str, method_name: str) -> str:
        """Generate a cached operation ID for a resource method."""
        return f"{resource_name}_{method_name}"

    def _build_operation_from_method(
        self, method: Any, resource_cls: type[Resource]
    ) -> dict[str, Any]:
        """
        Build an OpenAPI operation object from a Flask-RESTful resource method.

        Args:
            method: The resource method
            resource_cls: The resource class

        Returns:
            An OpenAPI operation object
        """
        operation: dict[str, Any] = {}

        # Get metadata from method if available
        metadata = getattr(method, "_openapi_metadata", {})

        # Process metadata, handling I18nString values
        for key, value in metadata.items():
            if isinstance(value, I18nStr):
                operation[key] = value.get(self.language)
            elif isinstance(value, dict):
                # Handle nested dictionaries that might contain I18nString values
                operation[key] = self._process_i18n_dict(value)
            else:
                operation[key] = value

        # Extract summary and description from docstring
        if method.__doc__:
            docstring = method.__doc__.strip()
            lines = docstring.split("\n")
            operation["summary"] = lines[0].strip()
            if len(lines) > 1:
                operation["description"] = "\n".join(
                    line.strip() for line in lines[1:]
                ).strip()

        # Get operation ID
        if "operationId" not in operation:
            operation["operationId"] = self._get_operation_id(
                resource_cls.__name__, method.__name__
            )

        # Extract request and response schemas from type annotations
        self._add_request_schema(method, operation)
        self._add_response_schema(method, operation)

        return operation

    def _add_request_schema(self, method: Any, operation: dict[str, Any]) -> None:
        """
        Add request schema to an OpenAPI operation based on method type annotations.

        Args:
            method: The resource method
            operation: The OpenAPI operation object to update
        """
        type_hints = get_type_hints(method)

        # Look for parameters that might be request bodies
        for param_name, param_type in type_hints.items():
            if param_name == "return":
                continue

            # Check if the parameter is a Pydantic model
            if isinstance(param_type, type) and issubclass(param_type, BaseModel):
                self._register_model(param_type)

                # Check if this is a file upload model
                is_file_upload = False
                has_binary_fields = False

                # Check model config for multipart/form-data flag
                if hasattr(param_type, "model_config"):
                    config = getattr(param_type, "model_config", {})
                    if isinstance(config, dict) and config.get(
                        "json_schema_extra", {}
                    ).get("multipart/form-data", False):
                        is_file_upload = True
                elif hasattr(param_type, "Config") and hasattr(
                    param_type.Config, "json_schema_extra"
                ):
                    config_extra = getattr(param_type.Config, "json_schema_extra", {})
                    is_file_upload = config_extra.get("multipart/form-data", False)

                # Check if model has any binary fields
                if hasattr(param_type, "model_fields"):
                    for field_name, field_info in param_type.model_fields.items():
                        field_schema = getattr(field_info, "json_schema_extra", None)
                        if (
                            field_schema is not None
                            and field_schema.get("format") == "binary"
                        ):
                            has_binary_fields = True
                            break

                # Determine content type based on model properties
                content_type = (
                    "multipart/form-data"
                    if (is_file_upload or has_binary_fields)
                    else "application/json"
                )

                # Add request body with appropriate content type
                operation["requestBody"] = {
                    "content": {
                        content_type: {
                            "schema": {
                                "$ref": f"#/components/schemas/{param_type.__name__}"
                            }
                        }
                    },
                    "required": True,
                }

                # If this is a file upload model, remove any file parameters from parameters
                # as they will be included in the requestBody
                if is_file_upload or has_binary_fields:
                    if "parameters" in operation:
                        # Keep only path and query parameters
                        operation["parameters"] = [
                            p
                            for p in operation["parameters"]
                            if p["in"] in ["path", "query"]
                        ]
                break

    def _add_response_schema(self, method: Any, operation: dict[str, Any]) -> None:
        """
        Add response schema to an OpenAPI operation based on method return type annotation.

        Args:
            method: The resource method
            operation: The OpenAPI operation object to update
        """
        type_hints = get_type_hints(method)

        # Check if there's a return type hint
        if "return" in type_hints:
            return_type = type_hints["return"]

            # Handle Pydantic models
            if isinstance(return_type, type) and issubclass(return_type, BaseModel):
                self._register_model(return_type)

                operation["responses"] = {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": f"#/components/schemas/{return_type.__name__}"
                                }
                            }
                        },
                    }
                }
            else:
                # Default response
                operation["responses"] = {"200": {"description": "Successful response"}}
        else:
            # Default response if no return type is specified
            operation["responses"] = {"200": {"description": "Successful response"}}

    def _register_model(self, model: type) -> None:
        """
        Register a Pydantic model or enum in the components schemas.

        Args:
            model: The model to register (Pydantic model or enum)
        """
        with self._models_lock:
            # Skip if already registered
            if model in self._registered_models:
                return

            # Add to registered models set
            self._registered_models.add(model)

        # Handle enum types
        if hasattr(model, "__members__"):
            # This is an enum type
            with self._components_lock:
                enum_schema = {"type": "string", "enum": [e.value for e in model]}

                if model.__name__ not in self.components["schemas"]:
                    self.components["schemas"][model.__name__] = enum_schema
            return

        # Handle Pydantic models
        if not issubclass(model, BaseModel):
            return

        # Generate schema (thread-safe via utils.py caching)
        try:
            if issubclass(model, I18nBaseModel):
                # Create a language-specific version of the model
                language_model = model.for_language(self.language)
                schema = pydantic_to_openapi_schema(language_model)
            else:
                # Use the cached version from utils.py
                schema = pydantic_to_openapi_schema(model)

            # Update components in a thread-safe manner
            with self._components_lock:
                self.components["schemas"][model.__name__] = schema
        except Exception as e:
            print(f"Error registering model {model.__name__}: {e}")

        # Register nested models
        self._register_nested_models(model)

    def _register_nested_models(self, model: type[BaseModel]) -> None:
        """
        Register nested Pydantic models found in fields of the given model.

        Args:
            model: The Pydantic model to scan for nested models
        """
        # Get model fields
        if not hasattr(model, "model_fields"):
            return

        # Check each field for nested models
        for field_name, field_info in model.model_fields.items():
            field_type = field_info.annotation

            # Handle direct BaseModel references
            if isinstance(field_type, type) and issubclass(field_type, BaseModel):
                self._register_model(field_type)
                continue

            # Handle List[BaseModel] and similar container types
            origin = getattr(field_type, "__origin__", None)
            args = getattr(field_type, "__args__", [])

            if origin and args:
                for arg in args:
                    if isinstance(arg, type) and issubclass(arg, BaseModel):
                        self._register_model(arg)
                    elif hasattr(arg, "__members__"):
                        # Handle enum types
                        # Register enum in components/schemas
                        with self._components_lock:
                            enum_schema = {
                                "type": "string",
                                "enum": [e.value for e in arg],
                            }

                            if arg.__name__ not in self.components["schemas"]:
                                self.components["schemas"][arg.__name__] = enum_schema

            # Handle enum types directly
            elif hasattr(field_type, "__members__"):
                # Register enum in components/schemas
                with self._components_lock:
                    enum_schema = {
                        "type": "string",
                        "enum": [e.value for e in field_type],
                    }

                    if field_type.__name__ not in self.components["schemas"]:
                        self.components["schemas"][field_type.__name__] = enum_schema

    def _process_i18n_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a dictionary that might contain I18nString values.

        Args:
            data: The dictionary to process

        Returns:
            A new dictionary with I18nString values converted to strings
        """
        return process_i18n_dict(data, self.language)

    def _process_i18n_value(self, value: Any) -> Any:
        """
        Process a value that might be an I18nString or contain I18nString values.

        Args:
            value: The value to process

        Returns:
            The processed value
        """
        return process_i18n_value(value, self.language)

    def generate_schema(self) -> Dict[str, Any]:
        """
        Generate the complete OpenAPI schema.

        Returns:
            The OpenAPI schema as a dictionary
        """
        # Use a lock to ensure consistent state during schema generation
        with self._lock:
            return {
                "openapi": "3.0.3",
                "info": {
                    "title": self.title,
                    "version": self.version,
                    "description": self.description,
                },
                "paths": self.paths,
                "components": self.components,
                "tags": self.tags,
            }
