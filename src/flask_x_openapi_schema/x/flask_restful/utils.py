"""Utilities for Flask-RESTful integration.

This module provides utilities for integrating Pydantic models with Flask-RESTful.
"""

import logging

from flask_restful import reqparse
from pydantic import BaseModel

logger = logging.getLogger(__name__)


def create_reqparse_from_pydantic(
    model: type[BaseModel], location: str = "json", bundle_errors: bool = True
) -> reqparse.RequestParser:
    """Create a Flask-RESTful RequestParser from a Pydantic model.

    Args:
        model: The Pydantic model to convert
        location: The location to look for arguments (default: 'json')
        bundle_errors: Whether to bundle errors (default: True)

    Returns:
        A Flask-RESTful RequestParser

    """
    parser = reqparse.RequestParser(bundle_errors=bundle_errors)

    # Get the model schema
    schema = model.model_json_schema()
    properties = schema.get("properties", {})
    required = schema.get("required", [])

    # Add arguments to the parser
    for field_name, field_schema in properties.items():
        field_type = field_schema.get("type")
        field_description = field_schema.get("description", "")
        field_required = field_name in required

        # Map Pydantic types to Python types
        type_mapping = {
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
            "array": list,
            "object": dict,
        }

        # Get the Python type
        python_type = type_mapping.get(field_type, str)

        # Handle arrays
        if field_type == "array":
            # Get the item type
            items = field_schema.get("items", {})
            item_type = items.get("type", "string")
            python_item_type = type_mapping.get(item_type, str)

            # Add the argument
            parser.add_argument(
                field_name,
                type=python_item_type,
                action="append",
                required=field_required,
                help=field_description,
                location=location,
            )
        else:
            # Add the argument
            parser.add_argument(
                field_name,
                type=python_type,
                required=field_required,
                help=field_description,
                location=location,
            )

    return parser
