"""Utility functions for OpenAPI schema generation.

This module provides utility functions for converting Pydantic models to OpenAPI schemas,
handling references, and processing internationalized strings. It includes functions for:

* Converting Pydantic models to OpenAPI schemas
* Converting Python types to OpenAPI types
* Generating response schemas for API endpoints
* Processing internationalized strings in schemas
"""

import inspect
from datetime import date, datetime, time
from enum import Enum
from typing import Any, Union
from uuid import UUID

from pydantic import BaseModel


def pydantic_to_openapi_schema(model: type[BaseModel]) -> dict[str, Any]:
    """Convert a Pydantic model to an OpenAPI schema.

    Extracts schema information from a Pydantic model and converts it to a format
    compatible with OpenAPI specifications. The function handles property types,
    required fields, and includes the model's docstring as the schema description.

    Args:
        model: The Pydantic model class to convert to an OpenAPI schema

    Returns:
        dict: The OpenAPI schema representation of the model

    Examples:
        >>> from pydantic import BaseModel, Field
        >>> class User(BaseModel):
        ...     '''A user model.'''
        ...
        ...     name: str = Field(..., description="The user's name")
        ...     age: int = Field(..., description="The user's age")
        >>> schema = pydantic_to_openapi_schema(User)
        >>> schema["type"]
        'object'
        >>> "name" in schema["properties"]
        True
        >>> "age" in schema["properties"]
        True
        >>> schema["description"]
        'A user model.'

    """
    schema: dict[str, Any] = {"type": "object", "properties": {}, "required": []}

    model_schema = model.model_json_schema()

    if "properties" in model_schema:
        properties = {}
        for prop_name, prop_schema in model_schema["properties"].items():
            properties[prop_name] = _fix_references(prop_schema)
        schema["properties"] = properties

    if "required" in model_schema:
        schema["required"] = model_schema["required"]

    if model.__doc__:
        schema["description"] = model.__doc__.strip()

    return schema


def _fix_references(schema: dict[str, Any]) -> dict[str, Any]:
    """Fix references in a schema to use components/schemas instead of $defs.

    Converts Pydantic's internal reference format to OpenAPI standard format and
    applies any json_schema_extra attributes to the schema. Also handles nullable
    fields according to the OpenAPI version being used.

    Args:
        schema: The schema dictionary to fix references in

    Returns:
        dict: The schema with fixed references

    """
    from .config import get_openapi_config

    config = get_openapi_config()
    is_openapi_31 = config.openapi_version.startswith("3.1")

    if not isinstance(schema, dict):
        return schema

    has_ref = (
        "$ref" in schema
        and isinstance(schema["$ref"], str)
        and ("#/$defs/" in schema["$ref"] or "#/definitions/" in schema["$ref"])
    )
    has_extra = "json_schema_extra" in schema
    has_file = "type" in schema and schema["type"] == "string" and "format" in schema and schema["format"] == "binary"
    has_nullable = "nullable" in schema and is_openapi_31

    has_nested = False
    if not (has_ref or has_extra or has_file or has_nullable):
        has_nested = any(isinstance(v, (dict, list)) for v in schema.values())

    if not (has_ref or has_extra or has_nested or has_file or has_nullable):
        return schema.copy()

    result = {}
    for key, value in schema.items():
        if key == "$ref" and isinstance(value, str) and ("#/$defs/" in value or "#/definitions/" in value):
            model_name = value.split("/")[-1]
            result[key] = f"#/components/schemas/{model_name}"
        elif key == "json_schema_extra" and isinstance(value, dict):
            for extra_key, extra_value in value.items():
                if extra_key != "multipart/form-data":
                    result[extra_key] = extra_value  # noqa: PERF403
        elif key == "nullable" and is_openapi_31:
            if value is True and "type" in result:
                if isinstance(result["type"], list):
                    if "null" not in result["type"]:
                        result["type"].append("null")
                else:
                    result["type"] = [result["type"], "null"]
            else:
                result[key] = value
        elif isinstance(value, dict):
            result[key] = _fix_references(value)
        elif isinstance(value, list) and any(isinstance(item, dict) for item in value):
            result[key] = [_fix_references(item) if isinstance(item, dict) else item for item in value]
        else:
            result[key] = value.copy() if isinstance(value, list) and hasattr(value, "copy") else value

    if has_file:
        result["type"] = "string"
        result["format"] = "binary"

    if has_nullable and "nullable" in schema and schema["nullable"] is True and "type" not in result:
        result["type"] = ["null"]

    return result


