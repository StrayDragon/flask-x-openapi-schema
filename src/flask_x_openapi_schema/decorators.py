"""
Decorators for adding OpenAPI metadata to API endpoints with auto-detection of parameters.
"""

import inspect
from collections.abc import Callable
from functools import wraps
from typing import Any, Optional, TypeVar, Union, cast, get_type_hints

from pydantic import BaseModel

from .i18n.i18n_string import I18nString, get_current_language
from .models.base import BaseRespModel

try:
    from .restful_utils import (
        create_reqparse_from_pydantic,
        extract_openapi_parameters_from_pydantic,
    )

    HAS_FLASK_RESTFUL = True
except ImportError:
    HAS_FLASK_RESTFUL = False

    # Define placeholder functions for when Flask-RESTful is not available
    def create_reqparse_from_pydantic(*args, **kwargs):
        raise ImportError(
            "Flask-RESTful is not installed. Install with 'pip install flask-x-openapi-schema[restful]'"
        )

    def extract_openapi_parameters_from_pydantic(*args, **kwargs):
        raise ImportError(
            "Flask-RESTful is not installed. Install with 'pip install flask-x-openapi-schema[restful]'"
        )


from flask import request

F = TypeVar("F", bound=Callable[..., Any])

# Special parameter prefixes for binding
REQUEST_BODY_PREFIX = "x_request_body"
REQUEST_QUERY_PREFIX = "x_request_query"
REQUEST_PATH_PREFIX = "x_request_path"
REQUEST_FILE_PREFIX = "x_request_file"


