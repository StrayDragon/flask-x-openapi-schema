"""Utilities for integrating Pydantic models with Flask-RESTful."""

import inspect
from collections.abc import Callable
from enum import Enum
from typing import Any, Union, get_args, get_origin

from pydantic import BaseModel

from flask_x_openapi_schema._opt_deps._flask_restful import HAS_FLASK_RESTFUL, reqparse
from flask_x_openapi_schema.models.file_models import FileField

IMPORT_ERROR_MSG = """
The 'Flask-RESTful integration' feature requires the 'flask-restful' package, "
which is not installed. Please install it with: pip install flask-restful or "
pip install flask-x-openapi-schema[flask-restful]
""".strip()


def pydantic_model_to_reqparse(
    model: type[BaseModel],
    location: str = "json",
    exclude: list[str] | None = None,
) -> reqparse.RequestParser:
    """Convert a Pydantic model to a Flask-RESTful RequestParser.

    Args:
        model: The Pydantic model to convert
        location: The location to parse arguments from (json, form, args, etc.)
        exclude: Fields to exclude from the parser

    Returns:
        A Flask-RESTful RequestParser

    """
    if not HAS_FLASK_RESTFUL:
        raise ImportError(IMPORT_ERROR_MSG)

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
        # Handle special cases for new style union types (X | None)
        annotation_str = str(field_info.annotation)
        if annotation_str == "float | None":
            field_type = float
        elif annotation_str == "int | None":
            field_type = int
        elif annotation_str == "str | None":
            field_type = str
        elif annotation_str == "bool | None":
            # Use the same bool conversion function as in _get_field_type
            field_type = bool
        else:
            field_type = _get_field_type(field_info.annotation)

        # Get field description
        description = field_schema.get("description", "")

        # Check if this is a file field
        is_file_field = False
        if inspect.isclass(field_info.annotation) and issubclass(field_info.annotation, FileField):
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


def _get_field_type(annotation: Any) -> Callable:  # noqa: PLR0911
    """Get the appropriate type function for a field annotation.

    Args:
        annotation: The field annotation

    Returns:
        A type function

    """
    # Handle basic types
    if annotation is str:
        return str
    if annotation is int:
        return int
    if annotation is float:
        return float
    if annotation is bool:
        return lambda x: x.lower() == "true" if isinstance(x, str) else bool(x)
    if annotation is list:
        return list
    if annotation is dict:
        return dict

    # Handle Union types (including Optional)
    origin = get_origin(annotation)
    if origin is Union:
        args = get_args(annotation)
        # Check if it's Optional[X] (Union[X, None])
        if len(args) == 2 and args[1] is type(None):  # noqa: PLR2004
            # Get the type of the first argument (the non-None type)
            non_none_type = args[0]
            # Handle specific types directly
            if non_none_type is float:
                return float
            if non_none_type is int:
                return int
            if non_none_type is str:
                return str
            if non_none_type is bool:
                return lambda x: x.lower() == "true" if isinstance(x, str) else bool(x)
            # For other types, recurse
            return _get_field_type(non_none_type)

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
    query_model: type[BaseModel] | None = None,
    body_model: type[BaseModel] | None = None,
    form_model: type[BaseModel] | None = None,
    file_model: type[BaseModel] | None = None,
) -> reqparse.RequestParser:
    """Create a Flask-RESTful RequestParser from Pydantic models.

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
            IMPORT_ERROR_MSG,
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
            for field_info in body_model.model_fields.values():
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
