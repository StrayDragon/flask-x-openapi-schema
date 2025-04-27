"""Request data processing utilities.

This module provides utilities for processing request data before validation.
"""

import json
import logging
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger(__name__)


def preprocess_request_data(data: dict[str, Any], model: type[BaseModel]) -> dict[str, Any]:  # noqa: PLR0915
    """Pre-process request data to handle list fields and other complex types correctly.

    Args:
        data: The request data to process
        model: The Pydantic model to use for type information

    Returns:
        Processed data that can be validated by Pydantic

    """
    if not hasattr(model, "model_fields"):
        return data

    result = {}

    # Process each field based on its type annotation
    for field_name, field_info in model.model_fields.items():
        if field_name not in data:
            continue

        field_value = data[field_name]
        field_type = field_info.annotation

        # Get the origin type (for generics like List, Dict)
        origin = getattr(field_type, "__origin__", None)

        # Handle list fields
        if origin is list or origin is list:
            # If the value is a string that looks like a JSON array, parse it
            if isinstance(field_value, str) and field_value.startswith("[") and field_value.endswith("]"):
                try:
                    result[field_name] = json.loads(field_value)
                    logger.debug(f"Parsed string to list for field {field_name}: {result[field_name]}")
                    continue
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse string as JSON list for field {field_name}: {e}")

            # If it's already a list, use it as is
            if isinstance(field_value, list):
                result[field_name] = field_value
            else:
                # Try to convert to a list if possible
                try:
                    result[field_name] = [field_value]
                except Exception as e:
                    logger.warning(f"Failed to convert value to list for field {field_name}: {e}")
                    # If conversion fails, keep the original value
                    result[field_name] = field_value

        # Handle dictionary fields
        elif origin is dict or origin is dict:
            # If the value is a string that looks like a JSON object, parse it
            if isinstance(field_value, str) and field_value.startswith("{") and field_value.endswith("}"):
                try:
                    result[field_name] = json.loads(field_value)
                    logger.debug(f"Parsed string to dict for field {field_name}: {result[field_name]}")
                    continue
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse string as JSON dict for field {field_name}: {e}")

            # If it's already a dict, use it as is
            if isinstance(field_value, dict):
                result[field_name] = field_value
            else:
                # For non-dict values, keep the original (will likely fail validation)
                logger.warning(f"Non-dict value for dict field {field_name}: {field_value}")
                result[field_name] = field_value

        # Handle nested model fields
        elif (
            isinstance(field_type, type)
            and issubclass(field_type, BaseModel)
            and isinstance(field_value, str)
            and field_value.startswith("{")
            and field_value.endswith("}")
        ):
            # If the value is a string that looks like a JSON object, parse it
            try:
                parsed_value = json.loads(field_value)
                if isinstance(parsed_value, dict):
                    result[field_name] = parsed_value
                    logger.debug(f"Parsed string to dict for nested model field {field_name}")
                    continue
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse string as JSON for nested model field {field_name}: {e}")

            # If parsing fails, keep the original value
            result[field_name] = field_value
        else:
            # For other fields, keep the original value
            result[field_name] = field_value

    # Add any fields from the original data that weren't processed
    for key, value in data.items():
        if key not in result:
            result[key] = value

    return result
