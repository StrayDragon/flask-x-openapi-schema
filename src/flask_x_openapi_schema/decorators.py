"""
Decorators for adding OpenAPI metadata to API endpoints with auto-detection of parameters.
This is an improved version with simplified logic and better maintainability.
"""

import inspect
from collections.abc import Callable
from functools import wraps
from typing import (
    Any,
    Optional,
    TypeVar,
    Union,
    cast,
    get_type_hints,
    Dict,
    List,
    Tuple,
    Type,
)

# For Python 3.10+, use typing directly; for older versions, use typing_extensions
try:
    from typing import ParamSpec  # Python 3.10+
except ImportError:
    from typing_extensions import ParamSpec  # Python < 3.10

from pydantic import BaseModel
from flask import request

from .i18n.i18n_string import I18nString, get_current_language
from .models.base import BaseRespModel

# Import Flask-RESTful utilities if available
try:
    from .restful_utils import (
        create_reqparse_from_pydantic,
        extract_openapi_parameters_from_pydantic,
    )

    HAS_FLASK_RESTFUL = True
except ImportError:
    # Define placeholder functions for when Flask-RESTful is not available
    def create_reqparse_from_pydantic(*args, **kwargs):
        raise ImportError(
            "Flask-RESTful is not installed. Install with 'pip install flask-x-openapi-schema[restful]'"
        )

    def extract_openapi_parameters_from_pydantic(*args, **kwargs):
        raise ImportError(
            "Flask-RESTful is not installed. Install with 'pip install flask-x-openapi-schema[restful]'"
        )

    HAS_FLASK_RESTFUL = False

# Type variables for function parameters and return type
P = ParamSpec("P")
R = TypeVar("R")
F = TypeVar("F", bound=Callable[..., Any])

# Special parameter prefixes for binding
REQUEST_BODY_PREFIX = "x_request_body"
REQUEST_QUERY_PREFIX = "x_request_query"
REQUEST_PATH_PREFIX = "x_request_path"
REQUEST_FILE_PREFIX = "x_request_file"


def _detect_parameters(
    signature: inspect.Signature, type_hints: Dict[str, Any]
) -> Tuple[Optional[Type[BaseModel]], Optional[Type[BaseModel]], List[str]]:
    """
    Detect request parameters from function signature.

    Args:
        signature: Function signature
        type_hints: Function type hints

    Returns:
        Tuple of (detected_request_body, detected_query_model, detected_path_params)
    """
    detected_request_body = None
    detected_query_model = None
    detected_path_params = []

    # Look for parameters with special prefixes
    for param_name in signature.parameters:
        # Skip 'self' and 'cls' parameters
        if param_name in ("self", "cls"):
            continue

        # Check for x_request_body parameter
        if param_name.startswith(REQUEST_BODY_PREFIX) and param_name in type_hints:
            param_type = type_hints[param_name]
            if isinstance(param_type, type) and issubclass(param_type, BaseModel):
                detected_request_body = param_type

        # Check for x_request_query parameter
        elif param_name.startswith(REQUEST_QUERY_PREFIX) and param_name in type_hints:
            param_type = type_hints[param_name]
            if isinstance(param_type, type) and issubclass(param_type, BaseModel):
                detected_query_model = param_type

        # Check for x_request_path parameter
        elif param_name.startswith(REQUEST_PATH_PREFIX):
            # Extract the path parameter name from the parameter name
            # Format: x_request_path_<param_name>
            if "_" in param_name[len(REQUEST_PATH_PREFIX) + 1 :]:
                path_param_name = param_name[len(REQUEST_PATH_PREFIX) + 1 :].split(
                    "_", 1
                )[1]
                detected_path_params.append(path_param_name)

    return detected_request_body, detected_query_model, detected_path_params


def _process_i18n_value(
    value: Optional[Union[str, I18nString]], language: Optional[str]
) -> Optional[str]:
    """
    Process an I18nString value to get the string for the current language.

    Args:
        value: The value to process (string or I18nString)
        language: The language to use, or None to use the current language

    Returns:
        The processed string value
    """
    if value is None:
        return None

    current_lang = language or get_current_language()

    if isinstance(value, I18nString):
        return value.get(current_lang)
    return value