def python_type_to_openapi_type(python_type: Any) -> dict[str, Any]:
    """Convert a Python type to an OpenAPI type.

    Maps Python types to their corresponding OpenAPI type definitions. Handles
    basic types, container types (lists, dicts), and special types like UUID
    and datetime. Also supports Union types and Pydantic models.

    Args:
        python_type: The Python type to convert to an OpenAPI type

    Returns:
        dict: The OpenAPI type definition for the given Python type

    Examples:
        >>> python_type_to_openapi_type(str)
        {'type': 'string'}
        >>> python_type_to_openapi_type(int)
        {'type': 'integer'}
        >>> python_type_to_openapi_type(list[str])["type"]
        'array'

    """
    from .config import get_openapi_config

    config = get_openapi_config()
    is_openapi_31 = config.openapi_version.startswith("3.1")

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

    origin = getattr(python_type, "__origin__", None)
    if python_type is list or origin is list:
        args = getattr(python_type, "__args__", [])
        if args:
            item_type = python_type_to_openapi_type(args[0])
            return {"type": "array", "items": item_type}
        return {"type": "array"}
    if python_type is dict or origin is dict:
        args = getattr(python_type, "__args__", [])
        if len(args) == 2 and is_openapi_31 and args[0] is str:  # noqa: PLR2004
            value_type = python_type_to_openapi_type(args[1])
            return {"type": "object", "additionalProperties": value_type}
        return {"type": "object"}

    if python_type == UUID:
        return {"type": "string", "format": "uuid"}
    if python_type == datetime:
        return {"type": "string", "format": "date-time"}
    if python_type == date:
        return {"type": "string", "format": "date"}
    if python_type == time:
        return {"type": "string", "format": "time"}

    if inspect.isclass(python_type):
        if issubclass(python_type, Enum):
            return {"type": "string", "enum": [e.value for e in python_type]}
        if issubclass(python_type, BaseModel):
            return {"$ref": f"#/components/schemas/{python_type.__name__}"}

    if origin is Union:
        args = getattr(python_type, "__args__", [])
        if len(args) == 2 and args[1] is type(None):  # noqa: PLR2004
            inner_type = python_type_to_openapi_type(args[0])
            if is_openapi_31:
                if "type" in inner_type:
                    if isinstance(inner_type["type"], list):
                        if "null" not in inner_type["type"]:
                            inner_type["type"].append("null")
                    else:
                        inner_type["type"] = [inner_type["type"], "null"]
                else:
                    inner_type = {"oneOf": [inner_type, {"type": "null"}]}
            else:
                inner_type["nullable"] = True
            return inner_type

        if is_openapi_31 and len(args) > 1:
            return {"oneOf": [python_type_to_openapi_type(arg) for arg in args]}

    return {"type": "string"}


def response_schema(
    model: type[BaseModel],
    description: str,
    status_code: int | str = 200,
) -> dict[str, Any]:
    """Generate an OpenAPI response schema for a Pydantic model.

    Creates an OpenAPI response object that references a Pydantic model schema.
    The response includes a description and specifies that the content type is
    application/json.

    Args:
        model: The Pydantic model to use for the response schema
        description: Description of the response
        status_code: HTTP status code for the response (default: 200)

    Returns:
        dict: An OpenAPI response schema object

    Examples:
        >>> from pydantic import BaseModel
        >>> class User(BaseModel):
        ...     name: str
        ...     age: int
        >>> schema = response_schema(User, "A user object", 200)
        >>> schema["200"]["description"]
        'A user object'
        >>> schema["200"]["content"]["application/json"]["schema"]["$ref"]
        '#/components/schemas/User'

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

    Creates a simple OpenAPI error response object with a description.
    Unlike success responses, error responses don't include content schema.

    Args:
        description: Description of the error
        status_code: HTTP status code for the error (default: 400)

    Returns:
        dict: An OpenAPI error response schema object

    Examples:
        >>> schema = error_response_schema("Bad Request", 400)
        >>> schema["400"]["description"]
        'Bad Request'

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

    Helper function that creates a tuple containing a model and description,
    which can be used with the responses_schema function to generate complete
    OpenAPI response schemas.

    Args:
        model: The Pydantic model to use for the response schema
        description: Description of the response

    Returns:
        tuple: A tuple of (model, description) for use with responses_schema

    Examples:
        >>> from pydantic import BaseModel
        >>> class User(BaseModel):
        ...     name: str
        >>> response = success_response(User, "A user object")
        >>> response[0] == User
        True
        >>> response[1]
        'A user object'

    """
    return (model, description)


