"""Base models for OpenAPI schema generation.

This module provides base models for generating OpenAPI schemas and handling API responses.
It includes the BaseRespModel class which extends Pydantic's BaseModel to provide
standardized methods for converting models to Flask-compatible responses.
"""

from typing import Any, Self, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T", bound="BaseRespModel")


class BaseRespModel(BaseModel):
    """Base model for API responses.

    This class extends Pydantic's BaseModel to provide a standard way to convert
    response models to Flask-compatible responses. It includes methods for converting
    the model to dictionaries and Flask response objects.

    Attributes:
        model_config: Configuration for the Pydantic model.

    Examples:
        >>> from flask_x_openapi_schema import BaseRespModel
        >>> from pydantic import Field
        >>>
        >>> class UserResponse(BaseRespModel):
        ...     id: str = Field(..., description="User ID")
        ...     name: str = Field(..., description="User name")
        ...     email: str = Field(..., description="User email")
        >>> def get(self):
        ...     return UserResponse(id="123", name="John Doe", email="john@example.com")
        >>> def post(self):
        ...     return UserResponse(id="123", name="John Doe", email="john@example.com"), 201
        >>> def put(self):
        ...     user = UserResponse(id="123", name="John Doe", email="john@example.com")
        ...     return user.to_response(status_code=200)

    """

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        extra="ignore",
        arbitrary_types_allowed=True,
    )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create a model instance from a dictionary.

        Args:
            data: Dictionary containing model data.

        Returns:
            An instance of the model.

        Examples:
            >>> from flask_x_openapi_schema import BaseRespModel
            >>> from pydantic import Field
            >>> class UserResponse(BaseRespModel):
            ...     id: str = Field(..., description="User ID")
            ...     name: str = Field(..., description="User name")
            ...     email: str = Field(..., description="User email")
            >>> data = {"id": "123", "name": "John Doe", "email": "john@example.com"}
            >>> user = UserResponse.from_dict(data)
            >>> user.id
            '123'

        """
        return cls(**data)

    def to_dict(self) -> dict[str, Any]:
        """Convert the model to a dictionary.

        Returns:
            A dictionary representation of the model.

        Examples:
            >>> from flask_x_openapi_schema import BaseRespModel
            >>> from pydantic import Field
            >>> class UserResponse(BaseRespModel):
            ...     id: str = Field(..., description="User ID")
            ...     name: str = Field(..., description="User name")
            ...     email: str = Field(..., description="User email")
            >>> user = UserResponse(id="123", name="John Doe", email="john@example.com")
            >>> user_dict = user.to_dict()
            >>> user_dict
            {'id': '123', 'name': 'John Doe', 'email': 'john@example.com'}

        """
        return self.model_dump(exclude_none=True, mode="json")

    def to_response(self, status_code: int | None = None) -> dict[str, Any] | tuple[dict[str, Any], int]:
        """Convert the model to a Flask-compatible response.

        Args:
            status_code: Optional HTTP status code.

        Returns:
            A Flask-compatible response (dict or tuple with dict and status code).

        Examples:
            >>> from flask_x_openapi_schema import BaseRespModel
            >>> from pydantic import Field
            >>> class UserResponse(BaseRespModel):
            ...     id: str = Field(..., description="User ID")
            ...     name: str = Field(..., description="User name")
            ...     email: str = Field(..., description="User email")
            >>> user = UserResponse(id="123", name="John Doe", email="john@example.com")
            >>> response = user.to_response()
            >>> isinstance(response, dict)
            True
            >>> response = user.to_response(status_code=201)
            >>> isinstance(response, tuple) and response[1] == 201
            True

        """
        response_dict = self.to_dict()

        if status_code is not None:
            return response_dict, status_code

        return response_dict
