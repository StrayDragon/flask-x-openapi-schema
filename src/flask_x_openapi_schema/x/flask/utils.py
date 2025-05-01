"""Utility functions for Flask integration.

This module provides utility functions for integrating Flask with OpenAPI schema generation.
It includes functions for generating OpenAPI schemas from Flask blueprints, registering
Pydantic models with schema generators, and extracting data from requests based on
Pydantic models.
"""

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
        blueprint: The Flask blueprint with registered MethodView classes.
        title: The title of the API. Can be a string or I18nStr for internationalization.
        version: The version of the API.
        description: The description of the API. Can be a string or I18nStr for internationalization.
        output_format: The output format. Options are "yaml" or "json". Defaults to "yaml".
        language: The language to use for internationalized strings. If None, uses the current language.

    Returns:
        dict or str: The OpenAPI schema as a dictionary (if output_format is "json")
            or as a YAML string (if output_format is "yaml").

    Examples:
        >>> from flask import Blueprint
        >>> bp = Blueprint("api", __name__)
        >>> schema = generate_openapi_schema(
        ...     blueprint=bp, title="My API", version="1.0.0", description="My API Description", output_format="yaml"
        ... )
        >>> isinstance(schema, str)
        True
        >>> "title: My API" in schema
        True

    """
    current_lang = language or get_current_language()

    generator = MethodViewOpenAPISchemaGenerator(
        title=title,
        version=version,
        description=description,
        language=current_lang,
    )

    generator.process_methodview_resources(blueprint=blueprint)

    schema = generator.generate_schema()

    if output_format == "yaml":
        import yaml

        return yaml.dump(schema, sort_keys=False, default_flow_style=False, allow_unicode=True)
    return schema


def register_model_schema(generator: OpenAPISchemaGenerator, model: type[BaseModel]) -> None:
    """Register a Pydantic model schema with an OpenAPI schema generator.

    This function registers a Pydantic model with the OpenAPI schema generator,
    making it available in the components/schemas section of the generated OpenAPI schema.

    Args:
        generator: The OpenAPI schema generator instance.
        model: The Pydantic model class to register.

    Examples:
        >>> from pydantic import BaseModel, Field
        >>> from flask_x_openapi_schema.x.flask.views import MethodViewOpenAPISchemaGenerator
        >>> class User(BaseModel):
        ...     id: int = Field(..., description="User ID")
        ...     name: str = Field(..., description="User name")
        >>> generator = MethodViewOpenAPISchemaGenerator(title="My API", version="1.0.0")
        >>> register_model_schema(generator, User)
        >>> schema = generator.generate_schema()
        >>> "User" in schema["components"]["schemas"]
        True

    Note:
        This function uses the internal _register_model method of the generator.

    """
    generator._register_model(model)


def extract_pydantic_data(model_class: type[BaseModel]) -> BaseModel:
    """Extract data from the request based on a Pydantic model.

    This function extracts data from the current Flask request and validates it
    against the provided Pydantic model. It handles JSON data, form data, and
    query parameters.

    Args:
        model_class: The Pydantic model class to use for validation.

    Returns:
        BaseModel: A validated instance of the provided Pydantic model.

    Raises:
        ValidationError: If the request data doesn't match the model's schema.

    Examples:
        >>> from flask import Flask, request
        >>> from pydantic import BaseModel, Field
        >>> app = Flask(__name__)
        >>> class UserCreate(BaseModel):
        ...     username: str
        ...     email: str
        ...     age: int = Field(gt=0)
        >>> @app.route("/users", methods=["POST"])
        ... def create_user():
        ...     # In a real request context:
        ...     user_data = extract_pydantic_data(UserCreate)
        ...     # user_data is now a validated UserCreate instance
        ...     return {"id": 1, "username": user_data.username}

    Note:
        This function combines data from request.json, request.form, and request.args.

    """
    if request.is_json:
        data = request.get_json(silent=True) or {}
    elif request.form:
        data = request.form.to_dict()
    else:
        data = {}

    if request.args:
        for key, value in request.args.items():
            if key not in data:
                data[key] = value

    return model_class(**data)
