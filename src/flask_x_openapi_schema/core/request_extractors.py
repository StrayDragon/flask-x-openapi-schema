"""Request data extraction utilities.

This module provides utilities for extracting data from different types of requests.
It implements the Strategy pattern for handling different request data formats.
"""

import functools
import json
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, TypeVar

from flask import Request
from pydantic import BaseModel

from flask_x_openapi_schema.core.logger import get_logger

# Type variable for the return type of the decorated function
T = TypeVar("T")

logger = get_logger(__name__)


def log_operation(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator for logging function calls and exceptions.

    Args:
        func: The function to decorate

    Returns:
        The decorated function

    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        logger = get_logger(func.__module__)
        logger.debug(f"Calling {func.__name__}")
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Error in {func.__name__}: {e}")
            raise

    return wrapper


def safe_operation(operation: Callable[[], T], fallback: Any = None, log_error: bool = True) -> T:
    """Safely execute an operation, returning a fallback value on error.

    Args:
        operation: The operation to execute
        fallback: The value to return if the operation fails
        log_error: Whether to log the error

    Returns:
        The result of the operation or the fallback value

    """
    try:
        return operation()
    except Exception as e:
        if log_error:
            logger = get_logger()
            logger.warning(f"Operation failed: {e}")
        return fallback() if callable(fallback) else fallback


class RequestDataExtractor(ABC):
    """Base class for request data extractors.

    This class defines the interface for extracting data from requests.
    Concrete implementations handle different request formats.
    """

    @abstractmethod
    def can_extract(self, request: Request) -> bool:
        """Check if this extractor can handle the given request.

        Args:
            request: The Flask request object

        Returns:
            True if this extractor can handle the request, False otherwise

        """

    @abstractmethod
    def extract(self, request: Request) -> dict[str, Any]:
        """Extract data from the request.

        Args:
            request: The Flask request object

        Returns:
            The extracted data as a dictionary

        """


class JsonRequestExtractor(RequestDataExtractor):
    """Extractor for JSON request data."""

    @log_operation
    def can_extract(self, request: Request) -> bool:
        """Check if this extractor can handle the given request.

        Args:
            request: The Flask request object

        Returns:
            True if the request has JSON data, False otherwise

        """
        return request.is_json

    @log_operation
    def extract(self, request: Request) -> dict[str, Any]:
        """Extract JSON data from the request.

        Args:
            request: The Flask request object

        Returns:
            The extracted JSON data as a dictionary

        """
        return request.get_json(silent=True) or {}


class FormRequestExtractor(RequestDataExtractor):
    """Extractor for form data requests."""

    @log_operation
    def can_extract(self, request: Request) -> bool:
        """Check if this extractor can handle the given request.

        Args:
            request: The Flask request object

        Returns:
            True if the request has form data, False otherwise

        """
        return bool(request.form or request.files)

    @log_operation
    def extract(self, request: Request) -> dict[str, Any]:
        """Extract form data from the request.

        Args:
            request: The Flask request object

        Returns:
            The extracted form data as a dictionary

        """
        data = dict(request.form.items())
        if request.files:
            for key, file in request.files.items():
                data[key] = file  # noqa: PERF403
        return data


class ContentTypeJsonExtractor(RequestDataExtractor):
    """Extractor for requests with JSON content type but not parsed as JSON."""

    @log_operation
    def can_extract(self, request: Request) -> bool:
        """Check if this extractor can handle the given request.

        Args:
            request: The Flask request object

        Returns:
            True if the request has JSON content type but is not parsed as JSON, False otherwise

        """
        return not request.is_json and request.content_type is not None and "json" in request.content_type.lower()

    @log_operation
    def extract(self, request: Request) -> dict[str, Any]:
        """Extract JSON data from the request body.

        Args:
            request: The Flask request object

        Returns:
            The extracted JSON data as a dictionary

        """
        raw_data = request.get_data(as_text=True)
        if raw_data:
            try:
                return json.loads(raw_data)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON data: {e}")
        return {}


class RawDataJsonExtractor(RequestDataExtractor):
    """Extractor for raw request data that might be JSON."""

    @log_operation
    def can_extract(self, request: Request) -> bool:  # noqa: ARG002
        """Check if this extractor can handle the given request.

        Args:
            request: The Flask request object

        Returns:
            True if the request has raw data, False otherwise

        """
        # This extractor is a fallback, so it can always try to extract
        return True

    @log_operation
    def extract(self, request: Request) -> dict[str, Any]:
        """Extract JSON data from the raw request data.

        Args:
            request: The Flask request object

        Returns:
            The extracted JSON data as a dictionary

        """
        raw_data = request.get_data(as_text=True)
        if raw_data:
            try:
                return json.loads(raw_data)
            except json.JSONDecodeError:
                pass
        return {}


class RequestJsonAttributeExtractor(RequestDataExtractor):
    """Extractor for request.json attribute (for test environments)."""

    @log_operation
    def can_extract(self, request: Request) -> bool:
        """Check if this extractor can handle the given request.

        Args:
            request: The Flask request object

        Returns:
            True if the request has a json attribute, False otherwise

        """
        return hasattr(request, "json") and request.json is not None

    @log_operation
    def extract(self, request: Request) -> dict[str, Any]:
        """Extract JSON data from the request.json attribute.

        Args:
            request: The Flask request object

        Returns:
            The extracted JSON data as a dictionary

        """
        return request.json or {}


class RequestCachedJsonExtractor(RequestDataExtractor):
    """Extractor for request._cached_json attribute (for pytest-flask)."""

    @log_operation
    def can_extract(self, request: Request) -> bool:
        """Check if this extractor can handle the given request.

        Args:
            request: The Flask request object

        Returns:
            True if the request has a _cached_json attribute, False otherwise

        """
        return hasattr(request, "_cached_json") and request._cached_json is not None  # noqa: SLF001

    @log_operation
    def extract(self, request: Request) -> dict[str, Any]:
        """Extract JSON data from the request._cached_json attribute.

        Args:
            request: The Flask request object

        Returns:
            The extracted JSON data as a dictionary

        """
        return request._cached_json or {}  # noqa: SLF001


class ModelFactory:
    """Factory for creating model instances from data."""

    @staticmethod
    @log_operation
    def create_from_data(model_class: type[BaseModel], data: dict[str, Any]) -> BaseModel:
        """Create a model instance from data.

        Args:
            model_class: The model class to instantiate
            data: The data to use for instantiation

        Returns:
            An instance of the model

        Raises:
            ValueError: If the model cannot be instantiated

        """
        # Try model_validate first (better handling of complex types)
        try:
            return model_class.model_validate(data)
        except Exception as e:
            logger.warning(f"Validation error using model_validate: {e}")

            # Try using the constructor with filtered data
            try:
                model_fields = model_class.model_fields
                filtered_data = {k: v for k, v in data.items() if k in model_fields}
                return model_class(**filtered_data)
            except Exception as e:
                logger.warning(f"Validation error using constructor: {e}")
                msg = f"Failed to create model instance: {e}"
                raise ValueError(msg) from e


class RequestProcessor:
    """Processor for extracting and validating request data."""

    def __init__(self) -> None:
        """Initialize the request processor with default extractors."""
        self.extractors: list[RequestDataExtractor] = [
            JsonRequestExtractor(),
            FormRequestExtractor(),
            ContentTypeJsonExtractor(),
            RequestJsonAttributeExtractor(),
            RequestCachedJsonExtractor(),
            RawDataJsonExtractor(),
        ]

    @log_operation
    def extract_data(self, request: Request) -> dict[str, Any]:
        """Extract data from the request using the first applicable extractor.

        Args:
            request: The Flask request object

        Returns:
            The extracted data as a dictionary

        """
        for extractor in self.extractors:
            if extractor.can_extract(request):
                try:
                    data = extractor.extract(request)
                    if data:
                        logger.debug(f"Extracted data using {extractor.__class__.__name__}")
                        return data
                except Exception as e:
                    logger.warning(f"Failed to extract data using {extractor.__class__.__name__}: {e}")
        return {}

    @log_operation
    def process_request_data(self, request: Request, model: type[BaseModel], param_name: str) -> BaseModel | None:
        """Process request data and create a model instance.

        Args:
            request: The Flask request object
            model: The model class to instantiate
            param_name: The parameter name (for logging)

        Returns:
            An instance of the model or None if processing fails

        """
        from flask_x_openapi_schema.core.request_processing import preprocess_request_data

        # Extract data from the request
        data = self.extract_data(request)
        if not data:
            logger.debug(f"No data extracted for {param_name}")
            return None

        # Preprocess the data
        processed_data = preprocess_request_data(data, model)
        logger.debug(f"Processed data for {param_name}: {processed_data}")

        # Create model instance
        try:
            model_instance = ModelFactory.create_from_data(model, processed_data)
            logger.debug(f"Created model instance for {param_name}")
        except Exception as e:
            logger.warning(f"Failed to create model instance for {param_name}: {e}")
            return None
        else:
            return model_instance


# Create a singleton instance for reuse
request_processor = RequestProcessor()
