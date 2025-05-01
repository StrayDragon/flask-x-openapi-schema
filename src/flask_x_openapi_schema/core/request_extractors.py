"""Request data extraction utilities.

This module provides utilities for extracting data from different types of requests.
It implements the Strategy pattern for handling different request data formats.

Examples:
    Basic usage with Flask request (in a Flask route handler):

    ```python
    from flask import request
    from flask_x_openapi_schema.core.request_extractors import request_processor
    from pydantic import BaseModel


    class UserModel(BaseModel):
        name: str
        age: int


    # In a Flask route handler
    user = request_processor.process_request_data(request, UserModel, "user")
    ```

"""

import functools
import json
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, TypeVar

from flask import Request
from pydantic import BaseModel

from flask_x_openapi_schema.core.logger import get_logger

T = TypeVar("T")

logger = get_logger(__name__)


def log_operation(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator for logging function calls and exceptions.

    This decorator logs when a function is called and any exceptions that occur
    during execution.

    Args:
        func: The function to decorate.

    Returns:
        The decorated function that logs its calls and exceptions.

    Examples:
        ```python
        @log_operation
        def example_function(x):
            return x * 2


        result = example_function(5)  # result will be 10
        ```

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

    This function executes the provided operation and returns its result. If the
    operation raises an exception, it returns the fallback value instead.

    Args:
        operation: The operation to execute.
        fallback: The value to return if the operation fails. If callable, it will be called.
        log_error: Whether to log the error. Defaults to True.

    Returns:
        The result of the operation or the fallback value.

    Examples:
        ```python
        def risky_operation():
            return 1 / 0  # Will raise ZeroDivisionError


        result1 = safe_operation(risky_operation, fallback=0)  # result1 will be 0
        result2 = safe_operation(lambda: 42, fallback=0)  # result2 will be 42
        ```

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
    Concrete implementations handle different request formats such as JSON,
    form data, or raw request data.

    Attributes:
        None

    Examples:
        ```python
        class CustomExtractor(RequestDataExtractor):
            def can_extract(self, request):
                return True

            def extract(self, request):
                return {"custom_data": "value"}
        ```

    """

    @abstractmethod
    def can_extract(self, request: Request) -> bool:
        """Check if this extractor can handle the given request.

        This method determines if the extractor is capable of processing
        the provided request based on its format or content.

        Args:
            request: The Flask request object to check.

        Returns:
            bool: True if this extractor can handle the request, False otherwise.

        """

    @abstractmethod
    def extract(self, request: Request) -> dict[str, Any]:
        """Extract data from the request.

        This method extracts and processes data from the request object,
        converting it to a dictionary format for further processing.

        Args:
            request: The Flask request object to extract data from.

        Returns:
            dict[str, Any]: The extracted data as a dictionary.

        """


class JsonRequestExtractor(RequestDataExtractor):
    """Extractor for JSON request data.

    This extractor handles requests with JSON content type that have been
    properly parsed by Flask's request parser.

    Examples:
        ```python
        extractor = JsonRequestExtractor()
        # Assuming request.is_json is True
        if extractor.can_extract(request):
            data = extractor.extract(request)  # {'key': 'value'}
        ```

    """

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
    """Extractor for form data requests.

    This extractor handles requests with form data, including multipart/form-data
    with file uploads. It combines both form fields and files into a single dictionary.

    Examples:
        ```python
        extractor = FormRequestExtractor()
        # Assuming request.form contains data
        if extractor.can_extract(request):
            data = extractor.extract(request)  # {'name': 'John', 'file': <FileStorage object>}
        ```

    """

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
    """Extractor for requests with JSON content type but not parsed as JSON.

    This extractor handles requests that have a JSON content type header but
    where Flask's automatic JSON parsing has not been applied. It manually
    parses the raw request data as JSON.

    Examples:
        ```python
        extractor = ContentTypeJsonExtractor()
        # Assuming request has content_type with 'json' but not parsed
        if extractor.can_extract(request):
            data = extractor.extract(request)  # {'key': 'value'}
        ```

    """

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
    """Extractor for raw request data that might be JSON.

    This extractor is a fallback that attempts to parse any request's raw data
    as JSON. It always returns True for can_extract, making it suitable as a
    last resort in the extractor chain.

    Examples:
        ```python
        extractor = RawDataJsonExtractor()
        # This extractor always returns True
        if extractor.can_extract(request):
            # If request data contains valid JSON
            data = extractor.extract(request)  # {'key': 'value'}

            # If request data is not valid JSON
            data = extractor.extract(request_with_invalid_json)  # {}
        ```

    """

    @log_operation
    def can_extract(self, request: Request) -> bool:  # noqa: ARG002
        """Check if this extractor can handle the given request.

        This extractor always returns True as it's designed to be a fallback
        that attempts to handle any request.

        Args:
            request: The Flask request object (not used).

        Returns:
            bool: Always returns True.

        """
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
    """Extractor for request.json attribute (for test environments).

    This extractor is designed for test environments where the request object
    might have a direct json attribute. It checks for the presence of this
    attribute and extracts data from it.

    Examples:
        ```python
        extractor = RequestJsonAttributeExtractor()
        # Assuming request has a json attribute
        if extractor.can_extract(request_with_json_attr):
            data = extractor.extract(request_with_json_attr)  # {'key': 'value'}
        ```

    """

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
    """Extractor for request._cached_json attribute (for pytest-flask).

    This extractor is specifically designed for pytest-flask environments,
    where the request object might have a _cached_json attribute. It checks
    for the presence of this attribute and extracts data from it.

    Examples:
        ```python
        extractor = RequestCachedJsonExtractor()
        # Assuming request has a _cached_json attribute (pytest-flask)
        if extractor.can_extract(pytest_flask_request):
            data = extractor.extract(pytest_flask_request)  # {'key': 'value'}
        ```

    """

    @log_operation
    def can_extract(self, request: Request) -> bool:
        """Check if this extractor can handle the given request.

        Args:
            request: The Flask request object

        Returns:
            True if the request has a _cached_json attribute, False otherwise

        """
        return hasattr(request, "_cached_json") and request._cached_json is not None

    @log_operation
    def extract(self, request: Request) -> dict[str, Any]:
        """Extract JSON data from the request._cached_json attribute.

        Args:
            request: The Flask request object

        Returns:
            The extracted JSON data as a dictionary

        """
        return request._cached_json or {}


class ModelFactory:
    """Factory for creating model instances from data.

    This class provides static methods for creating Pydantic model instances
    from dictionary data. It handles validation errors and provides fallback
    mechanisms for model creation.

    Examples:
        ```python
        from pydantic import BaseModel


        class User(BaseModel):
            name: str
            age: int


        data = {"name": "John", "age": 30}
        user = ModelFactory.create_from_data(User, data)
        # user.name will be 'John'
        ```

    """

    @staticmethod
    @log_operation
    def create_from_data(model_class: type[BaseModel], data: dict[str, Any]) -> BaseModel:
        """Create a model instance from data.

        This method attempts to create a Pydantic model instance from dictionary data.
        It first tries using model_validate, and if that fails, it falls back to
        filtering the data to only include fields defined in the model and using
        the constructor.

        Args:
            model_class: The model class to instantiate.
            data: The data to use for instantiation.

        Returns:
            BaseModel: An instance of the specified model class.

        Raises:
            ValueError: If the model cannot be instantiated using either method.

        Examples:
            ```python
            from pydantic import BaseModel


            class User(BaseModel):
                name: str
                age: int


            data = {"name": "John", "age": 30, "extra": "ignored"}
            user = ModelFactory.create_from_data(User, data)
            # user.model_dump() will be {'name': 'John', 'age': 30}
            ```

        """
        try:
            return model_class.model_validate(data)
        except Exception as e:
            logger.warning(f"Validation error using model_validate: {e}")

            try:
                model_fields = model_class.model_fields
                filtered_data = {k: v for k, v in data.items() if k in model_fields}
                return model_class(**filtered_data)
            except Exception as e:
                logger.warning(f"Validation error using constructor: {e}")
                msg = f"Failed to create model instance: {e}"
                raise ValueError(msg) from e


class RequestProcessor:
    """Processor for extracting and validating request data.

    This class orchestrates the extraction of data from Flask requests using
    a chain of extractors. It tries each extractor in sequence until one
    successfully extracts data, then processes that data to create model instances.

    Attributes:
        extractors: A list of RequestDataExtractor instances to try in sequence.

    Examples:
        ```python
        from flask import request
        from pydantic import BaseModel


        class User(BaseModel):
            name: str
            age: int


        processor = RequestProcessor()
        user = processor.process_request_data(request, User, "user")
        if user:
            print(f"User: {user.name}, Age: {user.age}")
        ```

    """

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

        This method tries each extractor in the chain until one successfully
        extracts data from the request. It returns the first non-empty result.

        Args:
            request: The Flask request object to extract data from.

        Returns:
            dict[str, Any]: The extracted data as a dictionary. Returns an empty
            dictionary if no extractor could extract data.

        Examples:
            ```python
            processor = RequestProcessor()
            data = processor.extract_data(request)
            if data:
                print(f"Extracted data: {data}")
            ```

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

        This method extracts data from the request, preprocesses it according to
        the model's requirements, and then creates a model instance. It handles
        the entire pipeline from raw request to validated model instance.

        Args:
            request: The Flask request object containing the data.
            model: The Pydantic model class to instantiate.
            param_name: The parameter name (for logging and error messages).

        Returns:
            BaseModel | None: An instance of the specified model if successful,
            or None if data extraction or model creation fails.

        Examples:
            ```python
            from flask import request
            from pydantic import BaseModel


            class User(BaseModel):
                name: str
                age: int


            processor = RequestProcessor()
            user = processor.process_request_data(request, User, "user")
            if user:
                print(f"Processed user: {user.name}")
            ```

        """
        from flask_x_openapi_schema.core.request_processing import preprocess_request_data

        data = self.extract_data(request)
        if not data:
            logger.debug(f"No data extracted for {param_name}")
            return None

        processed_data = preprocess_request_data(data, model)
        logger.debug(f"Processed data for {param_name}: {processed_data}")

        try:
            model_instance = ModelFactory.create_from_data(model, processed_data)
            logger.debug(f"Created model instance for {param_name}")
        except Exception as e:
            logger.warning(f"Failed to create model instance for {param_name}: {e}")
            return None
        else:
            return model_instance


request_processor = RequestProcessor()
