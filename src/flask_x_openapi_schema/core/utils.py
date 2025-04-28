"""Utility functions for OpenAPI schema generation.

This module provides utility functions for converting Pydantic models to OpenAPI schemas,
handling references, and processing internationalized strings.
"""

import inspect
from datetime import date, datetime, time
from enum import Enum
from typing import Any, Union
from uuid import UUID

from pydantic import BaseModel


def pydantic_to_openapi_schema(model: type[BaseModel]) -> dict[str, Any]:
    """Convert a Pydantic model to an OpenAPI schema.

    This function converts a Pydantic model to an OpenAPI schema.

    Args:
        model: The Pydantic model to convert

    Returns:
        The OpenAPI schema for the model

    """
    # Initialize schema with default values
    schema: dict[str, Any] = {"type": "object", "properties": {}, "required": []}

    # Get model schema from Pydantic
    model_schema = model.model_json_schema()

    # Extract properties and required fields
    if "properties" in model_schema:
        # Process properties to fix references
        properties = {}
        for prop_name, prop_schema in model_schema["properties"].items():
            properties[prop_name] = _fix_references(prop_schema)
        schema["properties"] = properties

    # Copy required fields if present
    if "required" in model_schema:
        schema["required"] = model_schema["required"]

    # Add description if available
    if model.__doc__:
        schema["description"] = model.__doc__.strip()

    return schema


# Reference handling for OpenAPI schema generation


def _fix_references(schema: dict[str, Any]) -> dict[str, Any]:
    """Fix references in a schema to use components/schemas instead of $defs.

    Also applies any json_schema_extra attributes to the schema.

    Args:
        schema: The schema to fix

    Returns:
        The fixed schema

    """
    # Get OpenAPI configuration to check version
    from .config import get_openapi_config

    config = get_openapi_config()
    is_openapi_31 = config.openapi_version.startswith("3.1")

    # Handle non-dict inputs
    if not isinstance(schema, dict):
        return schema

    # Fast path for schemas without references or special handling
    has_ref = (
        "$ref" in schema
        and isinstance(schema["$ref"], str)
        and ("#/$defs/" in schema["$ref"] or "#/definitions/" in schema["$ref"])
    )
    has_extra = "json_schema_extra" in schema
    has_file = "type" in schema and schema["type"] == "string" and "format" in schema and schema["format"] == "binary"
    has_nullable = "nullable" in schema and is_openapi_31  # Need to convert nullable in OpenAPI 3.1

    # Check for nested structures only if needed
    has_nested = False
    if not (has_ref or has_extra or has_file or has_nullable):
        has_nested = any(isinstance(v, (dict, list)) for v in schema.values())

    # If no special handling needed, return schema as is
    if not (has_ref or has_extra or has_nested or has_file or has_nullable):
        return schema.copy()

    # Process schema with special handling
    result = {}
    for key, value in schema.items():
        if key == "$ref" and isinstance(value, str) and ("#/$defs/" in value or "#/definitions/" in value):
            # Replace $defs or definitions with components/schemas
            model_name = value.split("/")[-1]
            result[key] = f"#/components/schemas/{model_name}"
        elif key == "json_schema_extra" and isinstance(value, dict):
            # Apply json_schema_extra attributes directly to the schema
            for extra_key, extra_value in value.items():
                if extra_key != "multipart/form-data":  # Skip this key, it's handled elsewhere
                    result[extra_key] = extra_value  # noqa: PERF403
        elif key == "nullable" and is_openapi_31:
            # In OpenAPI 3.1, convert nullable to type array with null
            if value is True and "type" in result:
                if isinstance(result["type"], list):
                    if "null" not in result["type"]:
                        result["type"].append("null")
                else:
                    result["type"] = [result["type"], "null"]
            else:
                # Keep nullable for OpenAPI 3.0 compatibility
                result[key] = value
        elif isinstance(value, dict):
            result[key] = _fix_references(value)
        elif isinstance(value, list) and any(isinstance(item, dict) for item in value):
            # Process lists containing dictionaries
            result[key] = [_fix_references(item) if isinstance(item, dict) else item for item in value]
        else:
            # Copy lists or use value directly for other types
            result[key] = value.copy() if isinstance(value, list) and hasattr(value, "copy") else value

    # Ensure file fields have the correct format
    if has_file:
        result["type"] = "string"
        result["format"] = "binary"

    # Handle nullable for OpenAPI 3.1 if it wasn't already processed
    if has_nullable and "nullable" in schema and schema["nullable"] is True and "type" not in result:
        # If there's no type but there is nullable, add type: ["null"]
        result["type"] = ["null"]

    return result


