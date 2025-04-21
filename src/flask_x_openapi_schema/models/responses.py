"""
Response models for OpenAPI schema generation.

This module provides models for defining OpenAPI responses in a structured way.
"""

from typing import Any, Dict, Optional, Type, Union

from pydantic import BaseModel, Field


class OpenAPIMetaResponseItem(BaseModel):
    """
    Represents a single response item in an OpenAPI specification.

    This class allows defining a response with either a Pydantic model or a simple message.
    """

    model: Optional[Type[BaseModel]] = Field(
        None, description="Pydantic model for the response"
    )
    description: str = Field("Successful response", description="Response description")
    content_type: str = Field("application/json", description="Response content type")
    headers: Optional[Dict[str, Any]] = Field(None, description="Response headers")
    examples: Optional[Dict[str, Any]] = Field(None, description="Response examples")
    msg: Optional[str] = Field(
        None, description="Simple message for responses without a model"
    )

    def to_openapi_dict(self) -> Dict[str, Any]:
        """
        Convert the response item to an OpenAPI response object.

        Returns:
            An OpenAPI response object
        """
        response = {"description": self.description}

        # Add content if model is provided
        if self.model:
            print(
                f"OpenAPIMetaResponseItem.to_openapi_dict: model={self.model.__name__}"
            )
            response["content"] = {
                self.content_type: {
                    "schema": {"$ref": f"#/components/schemas/{self.model.__name__}"}
                }
            }

            # Add examples if provided
            if self.examples:
                response["content"][self.content_type]["examples"] = self.examples

        # Add headers if provided
        if self.headers:
            response["headers"] = self.headers

        return response


class OpenAPIMetaResponse(BaseModel):
    """
    Container for OpenAPI response definitions.

    This class allows defining multiple responses for different status codes.
    """

    responses: Dict[str, OpenAPIMetaResponseItem] = Field(
        ..., description="Map of status codes to response definitions"
    )

    def to_openapi_dict(self) -> Dict[str, Any]:
        """
        Convert the response container to an OpenAPI responses object.

        Returns:
            An OpenAPI responses object
        """
        result = {}
        for status_code, response_item in self.responses.items():
            result[status_code] = response_item.to_openapi_dict()
        return result


def create_response(
    model: Optional[Type[BaseModel]] = None,
    description: str = "Successful response",
    status_code: Union[int, str] = 200,
    content_type: str = "application/json",
    headers: Optional[Dict[str, Any]] = None,
    examples: Optional[Dict[str, Any]] = None,
    msg: Optional[str] = None,
) -> Dict[str, OpenAPIMetaResponseItem]:
    """
    Create a response definition for use with OpenAPIMetaResponse.

    Args:
        model: Pydantic model for the response
        description: Response description
        status_code: HTTP status code
        content_type: Response content type
        headers: Response headers
        examples: Response examples
        msg: Simple message for responses without a model

    Returns:
        A dictionary with the status code as key and response item as value
    """
    return {
        str(status_code): OpenAPIMetaResponseItem(
            model=model,
            description=description,
            content_type=content_type,
            headers=headers,
            examples=examples,
            msg=msg,
        )
    }


def success_response(
    model: Type[BaseModel],
    description: str = "Successful response",
    status_code: Union[int, str] = 200,
    content_type: str = "application/json",
    headers: Optional[Dict[str, Any]] = None,
    examples: Optional[Dict[str, Any]] = None,
) -> Dict[str, OpenAPIMetaResponseItem]:
    """
    Create a success response definition for use with OpenAPIMetaResponse.

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
    status_code: Union[int, str] = 400,
    model: Optional[Type[BaseModel]] = None,
    content_type: str = "application/json",
    headers: Optional[Dict[str, Any]] = None,
    examples: Optional[Dict[str, Any]] = None,
    msg: Optional[str] = None,
) -> Dict[str, OpenAPIMetaResponseItem]:
    """
    Create an error response definition for use with OpenAPIMetaResponse.

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