def responses_schema(
    success_responses: dict[int | str, tuple[type[BaseModel], str]],
    errors: dict[int | str, str] | None = None,
) -> dict[str, Any]:
    """Generate a complete OpenAPI responses schema with success and error responses.

    Creates a comprehensive OpenAPI responses object that includes both success
    responses (with schemas) and error responses. This is useful for documenting
    all possible responses from an API endpoint.

    Args:
        success_responses: Dictionary mapping status codes to (model, description)
            tuples for success responses
        errors: Optional dictionary mapping status codes to descriptions for error
            responses

    Returns:
        dict: A complete OpenAPI responses schema object

    Examples:
        >>> from pydantic import BaseModel
        >>> class User(BaseModel):
        ...     name: str
        >>> class Error(BaseModel):
        ...     message: str
        >>> success = {200: success_response(User, "Success")}
        >>> errors = {400: "Bad Request", 404: "Not Found"}
        >>> schema = responses_schema(success, errors)
        >>> "200" in schema and "400" in schema and "404" in schema
        True

    """
    responses = {}

    for status_code, (model, description) in success_responses.items():
        responses.update(response_schema(model, description, status_code))

    if errors:
        for status_code, description in errors.items():
            responses.update(error_response_schema(description, status_code))

    return responses


def process_i18n_value(value: Any, language: str) -> Any:
    """Process a value that might be an I18nString or contain I18nString values.

    Recursively processes values that might be I18nString instances or contain
    I18nString instances (in lists or dictionaries). For I18nString instances,
    returns the string for the specified language.

    Args:
        value: The value to process, which might be an I18nString or contain I18nString values
        language: The language code to use for extracting localized strings

    Returns:
        Any: The processed value with I18nString instances replaced by their
            language-specific strings

    Examples:
        >>> from flask_x_openapi_schema.i18n.i18n_string import I18nStr
        >>> i18n_str = I18nStr({"en": "Hello", "fr": "Bonjour"})
        >>> process_i18n_value(i18n_str, "en")
        'Hello'
        >>> process_i18n_value(i18n_str, "fr")
        'Bonjour'
        >>> process_i18n_value({"greeting": i18n_str}, "en")
        {'greeting': 'Hello'}

    """
    from flask_x_openapi_schema.i18n.i18n_string import I18nStr

    if not isinstance(value, (I18nStr, dict, list)):
        return value

    if isinstance(value, I18nStr):
        return value.get(language)
    if isinstance(value, dict):
        return process_i18n_dict(value, language)
    if isinstance(value, list):
        return [process_i18n_value(item, language) for item in value]
    return value


def process_i18n_dict(data: dict[str, Any], language: str) -> dict[str, Any]:
    """Process a dictionary that might contain I18nString values.

    Recursively processes all I18nString values in a dictionary, converting them
    to language-specific strings. Also handles nested dictionaries and lists that
    might contain I18nString values.

    Args:
        data: The dictionary to process, which might contain I18nString values
        language: The language code to use for extracting localized strings

    Returns:
        dict: A new dictionary with I18nString values converted to language-specific strings

    Examples:
        >>> from flask_x_openapi_schema.i18n.i18n_string import I18nStr
        >>> data = {
        ...     "title": I18nStr({"en": "Hello", "fr": "Bonjour"}),
        ...     "nested": {"subtitle": I18nStr({"en": "World", "fr": "Monde"})},
        ... }
        >>> result = process_i18n_dict(data, "en")
        >>> result["title"]
        'Hello'
        >>> result["nested"]["subtitle"]
        'World'

    """
    from flask_x_openapi_schema.i18n.i18n_string import I18nStr

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
    """Clear the i18n processing cache.

    Clears any cached results from I18n string processing functions.
    Call this function when you need to ensure that I18n strings are
    re-processed, such as after changing the language configuration.
    """


def clear_references_cache() -> None:
    """Clear the references processing cache.

    Clears any cached results from schema reference processing functions.
    Call this function when you need to ensure that schema references are
    re-processed, such as after modifying schema definitions.
    """
