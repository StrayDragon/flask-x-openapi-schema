"""Utility functions for Flask integration."""

from typing import Any

from flask import Blueprint, request
from pydantic import BaseModel

from flask_x_openapi_schema.core.schema_generator import OpenAPISchemaGenerator
from flask_x_openapi_schema.i18n.i18n_string import I18nStr, get_current_language

from .views import MethodViewOpenAPISchemaGenerator


def generate_openapi_schema(
    blueprint: Blueprint,
    title: str | I18nStr,
    version: str,
    description: str | I18nStr = "",
    output_format: str = "yaml",
    language: str | None = None,
) -> dict[str, Any] | str:
    """Generate an OpenAPI schema from a Flask blueprint with MethodView classes.

    Args:
        blueprint: The Flask blueprint with registered MethodView classes
        title: The title of the API
        version: The version of the API
        description: The description of the API
        output_format: The output format (yaml or json)
        language: The language to use for internationalized strings

    Returns:
        The OpenAPI schema as a dictionary (if json) or string (if yaml)

    """
    # Use the specified language or get the current language
    current_lang = language or get_current_language()

    # Create a schema generator for MethodView classes
    generator = MethodViewOpenAPISchemaGenerator(
        title=title,
        version=version,
        description=description,
        language=current_lang,
    )

    # Process MethodView resources
    generator.process_methodview_resources(blueprint=blueprint)

    # Generate the schema
    schema = generator.generate_schema()

    # Return the schema in the requested format
    if output_format == "yaml":
        import yaml

        return yaml.dump(schema, sort_keys=False, default_flow_style=False, allow_unicode=True)
    return schema


def register_model_schema(generator: OpenAPISchemaGenerator, model: type[BaseModel]) -> None:
    """Register a Pydantic model schema with an OpenAPI schema generator.

    Args:
        generator: The OpenAPI schema generator
        model: The Pydantic model to register

    """
    generator._register_model(model)  # noqa: SLF001


def extract_pydantic_data(model_class: type[BaseModel]) -> BaseModel:
    """Extract data from the request based on a Pydantic model.

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