def _generate_openapi_metadata(
    summary: Optional[Union[str, I18nString]],
    description: Optional[Union[str, I18nString]],
    tags: Optional[List[str]],
    operation_id: Optional[str],
    deprecated: bool,
    security: Optional[List[Dict[str, List[str]]]],
    external_docs: Optional[Dict[str, str]],
    actual_request_body: Optional[Union[Type[BaseModel], Dict[str, Any]]],
    responses: Optional[Dict[str, Any]],
    parameters: Optional[List[Dict[str, Any]]],
    actual_query_model: Optional[Type[BaseModel]],
    actual_path_params: Optional[List[str]],
    language: Optional[str],
) -> Dict[str, Any]:
    """
    Generate OpenAPI metadata dictionary.

    Args:
        Various parameters for OpenAPI metadata

    Returns:
        OpenAPI metadata dictionary
    """
    metadata: Dict[str, Any] = {}

    # Use the specified language or get the current language
    current_lang = language or get_current_language()

    # Handle I18nString fields
    if summary is not None:
        metadata["summary"] = _process_i18n_value(summary, current_lang)
    if description is not None:
        metadata["description"] = _process_i18n_value(description, current_lang)

    # Add other metadata fields if provided
    if tags:
        metadata["tags"] = tags
    if operation_id:
        metadata["operationId"] = operation_id
    if deprecated:
        metadata["deprecated"] = deprecated
    if security:
        metadata["security"] = security
    if external_docs:
        metadata["externalDocs"] = external_docs

    # Handle request body
    if actual_request_body:
        if isinstance(actual_request_body, type) and issubclass(
            actual_request_body, BaseModel
        ):
            # It's a Pydantic model
            metadata["requestBody"] = {
                "content": {
                    "application/json": {
                        "schema": {
                            "$ref": f"#/components/schemas/{actual_request_body.__name__}"
                        }
                    }
                },
                "required": True,
            }
        else:
            # It's a dict
            metadata["requestBody"] = actual_request_body

    # Handle responses
    if responses:
        metadata["responses"] = responses

    return metadata


def _handle_response(result: Any) -> Any:
    """
    Handle response conversion for BaseRespModel instances.

    Args:
        result: Function result

    Returns:
        Processed result
    """
    if isinstance(result, BaseRespModel):
        # Convert the model to a response
        return result.to_response()
    elif (
        isinstance(result, tuple)
        and len(result) >= 1
        and isinstance(result[0], BaseRespModel)
    ):
        # Handle tuple returns with status code
        model = result[0]
        if len(result) >= 2 and isinstance(result[1], int):
            # Return with status code
            return model.to_response(result[1])
        else:
            # Return without status code
            return model.to_response()

    # Return the original result if it's not a BaseRespModel
    return result


