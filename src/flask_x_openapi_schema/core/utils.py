"""
Utility functions for OpenAPI schema generation.

This module provides utility functions for converting Pydantic models to OpenAPI schemas,
handling references, and processing internationalized strings.
"""

import inspect
from datetime import date, datetime, time
from enum import Enum
from functools import lru_cache
from typing import Any, Dict, Optional, Tuple, Type, Union
from uuid import UUID

from pydantic import BaseModel

from .cache import MODEL_SCHEMA_CACHE, make_cache_key


@lru_cache(maxsize=256)
def pydantic_to_openapi_schema(model: Type[BaseModel]) -> Dict[str, Any]:
    """
    Convert a Pydantic model to an OpenAPI schema.
    This function is cached to improve performance for frequently used models.

    Args:
        model: The Pydantic model to convert

    Returns:
        The OpenAPI schema for the model
    """
    # Check if schema is already in cache
    model_key = f"{model.__module__}.{model.__name__}"
    cached_schema = MODEL_SCHEMA_CACHE.get(model_key)
    if cached_schema is not None:
        return cached_schema

    # Initialize schema with default values
    schema: Dict[str, Any] = {"type": "object", "properties": {}, "required": []}

    try:
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

        # Cache the schema
        MODEL_SCHEMA_CACHE.set(model_key, schema)
    except Exception as e:
        # Log error but continue with default schema
        print(f"Error generating schema for {model.__name__}: {e}")

    return schema


def _fix_references(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fix references in a schema to use components/schemas instead of $defs.
    Also applies any json_schema_extra attributes to the schema.

    Args:
        schema: The schema to fix

    Returns:
        The fixed schema
    """
    # Handle non-dict inputs
    if not isinstance(schema, dict):
        return schema

    # Fast path for schemas without references or special handling
    has_ref = (
        "$ref" in schema
        and isinstance(schema["$ref"], str)
        and "#/$defs/" in schema["$ref"]
    )
    has_extra = "json_schema_extra" in schema
    has_file = (
        "type" in schema
        and schema["type"] == "string"
        and "format" in schema
        and schema["format"] == "binary"
    )

    # Check for nested structures only if needed
    has_nested = False
    if not (has_ref or has_extra or has_file):
        has_nested = any(isinstance(v, (dict, list)) for v in schema.values())

    # If no special handling needed, return schema as is
    if not (has_ref or has_extra or has_nested or has_file):
        return schema.copy()

    # Process schema with special handling
    result = {}
    for key, value in schema.items():
        if key == "$ref" and isinstance(value, str) and "#/$defs/" in value:
            # Replace $defs with components/schemas
            model_name = value.split("/")[-1]
            result[key] = f"#/components/schemas/{model_name}"
        elif key == "json_schema_extra" and isinstance(value, dict):
            # Apply json_schema_extra attributes directly to the schema
            for extra_key, extra_value in value.items():
                if (
                    extra_key != "multipart/form-data"
                ):  # Skip this key, it's handled elsewhere
                    result[extra_key] = extra_value
        elif isinstance(value, dict):
            result[key] = _fix_references(value)
        elif isinstance(value, list) and any(isinstance(item, dict) for item in value):
            # Process lists containing dictionaries
            result[key] = [
                _fix_references(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            # Copy lists or use value directly for other types
            result[key] = (
                value.copy()
                if isinstance(value, list) and hasattr(value, "copy")
                else value
            )

    # Ensure file fields have the correct format
    if has_file:
        result["type"] = "string"
        result["format"] = "binary"

    return result


@lru_cache(maxsize=256)
def python_type_to_openapi_type(python_type: Any) -> Dict[str, Any]:
    """
    Convert a Python type to an OpenAPI type.
    This function is cached to improve performance for frequently used types.

    Args:
        python_type: The Python type to convert

    Returns:
        The OpenAPI type definition
    """
    # Fast lookup for common primitive types
    if python_type is str:
        return {"type": "string"}
    elif python_type is int:
        return {"type": "integer"}
    elif python_type is float:
        return {"type": "number"}
    elif python_type is bool:
        return {"type": "boolean"}
    elif python_type is None or python_type is type(None):
        return {"type": "null"}

    # Handle container types
    origin = getattr(python_type, "__origin__", None)
    if python_type is list or origin is list:
        # Handle List[X]
        args = getattr(python_type, "__args__", [])
        if args:
            item_type = python_type_to_openapi_type(args[0])
            return {"type": "array", "items": item_type}
        return {"type": "array"}
    elif python_type is dict or origin is dict:
        # Handle Dict[X, Y]
        return {"type": "object"}

    # Handle special types
    if python_type == UUID:
        return {"type": "string", "format": "uuid"}
    elif python_type == datetime:
        return {"type": "string", "format": "date-time"}
    elif python_type == date:
        return {"type": "string", "format": "date"}
    elif python_type == time:
        return {"type": "string", "format": "time"}

    # Handle class types
    if inspect.isclass(python_type):
        if issubclass(python_type, Enum):
            # Handle Enum types
            return {"type": "string", "enum": [e.value for e in python_type]}
        elif issubclass(python_type, BaseModel):
            # Handle Pydantic models
            return {"$ref": f"#/components/schemas/{python_type.__name__}"}

    # Handle Optional[X] types
    if origin is Union:
        args = getattr(python_type, "__args__", [])
        if len(args) == 2 and args[1] is type(None):
            # This is Optional[X]
            inner_type = python_type_to_openapi_type(args[0])
            inner_type["nullable"] = True
            return inner_type

    # Default to string for unknown types
    return {"type": "string"}


def response_schema(
    model: type[BaseModel],
    description: str,
    status_code: Union[int, str] = 200,
) -> dict[str, Any]:
    """
    Generate an OpenAPI response schema for a Pydantic model.

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
            "content": {
                "application/json": {
                    "schema": {"$ref": f"#/components/schemas/{model.__name__}"}
                }
            },
        }
    }