def python_type_to_openapi_type(python_type: Any) -> dict[str, Any]:  # noqa: PLR0911
    """Convert a Python type to an OpenAPI type.

    Args:
        python_type: The Python type to convert

    Returns:
        The OpenAPI type definition

    """
    # Get OpenAPI configuration to check version
    from .config import get_openapi_config

    config = get_openapi_config()
    is_openapi_31 = config.openapi_version.startswith("3.1")

    # Fast lookup for common primitive types
    if python_type is str:
        return {"type": "string"}
    if python_type is int:
        return {"type": "integer"}
    if python_type is float:
        return {"type": "number"}
    if python_type is bool:
        return {"type": "boolean"}
    if python_type is None or python_type is type(None):
        return {"type": "null"} if is_openapi_31 else {"nullable": True}

    # Handle container types
    origin = getattr(python_type, "__origin__", None)
    if python_type is list or origin is list:
        # Handle List[X]
        args = getattr(python_type, "__args__", [])
        if args:
            item_type = python_type_to_openapi_type(args[0])
            return {"type": "array", "items": item_type}
        return {"type": "array"}
    if python_type is dict or origin is dict:
        # Handle Dict[X, Y]
        args = getattr(python_type, "__args__", [])
        if len(args) == 2 and is_openapi_31 and args[0] is str:  # noqa: PLR2004
            # In OpenAPI 3.1, we can specify additionalProperties more precisely
            value_type = python_type_to_openapi_type(args[1])
            return {"type": "object", "additionalProperties": value_type}
        return {"type": "object"}

    # Handle special types
    if python_type == UUID:
        return {"type": "string", "format": "uuid"}
    if python_type == datetime:
        return {"type": "string", "format": "date-time"}
    if python_type == date:
        return {"type": "string", "format": "date"}
    if python_type == time:
        return {"type": "string", "format": "time"}

    # Handle class types
    if inspect.isclass(python_type):
        if issubclass(python_type, Enum):
            # Handle Enum types
            return {"type": "string", "enum": [e.value for e in python_type]}
        if issubclass(python_type, BaseModel):
            # Handle Pydantic models
            return {"$ref": f"#/components/schemas/{python_type.__name__}"}

    # Handle Optional[X] types (Union[X, None])
    if origin is Union:
        args = getattr(python_type, "__args__", [])
        if len(args) == 2 and args[1] is type(None):  # noqa: PLR2004
            inner_type = python_type_to_openapi_type(args[0])
            if is_openapi_31:
                # In OpenAPI 3.1, use type array with null
                if "type" in inner_type:
                    if isinstance(inner_type["type"], list):
                        if "null" not in inner_type["type"]:
                            inner_type["type"].append("null")
                    else:
                        inner_type["type"] = [inner_type["type"], "null"]
                else:
                    # For references, we need to use oneOf with null
                    inner_type = {"oneOf": [inner_type, {"type": "null"}]}
            else:
                # In OpenAPI 3.0, use nullable: true
                inner_type["nullable"] = True
            return inner_type

        # Handle Union[X, Y, ...] for OpenAPI 3.1
        if is_openapi_31 and len(args) > 1:
            return {"oneOf": [python_type_to_openapi_type(arg) for arg in args]}

    # Default to string for unknown types
    return {"type": "string"}


def response_schema(
    model: type[BaseModel],
    description: str,
    status_code: int | str = 200,
) -> dict[str, Any]:
    """Generate an OpenAPI response schema for a Pydantic model.

    Args:
        model: The Pydantic model to use for the response schema
        description: Description of the response
        status_code: HTTP status code for the response (default: 200)

    Returns:
        An OpenAPI response schema

    """
    return {
        str(status_code): {
            "description": description,
            "content": {"application/json": {"schema": {"$ref": f"#/components/schemas/{model.__name__}"}}},
        },
    }


def error_response_schema(
    description: str,
    status_code: int | str = 400,
) -> dict[str, Any]:
    """Generate an OpenAPI error response schema.

    Args:
        description: Description of the error
        status_code: HTTP status code for the error (default: 400)

    Returns:
        An OpenAPI error response schema

    """
    return {
        str(status_code): {
            "description": description,
        },
    }


def success_response(
    model: type[BaseModel],
    description: str,
) -> tuple[type[BaseModel], str]:
    """Create a success response tuple for use with responses_schema.

    Args:
        model: The Pydantic model to use for the response schema
        description: Description of the response

    Returns:
        A tuple of (model, description) for use with responses_schema

    """
    return (model, description)


def responses_schema(
    success_responses: dict[int | str, tuple[type[BaseModel], str]],
    errors: dict[int | str, str] | None = None,
) -> dict[str, Any]:
    """Generate a complete OpenAPI responses schema with success and error responses.

    Args:
        success_responses: Dictionary of status codes and (model, description) tuples for success responses
        errors: Dictionary of error status codes and descriptions

    Returns:
        A complete OpenAPI responses schema

    """
    responses = {}

    # Add success responses
    for status_code, (model, description) in success_responses.items():
        responses.update(response_schema(model, description, status_code))

    # Add error responses
    if errors:
        for status_code, description in errors.items():
            responses.update(error_response_schema(description, status_code))

    return responses


# I18n string processing for OpenAPI schema generation


def process_i18n_value(value: Any, language: str) -> Any:
    """Process a value that might be an I18nString or contain I18nString values.

    Args:
        value: The value to process
        language: The language to use

    Returns:
        The processed value

    """
    from flask_x_openapi_schema.i18n.i18n_string import I18nStr

    # Fast path for non-container types that aren't I18nStr
    if not isinstance(value, (I18nStr, dict, list)):
        return value

    # Process based on type
    if isinstance(value, I18nStr):
        return value.get(language)
    if isinstance(value, dict):
        return process_i18n_dict(value, language)
    if isinstance(value, list):
        return [process_i18n_value(item, language) for item in value]
    return value


def process_i18n_dict(data: dict[str, Any], language: str) -> dict[str, Any]:
    """Process a dictionary that might contain I18nString values.

    Recursively processes all I18nString values in a dictionary.

    Args:
        data: The dictionary to process
        language: The language to use

    Returns:
        A new dictionary with I18nString values converted to strings

    """
    from flask_x_openapi_schema.i18n.i18n_string import I18nStr

    # Process dictionary
    result = {}
    for key, value in data.items():
        if isinstance(value, I18nStr):
            result[key] = value.get(language)
        elif isinstance(value, dict):
            result[key] = process_i18n_dict(value, language)
        elif isinstance(value, list):
            result[key] = [process_i18n_value(item, language) for item in value]
        else:
            result[key] = value

    return result


def clear_i18n_cache() -> None:
    """Clear the i18n processing cache."""
    # No-op in simplified cache system


def clear_references_cache() -> None:
    """Clear the references processing cache."""
    # No-op in simplified cache system
