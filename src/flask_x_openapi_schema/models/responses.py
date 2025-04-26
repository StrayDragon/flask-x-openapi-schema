"""Response models for OpenAPI schema generation.

This module provides models for defining OpenAPI responses in a structured way.
"""

from typing import Any

from pydantic import BaseModel, Field


class OpenAPIMetaResponseItem(BaseModel):
    """Represents a single response item in an OpenAPI specification.

    This class allows defining a response with either a Pydantic model or a simple message.
    It is used to define the response for a specific status code in the OpenAPI schema.

    :param model: Pydantic model for the response
    :type model: Optional[Type[BaseModel]]
    :param description: Response description
    :type description: str
    :param content_type: Response content type
    :type content_type: str
    :param headers: Response headers
    :type headers: Optional[Dict[str, Any]]
    :param examples: Response examples
    :type examples: Optional[Dict[str, Any]]
    :param msg: Simple message for responses without a model
    :type msg: Optional[str]

    Example:
        >>> from flask_x_openapi_schema import OpenAPIMetaResponseItem
        >>> from pydantic import BaseModel
        >>>
        >>> class UserResponse(BaseModel):
        ...     id: str
        ...     name: str
        >>> response_item = OpenAPIMetaResponseItem(
        ...     model=UserResponse, description="User details", content_type="application/json"
        ... )

    """

    model: type[BaseModel] | None = Field(None, description="Pydantic model for the response")
    description: str = Field("Successful response", description="Response description")
    content_type: str = Field("application/json", description="Response content type")
    headers: dict[str, Any] | None = Field(None, description="Response headers")
    examples: dict[str, Any] | None = Field(None, description="Response examples")
    msg: str | None = Field(None, description="Simple message for responses without a model")

    def to_openapi_dict(self) -> dict[str, Any]:
        """Convert the response item to an OpenAPI response object.

        Returns:
            An OpenAPI response object

        """
        response = {"description": self.description}

        # Add content if model is provided
        if self.model:
            response["content"] = {
                self.content_type: {"schema": {"$ref": f"#/components/schemas/{self.model.__name__}"}},
            }

            # Add examples if provided
            if self.examples:
                response["content"][self.content_type]["examples"] = self.examples

        # Add headers if provided
        if self.headers:
            response["headers"] = self.headers

        return response


class OpenAPIMetaResponse(BaseModel):
    """Container for OpenAPI response definitions.

    This class allows defining multiple responses for different status codes.
    It is used to define all possible responses for an API endpoint in the OpenAPI schema.

    :param responses: Map of status codes to response definitions
    :type responses: Dict[str, OpenAPIMetaResponseItem]

    Example:
        >>> from flask_x_openapi_schema import OpenAPIMetaResponse, OpenAPIMetaResponseItem
        >>> from pydantic import BaseModel
        >>>
        >>> class UserResponse(BaseModel):
        ...     id: str
        ...     name: str
        >>> class ErrorResponse(BaseModel):
        ...     error: str
        ...     code: int
        >>> responses = OpenAPIMetaResponse(
        ...     responses={
        ...         "200": OpenAPIMetaResponseItem(
        ...             model=UserResponse, description="User details retrieved successfully"
        ...         ),
        ...         "404": OpenAPIMetaResponseItem(model=ErrorResponse, description="User not found"),
        ...     }
        ... )

    """

    responses: dict[str, OpenAPIMetaResponseItem] = Field(
        ...,
        description="Map of status codes to response definitions",
    )

    def to_openapi_dict(self) -> dict[str, Any]:
        """Convert the response container to an OpenAPI responses object.

        Returns:
            An OpenAPI responses object

        """
        result = {}
        for status_code, response_item in self.responses.items():
            result[status_code] = response_item.to_openapi_dict()
        return result


def create_response(
    model: type[BaseModel] | None = None,
    description: str = "Successful response",
    status_code: int | str = 200,
    content_type: str = "application/json",
    headers: dict[str, Any] | None = None,
    examples: dict[str, Any] | None = None,
    msg: str | None = None,
) -> dict[str, OpenAPIMetaResponseItem]:
    """Create a response definition for use with OpenAPIMetaResponse.

    This is a helper function to create a response definition for a specific status code.
    It returns a dictionary that can be used to build an OpenAPIMetaResponse object.

    :param model: Pydantic model for the response
    :type model: Optional[Type[BaseModel]]
    :param description: Response description
    :type description: str
    :param status_code: HTTP status code
    :type status_code: Union[int, str]
    :param content_type: Response content type
    :type content_type: str
    :param headers: Response headers
    :type headers: Optional[Dict[str, Any]]
    :param examples: Response examples
    :type examples: Optional[Dict[str, Any]]
    :param msg: Simple message for responses without a model
    :type msg: Optional[str]
    :return: A dictionary with the status code as key and response item as value
    :rtype: Dict[str, OpenAPIMetaResponseItem]

    Example:
        >>> from flask_x_openapi_schema import create_response, OpenAPIMetaResponse
        >>> from pydantic import BaseModel
        >>>
        >>> class UserResponse(BaseModel):
        ...     id: str
        ...     name: str
        >>> # Create a response for status code 200
        >>> user_response = create_response(model=UserResponse, description="User details", status_code=200)
        >>>
        >>> # Create a response for status code 404
        >>> not_found_response = create_response(msg="User not found", description="User not found", status_code=404)
        >>>
        >>> # Combine responses
        >>> responses = OpenAPIMetaResponse(responses={**user_response, **not_found_response})

    """
    return {
        str(status_code): OpenAPIMetaResponseItem(
            model=model,
            description=description,
            content_type=content_type,
            headers=headers,
            examples=examples,
            msg=msg,
        ),
    }


def success_response(
    model: type[BaseModel],
    description: str = "Successful response",
    status_code: int | str = 200,
    content_type: str = "application/json",
    headers: dict[str, Any] | None = None,
    examples: dict[str, Any] | None = None,
) -> dict[str, OpenAPIMetaResponseItem]:
    """Create a success response definition for use with OpenAPIMetaResponse.

    Args:
        model: Pydantic model for the response
        description: Response description
        status_code: HTTP status code
        content_type: Response content type
        headers: Response headers
        examples: Response examples

    Returns:
        A dictionary with the status code as key and response item as value

    """
    return create_response(
        model=model,
        description=description,
        status_code=status_code,
        content_type=content_type,
        headers=headers,
        examples=examples,
    )


def error_response(
    description: str,
    status_code: int | str = 400,
    model: type[BaseModel] | None = None,
    content_type: str = "application/json",
    headers: dict[str, Any] | None = None,
    examples: dict[str, Any] | None = None,
    msg: str | None = None,
) -> dict[str, OpenAPIMetaResponseItem]:
    """Create an error response definition for use with OpenAPIMetaResponse.

    Args:
        description: Response description
        status_code: HTTP status code
        model: Optional Pydantic model for the response
        content_type: Response content type
        headers: Response headers
        examples: Response examples
        msg: Simple message for responses without a model

    Returns:
        A dictionary with the status code as key and response item as value

    """
    return create_response(
        model=model,
        description=description,
        status_code=status_code,
        content_type=content_type,
        headers=headers,
        examples=examples,
        msg=msg,
    )