def openapi_metadata(
    *,
    summary: Optional[Union[str, I18nString]] = None,
    description: Optional[Union[str, I18nString]] = None,
    tags: Optional[list[str]] = None,
    operation_id: Optional[str] = None,
    request_body: Optional[Union[type[BaseModel], dict[str, Any]]] = None,
    responses: Optional[dict[str, Any]] = None,
    parameters: Optional[list[dict[str, Any]]] = None,
    deprecated: bool = False,
    security: Optional[list[dict[str, list[str]]]] = None,
    external_docs: Optional[dict[str, str]] = None,
    query_model: Optional[type[BaseModel]] = None,
    path_params: Optional[list[str]] = None,
    # The following parameters are optional and can be automatically detected from the function signature
    auto_detect_params: bool = True,
    language: Optional[str] = None,
) -> Callable[[F], F]:
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

    Returns:
        The decorated function with OpenAPI metadata attached and type annotations preserved
    """

    def decorator(func: F) -> F:
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
            # Look for parameters with special prefixes
            for param_name in signature.parameters:
                # Skip 'self' and 'cls' parameters
                if param_name in ("self", "cls"):
                    continue

                # Check for x_request_body parameter
                if (
                    param_name.startswith(REQUEST_BODY_PREFIX)
                    and param_name in type_hints
                ):
                    param_type = type_hints[param_name]
                    if isinstance(param_type, type) and issubclass(
                        param_type, BaseModel
                    ):
                        detected_request_body = param_type

                # Check for x_request_query parameter
                elif (
                    param_name.startswith(REQUEST_QUERY_PREFIX)
                    and param_name in type_hints
                ):
                    param_type = type_hints[param_name]
                    if isinstance(param_type, type) and issubclass(
                        param_type, BaseModel
                    ):
                        detected_query_model = param_type

                # Check for x_request_path parameter
                elif param_name.startswith(REQUEST_PATH_PREFIX):
                    # Extract the path parameter name from the parameter name
                    # Format: x_request_path_<param_name>
                    if "_" in param_name[len(REQUEST_PATH_PREFIX) + 1 :]:
                        path_param_name = param_name[
                            len(REQUEST_PATH_PREFIX) + 1 :
                        ].split("_", 1)[1]
                        detected_path_params.append(path_param_name)

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

        # Generate OpenAPI metadata
        metadata: dict[str, Any] = {}

        # Use the specified language or get the current language
        current_lang = language or get_current_language()

        # Handle I18nString fields
        if summary is not None:
            if isinstance(summary, I18nString):
                metadata["summary"] = summary.get(current_lang)
            else:
                metadata["summary"] = summary
        if description is not None:
            if isinstance(description, I18nString):
                metadata["description"] = description.get(current_lang)
            else:
                metadata["description"] = description
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

        # Handle parameters from the parameters argument
        openapi_parameters = parameters or []

        # Add parameters from query_model and path_params
        if actual_query_model or actual_path_params:
            model_parameters = extract_openapi_parameters_from_pydantic(
                query_model=actual_query_model, path_params=actual_path_params
            )
            openapi_parameters.extend(model_parameters)

        # Add file parameters based on function signature
        has_file_params = False
        if auto_detect_params:
            # Get function annotations
            func_annotations = get_type_hints(func)

            for param_name in param_names:
                if param_name.startswith(REQUEST_FILE_PREFIX):
                    has_file_params = True

                    # Get the parameter type annotation
                    param_type = None
                    if param_name in func_annotations:
                        param_type = func_annotations[param_name]

                    # Extract the file parameter name
                    if "_" in param_name[len(REQUEST_FILE_PREFIX) + 1 :]:
                        file_param_name = param_name[
                            len(REQUEST_FILE_PREFIX) + 1 :
                        ].split("_", 1)[1]
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
                    openapi_parameters.append(file_param)

        # If we have file parameters, set the consumes property to multipart/form-data
        if has_file_params:
            metadata["consumes"] = ["multipart/form-data"]

        if openapi_parameters:
            metadata["parameters"] = openapi_parameters

        # Attach metadata to the function
        func._openapi_metadata = metadata  # type: ignore

        # Create a dictionary of parameter types for type annotations
        param_types = {}

        # Add types from request_body if it's a Pydantic model
        if isinstance(actual_request_body, type) and issubclass(
            actual_request_body, BaseModel
        ):
            # Get field types from the Pydantic model
            for field_name, field in actual_request_body.model_fields.items():
                param_types[field_name] = field.annotation

        # Add types from query_model if it's a Pydantic model
        if actual_query_model:
            for field_name, field in actual_query_model.model_fields.items():
                param_types[field_name] = field.annotation

        # Create a wrapper function that handles parameter binding
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Process request parameters based on whether Flask-RESTful is available
            if actual_request_body or actual_query_model:
                if HAS_FLASK_RESTFUL:
                    # Flask-RESTful approach using reqparse
                    parser = create_reqparse_from_pydantic(
                        query_model=actual_query_model,
                        body_model=actual_request_body
                        if isinstance(actual_request_body, type)
                        and issubclass(actual_request_body, BaseModel)
                        else None,
                    )
                    parsed_args = parser.parse_args()
                else:
                    # Direct Flask approach without reqparse
                    parsed_args = {}

                    # Process query parameters
                    if actual_query_model:
                        query_data = {}
                        for field_name in actual_query_model.model_fields:
                            if field_name in request.args:
                                query_data[field_name] = request.args.get(field_name)

                        # Add to parsed args
                        for field_name, value in query_data.items():
                            parsed_args[field_name] = value

                    # Process body parameters
                    if (
                        actual_request_body
                        and isinstance(actual_request_body, type)
                        and issubclass(actual_request_body, BaseModel)
                    ):
                        if request.is_json:
                            body_data = request.get_json(silent=True) or {}
                            # Add to parsed args
                            for field_name, value in body_data.items():
                                parsed_args[field_name] = value

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
                        # Create a Pydantic model instance
                        if request.is_json:
                            body_data = request.get_json(silent=True) or {}
                            # Remove any keys that are not in the model to avoid unexpected keyword argument errors
                            filtered_body_data = {}
                            for field_name in actual_request_body.model_fields:
                                if field_name in body_data:
                                    filtered_body_data[field_name] = body_data[
                                        field_name
                                    ]
                            model_instance = actual_request_body(**filtered_body_data)
                            kwargs[param_name] = model_instance
                        elif HAS_FLASK_RESTFUL:
                            # Create from parsed arguments if using Flask-RESTful
                            body_data = {}
                            for field_name in actual_request_body.model_fields:
                                if field_name in parsed_args:
                                    body_data[field_name] = parsed_args[field_name]
                            model_instance = actual_request_body(**body_data)
                            kwargs[param_name] = model_instance

                    # Handle x_request_query parameter
                    elif (
                        param_name.startswith(REQUEST_QUERY_PREFIX)
                        and actual_query_model
                    ):
                        # Create a Pydantic model instance from query parameters
                        query_data = {}
                        if HAS_FLASK_RESTFUL:
                            # Use parsed args from reqparse
                            for field_name in actual_query_model.model_fields:
                                if field_name in parsed_args:
                                    query_data[field_name] = parsed_args[field_name]
                        else:
                            # Use request.args directly
                            for field_name in actual_query_model.model_fields:
                                if field_name in request.args:
                                    query_data[field_name] = request.args.get(
                                        field_name
                                    )

                        # Create the model instance
                        model_instance = actual_query_model(**query_data)
                        kwargs[param_name] = model_instance

                    # Handle x_request_path parameter
                    elif (
                        param_name.startswith(REQUEST_PATH_PREFIX)
                        and actual_path_params
                    ):
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
                        param_type = (
                            param_types.get(param_name) if param_types else None
                        )

                        # Check if the parameter is a Pydantic model
                        is_pydantic_model = (
                            param_type
                            and isinstance(param_type, type)
                            and issubclass(param_type, BaseModel)
                            and hasattr(param_type, "model_fields")
                            and "file" in param_type.model_fields
                        )

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
                if HAS_FLASK_RESTFUL:
                    for arg_name, arg_value in parsed_args.items():
                        if arg_name not in kwargs:
                            kwargs[arg_name] = arg_value

            # No debug print in production code

            # Filter out any kwargs that are not in the function signature
            signature = inspect.signature(func)
            valid_kwargs = {}
            for param_name in signature.parameters:
                if param_name in kwargs:
                    valid_kwargs[param_name] = kwargs[param_name]

            # Call the original function with filtered kwargs
            result = func(*args, **valid_kwargs)

            # Handle response conversion for BaseRespModel instances
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

        return cast(F, wrapper)

    return decorator
