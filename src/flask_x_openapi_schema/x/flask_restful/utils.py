"""Utilities for Flask-RESTful integration.

This module provides utilities for integrating Pydantic models with Flask-RESTful,
enabling automatic conversion of Pydantic models to Flask-RESTful RequestParser objects.

The main functionality allows for seamless integration between Pydantic's validation
capabilities and Flask-RESTful's request parsing system.
"""

import logging

from flask_restful import reqparse
from pydantic import BaseModel

logger = logging.getLogger(__name__)


def create_reqparse_from_pydantic(
    model: type[BaseModel], location: str = "json", bundle_errors: bool = True
) -> reqparse.RequestParser:
    """Create a Flask-RESTful RequestParser from a Pydantic model.

    Converts a Pydantic model into a Flask-RESTful RequestParser, mapping Pydantic
    field types to appropriate Python types for request parsing. Handles basic types
    as well as lists (arrays) and preserves field descriptions and required status.

    Args:
        model: The Pydantic model class to convert to a RequestParser.
        location: The location to look for arguments. Options include 'json',
            'form', 'args', 'headers', etc. Defaults to 'json'.
        bundle_errors: Whether to bundle all errors in a single response.
            When False, the first error is returned. Defaults to True.

    Returns:
        reqparse.RequestParser: A configured Flask-RESTful RequestParser instance
            that can be used to parse and validate incoming requests.

    Examples:
        >>> from pydantic import BaseModel, Field
        >>> from flask_restful import reqparse
        >>> class UserModel(BaseModel):
        ...     name: str = Field(..., description="User's full name")
        ...     age: int = Field(..., description="User's age in years")
        ...     tags: list[str] = Field([], description="User tags")
        >>> parser = create_reqparse_from_pydantic(UserModel)
        >>> isinstance(parser, reqparse.RequestParser)
        True

    """
    parser = reqparse.RequestParser(bundle_errors=bundle_errors)

    schema = model.model_json_schema()
    properties = schema.get("properties", {})
    required = schema.get("required", [])

    for field_name, field_schema in properties.items():
        field_type = field_schema.get("type")
        field_description = field_schema.get("description", "")
        field_required = field_name in required

        type_mapping = {
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
            "array": list,
            "object": dict,
        }

        python_type = type_mapping.get(field_type, str)

        if field_type == "array":
            items = field_schema.get("items", {})
            item_type = items.get("type", "string")
            python_item_type = type_mapping.get(item_type, str)

            parser.add_argument(
                field_name,
                type=python_item_type,
                action="append",
                required=field_required,
                help=field_description,
                location=location,
            )
        else:
            parser.add_argument(
                field_name,
                type=python_type,
                required=field_required,
                help=field_description,
                location=location,
            )

    return parser
