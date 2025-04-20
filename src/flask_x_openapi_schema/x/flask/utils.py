"""
Utility functions for Flask integration.
"""

from typing import Any, Dict, Optional, Type, Union

from flask import Blueprint
from pydantic import BaseModel

from ...core.schema_generator import OpenAPISchemaGenerator
from ...i18n.i18n_string import I18nStr, get_current_language
from .views import MethodViewOpenAPISchemaGenerator


def generate_openapi_schema(
    blueprint: Blueprint,
    title: Union[str, I18nStr],
    version: str,
    description: Union[str, I18nStr] = "",
    output_format: str = "yaml",
    language: Optional[str] = None,
) -> Union[Dict[str, Any], str]:
    """
    Generate an OpenAPI schema from a Flask blueprint with MethodView classes.

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
        title=title, version=version, description=description, language=current_lang
    )

    # Process MethodView resources
    generator.process_methodview_resources(blueprint)

    # Generate the schema
    schema = generator.generate_schema()

    # Return the schema in the requested format
    if output_format == "yaml":
        import yaml

        return yaml.dump(
            schema, sort_keys=False, default_flow_style=False, allow_unicode=True
        )
    else:
        return schema


def register_model_schema(
    generator: OpenAPISchemaGenerator, model: Type[BaseModel]
) -> None:
    """
    Register a Pydantic model schema with an OpenAPI schema generator.

    Args:
        generator: The OpenAPI schema generator
        model: The Pydantic model to register
    """
    generator._register_model(model)
