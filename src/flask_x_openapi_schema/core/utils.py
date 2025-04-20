"""
Utility functions for OpenAPI schema generation.
"""

import inspect
from datetime import date, datetime, time
from enum import Enum
from functools import lru_cache
from typing import Any, Dict, Optional, Union
from uuid import UUID

from pydantic import BaseModel

from .cache import MODEL_SCHEMA_CACHE


def pydantic_to_openapi_schema(model: type[BaseModel]) -> dict[str, Any]:
    """
    Convert a Pydantic model to an OpenAPI schema.

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

    schema: dict[str, Any] = {"type": "object", "properties": {}, "required": []}

    # Get model schema from Pydantic
    model_schema = model.model_json_schema()

    # Extract properties and required fields
    if "properties" in model_schema:
        schema["properties"] = model_schema["properties"]

    if "required" in model_schema:
        schema["required"] = model_schema["required"]

    # Add description if available
    if model.__doc__:
        schema["description"] = model.__doc__.strip()

    # Cache the schema
    MODEL_SCHEMA_CACHE.set(model_key, schema)

    return schema


@lru_cache(maxsize=128)
def python_type_to_openapi_type(python_type: Any) -> dict[str, Any]:
    """
    Convert a Python type to an OpenAPI type.

    Args:
        python_type: The Python type to convert

    Returns:
        The OpenAPI type definition
    """
    # Handle primitive types
    if python_type is str:
        return {"type": "string"}
    elif python_type is int:
        return {"type": "integer"}
    elif python_type is float:
        return {"type": "number"}
    elif python_type is bool:
        return {"type": "boolean"}
    elif python_type is list or getattr(python_type, "__origin__", None) is list:
        # Handle List[X]
        args = getattr(python_type, "__args__", [])
        if args:
            item_type = python_type_to_openapi_type(args[0])
            return {"type": "array", "items": item_type}
        return {"type": "array"}
    elif python_type is dict or getattr(python_type, "__origin__", None) is dict:
        # Handle Dict[X, Y]
        return {"type": "object"}
    elif python_type == UUID:
        return {"type": "string", "format": "uuid"}
    elif python_type == datetime:
        return {"type": "string", "format": "date-time"}
    elif python_type == date:
        return {"type": "string", "format": "date"}
    elif python_type == time:
        return {"type": "string", "format": "time"}
    elif inspect.isclass(python_type) and issubclass(python_type, Enum):
        # Handle Enum types
        return {"type": "string", "enum": [e.value for e in python_type]}
    elif inspect.isclass(python_type) and issubclass(python_type, BaseModel):
        # Handle Pydantic models
        return {"$ref": f"#/components/schemas/{python_type.__name__}"}

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


def process_i18n_value(value: Any, language: str) -> Any:
    """
    Process a value that might be an I18nString or contain I18nString values.

    Args:
        value: The value to process
        language: The language to use

    Returns:
        The processed value
    """
    from ..i18n.i18n_string import I18nStr

    if isinstance(value, I18nStr):
        return value.get(language)
    elif isinstance(value, dict):
        return process_i18n_dict(value, language)
    elif isinstance(value, list):
        return [process_i18n_value(item, language) for item in value]
    else:
        return value


def process_i18n_dict(data: Dict[str, Any], language: str) -> Dict[str, Any]:
    """
    Process a dictionary that might contain I18nString values.

    Args:
        data: The dictionary to process
        language: The language to use

    Returns:
        A new dictionary with I18nString values converted to strings
    """
    from ..i18n.i18n_string import I18nStr

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