def _detect_file_parameters(
    param_names: List[str], func_annotations: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Detect file parameters from function signature.

    Args:
        param_names: List of parameter names
        func_annotations: Function type annotations

    Returns:
        List of file parameters for OpenAPI schema
    """
    file_params = []

    for param_name in param_names:
        if param_name.startswith(REQUEST_FILE_PREFIX):
            # Get the parameter type annotation
            param_type = None
            if param_name in func_annotations:
                param_type = func_annotations[param_name]

            # Extract the file parameter name
            if "_" in param_name[len(REQUEST_FILE_PREFIX) + 1 :]:
                file_param_name = param_name[len(REQUEST_FILE_PREFIX) + 1 :].split(
                    "_", 1
                )[1]
            else:
                file_param_name = "file"

            # Check if the parameter is a Pydantic model
            is_pydantic_model = (
                param_type
                and isinstance(param_type, type)
                and issubclass(param_type, BaseModel)
                and hasattr(param_type, "model_fields")
                and "file" in param_type.model_fields
            )

            # Get description from Pydantic model if available
            file_description = f"File upload for {file_param_name}"
            if is_pydantic_model and "file" in param_type.model_fields:
                field_info = param_type.model_fields["file"]
                if field_info.description:
                    file_description = field_info.description

            # Add file parameter to OpenAPI schema
            file_param = {
                "name": file_param_name,
                "in": "formData",
                "required": True,
                "type": "file",
                "description": file_description,
            }
            file_params.append(file_param)

    return file_params


def _extract_param_types(
    request_body_model: Optional[Type[BaseModel]],
    query_model: Optional[Type[BaseModel]],
) -> Dict[str, Any]:
    """
    Extract parameter types from Pydantic models for type annotations.

    Args:
        request_body_model: Request body Pydantic model
        query_model: Query parameters Pydantic model

    Returns:
        Dictionary of parameter types
    """
    param_types = {}

    # Add types from request_body if it's a Pydantic model
    if (
        request_body_model
        and isinstance(request_body_model, type)
        and issubclass(request_body_model, BaseModel)
    ):
        # Get field types from the Pydantic model
        for field_name, field in request_body_model.model_fields.items():
            param_types[field_name] = field.annotation

    # Add types from query_model if it's a Pydantic model
    if query_model:
        for field_name, field in query_model.model_fields.items():
            param_types[field_name] = field.annotation

    return param_types


def openapi_metadata(
    *,
    summary: Optional[Union[str, I18nString]] = None,
    description: Optional[Union[str, I18nString]] = None,
    tags: Optional[List[str]] = None,
    operation_id: Optional[str] = None,
    request_body: Optional[Union[Type[BaseModel], Dict[str, Any]]] = None,
    responses: Optional[Dict[str, Any]] = None,
    parameters: Optional[List[Dict[str, Any]]] = None,
    deprecated: bool = False,
    security: Optional[List[Dict[str, List[str]]]] = None,
    external_docs: Optional[Dict[str, str]] = None,
    query_model: Optional[Type[BaseModel]] = None,
    path_params: Optional[List[str]] = None,
    # The following parameters are optional and can be automatically detected from the function signature
    auto_detect_params: bool = True,
    language: Optional[str] = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator to add OpenAPI metadata to an API endpoint.

    This decorator does the following:
    1. Adds OpenAPI metadata to the function for documentation generation
    2. Automatically detects and binds request parameters to function parameters with special prefixes
    3. Preserves type annotations from Pydantic models for better IDE support
    4. Automatically converts BaseRespModel responses to Flask-RESTful compatible responses

    Special parameter prefixes (automatically detected if auto_detect_params=True):
    - x_request_body: Binds the entire request body object (auto-detected from type annotation)
    - x_request_query: Binds the entire query parameters object (auto-detected from type annotation)
    - x_request_path_<param_name>: Binds a path parameter (auto-detected from parameter name)
    - x_request_file: Binds a file object (auto-detected from parameter name)

    Args:
        summary: A short summary of what the operation does
        description: A verbose explanation of the operation behavior
        tags: A list of tags for API documentation control
        operation_id: Unique string used to identify the operation
        request_body: The request body schema (Pydantic model or dict)
        responses: The responses the API can return
        parameters: Parameters that are sent with the request
        deprecated: Declares this operation to be deprecated
        security: A declaration of which security mechanisms can be used for this operation
        external_docs: Additional external documentation
        query_model: Pydantic model for query parameters (optional if auto-detected)
        path_params: List of path parameter names (optional if auto-detected)
        auto_detect_params: Whether to automatically detect parameters from function signature
        language: Language code to use for I18nString values (default: current language)

    Returns:
        The decorated function with OpenAPI metadata attached and type annotations preserved
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        # Get the function signature to find parameters with special prefixes
        signature = inspect.signature(func)
        param_names = list(signature.parameters.keys())

        # Get type hints from the function
        type_hints = get_type_hints(func)

        # Auto-detect parameters if enabled
        detected_request_body = None
        detected_query_model = None
        detected_path_params = []

        if auto_detect_params:
            # Use helper function to detect parameters
            detected_request_body, detected_query_model, detected_path_params = (
                _detect_parameters(signature, type_hints)
            )

        # Use detected parameters if not explicitly provided
        actual_request_body = request_body
        if actual_request_body is None and detected_request_body is not None:
            actual_request_body = detected_request_body

        actual_query_model = query_model
        if actual_query_model is None and detected_query_model is not None:
            actual_query_model = detected_query_model

        actual_path_params = path_params
        if actual_path_params is None and detected_path_params:
            actual_path_params = detected_path_params

        # Generate OpenAPI metadata using helper function
        metadata = _generate_openapi_metadata(
            summary=summary,
            description=description,
            tags=tags,
            operation_id=operation_id,
            deprecated=deprecated,
            security=security,
            external_docs=external_docs,
            actual_request_body=actual_request_body,
            responses=responses,
            parameters=parameters,
            actual_query_model=actual_query_model,
            actual_path_params=actual_path_params,
            language=language,
        )

        # Handle parameters from the parameters argument
        openapi_parameters = parameters or []

        # Add parameters from query_model and path_params
        if actual_query_model or actual_path_params:
            model_parameters = extract_openapi_parameters_from_pydantic(
                query_model=actual_query_model, path_params=actual_path_params
            )
            openapi_parameters.extend(model_parameters)

        # Add file parameters based on function signature
        file_params = []
        if auto_detect_params:
            # Get function annotations
            func_annotations = get_type_hints(func)
            file_params = _detect_file_parameters(param_names, func_annotations)

        # If we have file parameters, set the consumes property to multipart/form-data
        if file_params:
            metadata["consumes"] = ["multipart/form-data"]
            openapi_parameters.extend(file_params)

        if openapi_parameters:
            metadata["parameters"] = openapi_parameters

        # Attach metadata to the function
        func._openapi_metadata = metadata  # type: ignore

        # Extract parameter types for type annotations
        param_types = _extract_param_types(
            request_body_model=actual_request_body
            if isinstance(actual_request_body, type)
            and issubclass(actual_request_body, BaseModel)
            else None,
            query_model=actual_query_model,
        )

        # Create a wrapper function that handles parameter binding
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Process request parameters based on whether Flask-RESTful is available
            parsed_args = None

            # Always process special parameters regardless of request_body or query_model
            # Check for parameters with special prefixes and bind accordingly
            for param_name in param_names:
                # Skip 'self' and 'cls' parameters
                if param_name in ("self", "cls"):
                    continue

                # Handle x_request_body parameter
                if (
                    param_name.startswith(REQUEST_BODY_PREFIX)
                    and actual_request_body
                    and isinstance(actual_request_body, type)
                    and issubclass(actual_request_body, BaseModel)
                ):
                    if HAS_FLASK_RESTFUL:
                        # Flask-RESTful approach using reqparse
                        parser = create_reqparse_from_pydantic(
                            body_model=actual_request_body, query_model=None
                        )
                        parsed_args = parser.parse_args()

                        # Create from parsed arguments
                        body_data = {}
                        for field_name in actual_request_body.model_fields:
                            if field_name in parsed_args:
                                body_data[field_name] = parsed_args[field_name]
                        model_instance = actual_request_body(**body_data)
                        kwargs[param_name] = model_instance
                    else:
                        # Direct Flask approach without reqparse
                        if request.is_json:
                            body_data = request.get_json(silent=True) or {}
                            # Try to use model_validate first (better handling of complex types)
                            try:
                                model_instance = actual_request_body.model_validate(
                                    body_data
                                )
                                kwargs[param_name] = model_instance
                            except Exception:
                                # Fallback to the old approach if model_validate fails
                                # Remove any keys that are not in the model to avoid unexpected keyword argument errors
                                filtered_body_data = {}
                                for field_name in actual_request_body.model_fields:
                                    if field_name in body_data:
                                        filtered_body_data[field_name] = body_data[
                                            field_name
                                        ]
                                model_instance = actual_request_body(
                                    **filtered_body_data
                                )
                                kwargs[param_name] = model_instance

                # Handle x_request_query parameter
                elif param_name.startswith(REQUEST_QUERY_PREFIX) and actual_query_model:
                    if HAS_FLASK_RESTFUL and not parsed_args:
                        # Flask-RESTful approach using reqparse
                        parser = create_reqparse_from_pydantic(
                            query_model=actual_query_model, body_model=None
                        )
                        parsed_args = parser.parse_args()

                        # Create from parsed arguments
                        query_data = {}
                        for field_name in actual_query_model.model_fields:
                            if field_name in parsed_args:
                                query_data[field_name] = parsed_args[field_name]
                        model_instance = actual_query_model(**query_data)
                        kwargs[param_name] = model_instance
                    else:
                        # Direct Flask approach without reqparse
                        query_data = {}
                        for field_name in actual_query_model.model_fields:
                            if field_name in request.args:
                                query_data[field_name] = request.args.get(field_name)
                        model_instance = actual_query_model(**query_data)
                        kwargs[param_name] = model_instance

                # Handle x_request_path parameter
                elif param_name.startswith(REQUEST_PATH_PREFIX) and actual_path_params:
                    # Extract the path parameter name from the parameter name
                    # Format: x_request_path_<param_name>
                    if "_" in param_name[len(REQUEST_PATH_PREFIX) + 1 :]:
                        path_param_name = param_name[
                            len(REQUEST_PATH_PREFIX) + 1 :
                        ].split("_", 1)[1]
                        if path_param_name in kwargs:
                            kwargs[param_name] = kwargs[path_param_name]

                # Handle x_request_file parameter
                elif param_name.startswith(REQUEST_FILE_PREFIX):
                    # Get the parameter type annotation
                    param_type = type_hints.get(param_name)

                    # Check if the parameter is a Pydantic model
                    is_pydantic_model = (
                        param_type
                        and isinstance(param_type, type)
                        and issubclass(param_type, BaseModel)
                        and hasattr(param_type, "model_fields")
                        and "file" in param_type.model_fields
                    )

                    # Check if we're in a request context
                    try:
                        has_request_context = bool(request)
                    except RuntimeError:
                        # Not in a request context, skip file handling
                        has_request_context = False

                    if has_request_context:
                        # Extract the file parameter name from the parameter name
                        # Format: x_request_file_<param_name>
                        if "_" in param_name[len(REQUEST_FILE_PREFIX) + 1 :]:
                            file_param_name = param_name[
                                len(REQUEST_FILE_PREFIX) + 1 :
                            ].split("_", 1)[1]
                            if file_param_name in request.files:
                                file_obj = request.files[file_param_name]
                                if is_pydantic_model:
                                    # Create a Pydantic model instance with the file
                                    kwargs[param_name] = param_type(file=file_obj)
                                else:
                                    # Just pass the file directly
                                    kwargs[param_name] = file_obj
                        else:
                            # If no specific file name is provided, use 'file' as the default
                            if "file" in request.files:
                                file_obj = request.files["file"]
                                if is_pydantic_model:
                                    # Create a Pydantic model instance with the file
                                    kwargs[param_name] = param_type(file=file_obj)
                                else:
                                    # Just pass the file directly
                                    kwargs[param_name] = file_obj
                            # If there's only one file, use that
                            elif len(request.files) == 1:
                                file_obj = next(iter(request.files.values()))
                                if is_pydantic_model:
                                    # Create a Pydantic model instance with the file
                                    kwargs[param_name] = param_type(file=file_obj)
                                else:
                                    # Just pass the file directly
                                    kwargs[param_name] = file_obj

            # Add all parsed arguments to kwargs for regular parameters
            if HAS_FLASK_RESTFUL and parsed_args:
                for arg_name, arg_value in parsed_args.items():
                    if arg_name not in kwargs:
                        kwargs[arg_name] = arg_value

            # Filter out any kwargs that are not in the function signature
            signature = inspect.signature(func)
            valid_kwargs = {}
            for param_name in signature.parameters:
                if param_name in kwargs:
                    valid_kwargs[param_name] = kwargs[param_name]

            # Call the original function with filtered kwargs
            result = func(*args, **valid_kwargs)

            # Handle response conversion using helper function
            return _handle_response(result)

        # Copy OpenAPI metadata to the wrapper
        wrapper._openapi_metadata = metadata  # type: ignore

        # Add type hints to the wrapper function
        if param_types:
            # Get existing type hints
            existing_hints = get_type_hints(func)
            # Merge with new type hints from Pydantic models
            merged_hints = {**existing_hints, **param_types}
            # Apply the merged type hints to the wrapper
            wrapper.__annotations__ = merged_hints

        return cast(Callable[P, R], wrapper)

    return decorator
