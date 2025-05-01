"""Request data processing utilities.

This module provides utilities for processing request data before validation.
It handles conversion of string representations of complex data types (lists, dicts,
nested models) into their proper Python types to ensure Pydantic validation works correctly.
"""

import json
import logging
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger(__name__)


def preprocess_request_data(data: dict[str, Any], model: type[BaseModel]) -> dict[str, Any]:
    """Pre-process request data to handle list fields and other complex types correctly.

    This function examines the Pydantic model's field types and attempts to convert
    string representations of complex data types (like JSON strings) into their
    proper Python types. This is particularly useful for web forms and query parameters
    where complex types are often submitted as strings.

    Args:
        data: The request data to process as a dictionary
        model: The Pydantic model to use for type information

    Returns:
        dict: Processed data that can be validated by Pydantic

    Examples:
        >>> from pydantic import BaseModel
        >>> class UserModel(BaseModel):
        ...     name: str
        ...     tags: list[str]
        ...     metadata: dict[str, str]
        >>> data = {"name": "John", "tags": '["python", "flask"]', "metadata": '{"role": "admin", "department": "IT"}'}
        >>> result = preprocess_request_data(data, UserModel)
        >>> result["tags"]
        ['python', 'flask']
        >>> result["metadata"]
        {'role': 'admin', 'department': 'IT'}

    """
    if not hasattr(model, "model_fields"):
        return data

    result = {}

    for field_name, field_info in model.model_fields.items():
        if field_name not in data:
            continue

        field_value = data[field_name]
        field_type = field_info.annotation

        origin = getattr(field_type, "__origin__", None)

        if origin is list or origin is list:
            if isinstance(field_value, str) and field_value.startswith("[") and field_value.endswith("]"):
                try:
                    result[field_name] = json.loads(field_value)
                    logger.debug(f"Parsed string to list for field {field_name}: {result[field_name]}")
                    continue
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse string as JSON list for field {field_name}: {e}")

            if isinstance(field_value, list):
                result[field_name] = field_value
            else:
                try:
                    result[field_name] = [field_value]
                except Exception as e:
                    logger.warning(f"Failed to convert value to list for field {field_name}: {e}")

                    result[field_name] = field_value

        elif origin is dict or origin is dict:
            if isinstance(field_value, str) and field_value.startswith("{") and field_value.endswith("}"):
                try:
                    result[field_name] = json.loads(field_value)
                    logger.debug(f"Parsed string to dict for field {field_name}: {result[field_name]}")
                    continue
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse string as JSON dict for field {field_name}: {e}")

            if isinstance(field_value, dict):
                result[field_name] = field_value
            else:
                logger.warning(f"Non-dict value for dict field {field_name}: {field_value}")
                result[field_name] = field_value

        elif (
            isinstance(field_type, type)
            and issubclass(field_type, BaseModel)
            and isinstance(field_value, str)
            and field_value.startswith("{")
            and field_value.endswith("}")
        ):
            try:
                parsed_value = json.loads(field_value)
                if isinstance(parsed_value, dict):
                    result[field_name] = parsed_value
                    logger.debug(f"Parsed string to dict for nested model field {field_name}")
                    continue
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse string as JSON for nested model field {field_name}: {e}")

            result[field_name] = field_value
        else:
            result[field_name] = field_value

    for key, value in data.items():
        if key not in result:
            result[key] = value

    return result
