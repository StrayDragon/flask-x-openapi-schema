"""Base models for OpenAPI schema generation."""

from typing import Any, Self, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T", bound="BaseRespModel")


class BaseRespModel(BaseModel):
    """Base model for API responses.

    This class extends Pydantic's BaseModel to provide a standard way to convert
    response models to Flask-compatible responses. It includes methods for converting
    the model to dictionaries and Flask response objects.

    :param model_config: Configuration for the Pydantic model

    Example:
        >>> from flask_x_openapi_schema import BaseRespModel
        >>> from pydantic import Field
        >>>
        >>> class UserResponse(BaseRespModel):
        ...     id: str = Field(..., description="User ID")
        ...     name: str = Field(..., description="User name")
        ...     email: str = Field(..., description="User email")
        >>> # In your API endpoint:
        >>> def get(self):
        ...     # Returns a dictionary that Flask will convert to JSON
        ...     return UserResponse(id="123", name="John Doe", email="john@example.com")
        >>> # Or with a status code:
        >>> def post(self):
        ...     # Returns a tuple with the dictionary and status code
        ...     return UserResponse(id="123", name="John Doe", email="john@example.com"), 201
        >>> # Or use the to_response method:
        >>> def put(self):
        ...     user = UserResponse(id="123", name="John Doe", email="john@example.com")
        ...     return user.to_response(status_code=200)

    """

    # Configure Pydantic model
    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        extra="ignore",
        arbitrary_types_allowed=True,
    )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create a model instance from a dictionary.

        :param data: Dictionary containing model data
        :type data: dict[str, Any]
        :return: An instance of the model
        :rtype: T

        Example:
            >>> data = {"id": "123", "name": "John Doe", "email": "john@example.com"}
            >>> user = UserResponse.from_dict(data)

        """
        return cls(**data)

    def to_dict(self) -> dict[str, Any]:
        """Convert the model to a dictionary.

        :return: A dictionary representation of the model
        :rtype: dict[str, Any]

        Example:
            >>> user = UserResponse(id="123", name="John Doe", email="john@example.com")
            >>> user_dict = user.to_dict()
            >>> user_dict
            {'id': '123', 'name': 'John Doe', 'email': 'john@example.com'}

        """
        # Use model_dump with custom encoder for datetime objects
        return self.model_dump(exclude_none=True, mode="json")

    def to_response(self, status_code: int | None = None) -> dict[str, Any] | tuple[dict[str, Any], int]:
        """Convert the model to a Flask-compatible response.

        :param status_code: Optional HTTP status code
        :type status_code: Optional[int]
        :return: A Flask-compatible response (dict or tuple with dict and status code)
        :rtype: Union[dict[str, Any], tuple[dict[str, Any], int]]

        Example:
            >>> user = UserResponse(id="123", name="John Doe", email="john@example.com")
            >>> # Without status code
            >>> response = user.to_response()
            >>> # With status code
            >>> response = user.to_response(status_code=201)

        """
        response_dict = self.to_dict()

        if status_code is not None:
            return response_dict, status_code

        return response_dict