def error_response_schema(
    description: str,
    status_code: Union[int, str] = 400,
) -> dict[str, Any]:
    """
    Generate an OpenAPI error response schema.

    Args:
        description: Description of the error
        status_code: HTTP status code for the error (default: 400)

    Returns:
        An OpenAPI error response schema
    """
    return {
        str(status_code): {
            "description": description,
        }
    }


def success_response(
    model: type[BaseModel],
    description: str,
) -> tuple[type[BaseModel], str]:
    """
    Create a success response tuple for use with responses_schema.

    Args:
        model: The Pydantic model to use for the response schema
        description: Description of the response

    Returns:
        A tuple of (model, description) for use with responses_schema
    """
    return (model, description)


def responses_schema(
    success_responses: dict[Union[int, str], tuple[type[BaseModel], str]],
    errors: Optional[dict[Union[int, str], str]] = None,
) -> dict[str, Any]:
    """
    Generate a complete OpenAPI responses schema with success and error responses.

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


# Cache for i18n processing to avoid repeated conversions
_I18N_CACHE: Dict[Tuple, Any] = {}
MAX_I18N_CACHE_SIZE = 1000


def process_i18n_value(value: Any, language: str) -> Any:
    """
    Process a value that might be an I18nString or contain I18nString values.
    Uses caching to improve performance for repeated conversions.

    Args:
        value: The value to process
        language: The language to use

    Returns:
        The processed value
    """
    from ..i18n.i18n_string import I18nStr

    # Fast path for non-container types that aren't I18nStr
    if not isinstance(value, (I18nStr, dict, list)):
        return value

    # Try to use cached result
    cache_key = make_cache_key(id(value), language)
    if cache_key in _I18N_CACHE:
        return _I18N_CACHE[cache_key]

    # Process based on type
    result = None
    if isinstance(value, I18nStr):
        result = value.get(language)
    elif isinstance(value, dict):
        result = process_i18n_dict(value, language)
    elif isinstance(value, list):
        result = [process_i18n_value(item, language) for item in value]
    else:
        result = value

    # Cache the result if cache isn't too large
    if len(_I18N_CACHE) < MAX_I18N_CACHE_SIZE:
        _I18N_CACHE[cache_key] = result

    return result


def process_i18n_dict(data: Dict[str, Any], language: str) -> Dict[str, Any]:
    """
    Process a dictionary that might contain I18nString values.
    Uses caching to improve performance for repeated conversions.

    Args:
        data: The dictionary to process
        language: The language to use

    Returns:
        A new dictionary with I18nString values converted to strings
    """
    from ..i18n.i18n_string import I18nStr

    # Try to use cached result
    cache_key = make_cache_key(id(data), language)
    if cache_key in _I18N_CACHE:
        return _I18N_CACHE[cache_key]

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

    # Cache the result if cache isn't too large
    if len(_I18N_CACHE) < MAX_I18N_CACHE_SIZE:
        _I18N_CACHE[cache_key] = result

    return result


def clear_i18n_cache() -> None:
    """Clear the i18n processing cache."""
    _I18N_CACHE.clear()
