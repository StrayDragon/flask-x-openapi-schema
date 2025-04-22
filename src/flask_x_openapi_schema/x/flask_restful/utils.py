"""
Utilities for integrating Pydantic models with Flask-RESTful.
"""

import inspect
from collections.abc import Callable
from enum import Enum
from typing import Any, Optional, Union

from flask_x_openapi_schema._opt_deps._flask_restful import reqparse, HAS_FLASK_RESTFUL


from pydantic import BaseModel

from ...models.file_models import FileField


def pydantic_model_to_reqparse(
    model: type[BaseModel], location: str = "json", exclude: Optional[list[str]] = None
) -> reqparse.RequestParser:
    """
    Convert a Pydantic model to a Flask-RESTful RequestParser.

    Args:
        model: The Pydantic model to convert
        location: The location to parse arguments from (json, form, args, etc.)
        exclude: Fields to exclude from the parser

    Returns:
        A Flask-RESTful RequestParser
    """
    if not HAS_FLASK_RESTFUL:
        raise ImportError(
            "The 'Flask-RESTful integration' feature requires the 'flask-restful' package, "
            "which is not installed. Please install it with: pip install flask-restful or "
            "pip install flask-x-openapi-schema[flask-restful]"
        )

    parser = reqparse.RequestParser()
    exclude = exclude or []

    # Get model schema
    schema = model.model_json_schema()
    properties = schema.get("properties", {})
    required = schema.get("required", [])

    for field_name, field_schema in properties.items():
        if field_name in exclude:
            continue

        # Get field from model
        field_info = model.model_fields.get(field_name)
        if not field_info:
            continue

        # Determine if field is required
        is_required = field_name in required

        # Get field type
        field_type = _get_field_type(field_info.annotation)

        # Get field description
        description = field_schema.get("description", "")

        # Check if this is a file field
        is_file_field = False
        if inspect.isclass(field_info.annotation) and issubclass(
            field_info.annotation, FileField
        ):
            is_file_field = True

        # Add argument to parser with appropriate settings
        if is_file_field and location == "files":
            # For file uploads, we don't need type conversion
            parser.add_argument(
                field_name,
                type=field_type,
                required=is_required,
                location="files",  # Always use 'files' location for file fields
                help=description,
                nullable=not is_required,
            )
        else:
            # For regular fields
            parser.add_argument(
                field_name,
                type=field_type,
                required=is_required,
                location=location,
                help=description,
                nullable=not is_required,
            )

    return parser


def _get_field_type(annotation: Any) -> Callable:
    """
    Get the appropriate type function for a field annotation.

    Args:
        annotation: The field annotation

    Returns:
        A type function
    """
    # Handle basic types
    if annotation is str:
        return str
    elif annotation is int:
        return int
    elif annotation is float:
        return float
    elif annotation is bool:
        return lambda x: x.lower() == "true" if isinstance(x, str) else bool(x)
    elif annotation is list:
        return list
    elif annotation is dict:
        return dict

    # Handle Optional types
    origin = getattr(annotation, "__origin__", None)
    if origin == Union:
        args = getattr(annotation, "__args__", [])
        # Check if it's Optional[X]
        if len(args) == 2 and args[1] is type(None):
            return _get_field_type(args[0])

    # Handle Enum types
    if inspect.isclass(annotation) and issubclass(annotation, Enum):
        return lambda x: annotation(x)

    # Handle FileField types
    if inspect.isclass(annotation) and issubclass(annotation, FileField):
        # For file uploads, we don't need to convert the type
        return lambda x: x

    # Default to string
    return str


def create_reqparse_from_pydantic(
    query_model: Optional[type[BaseModel]] = None,
    body_model: Optional[type[BaseModel]] = None,
    form_model: Optional[type[BaseModel]] = None,
    file_model: Optional[type[BaseModel]] = None,
) -> reqparse.RequestParser:
    """
    Create a Flask-RESTful RequestParser from Pydantic models.

    Args:
        query_model: Pydantic model for query parameters
        body_model: Pydantic model for request body
        form_model: Pydantic model for form data
        file_model: Pydantic model for file uploads

    Returns:
        A Flask-RESTful RequestParser
    """
    if not HAS_FLASK_RESTFUL:
        raise ImportError(
            "The 'Flask-RESTful integration' feature requires the 'flask-restful' package, "
            "which is not installed. Please install it with: pip install flask-restful or "
            "pip install flask-x-openapi-schema[flask-restful]"
        )

    parser = reqparse.RequestParser()

    if query_model:
        query_parser = pydantic_model_to_reqparse(query_model, location="args")
        for arg in query_parser.args:
            parser.args.append(arg)

    if body_model:
        # Check if this is a file upload model
        has_file_fields = False
        if hasattr(body_model, "model_fields"):
            for field_name, field_info in body_model.model_fields.items():
                field_type = field_info.annotation
                if inspect.isclass(field_type) and issubclass(field_type, FileField):
                    has_file_fields = True
                    break

        # If model has file fields, use form location
        if has_file_fields:
            body_parser = pydantic_model_to_reqparse(body_model, location="files")
        else:
            body_parser = pydantic_model_to_reqparse(body_model, location="json")

        for arg in body_parser.args:
            parser.args.append(arg)

    if form_model:
        form_parser = pydantic_model_to_reqparse(form_model, location="form")
        for arg in form_parser.args:
            parser.args.append(arg)

    if file_model:
        file_parser = pydantic_model_to_reqparse(file_model, location="files")
        for arg in file_parser.args:
            parser.args.append(arg)

    return parser
