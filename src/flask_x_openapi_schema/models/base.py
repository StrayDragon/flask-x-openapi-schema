"""
Base models for OpenAPI schema generation.
"""

from typing import Any, Optional, TypeVar, Union

from pydantic import BaseModel, ConfigDict

T = TypeVar("T", bound="BaseRespModel")


class BaseRespModel(BaseModel):
    """
    Base model for API responses.

    This class extends Pydantic's BaseModel to provide a standard way to convert
    response models to Flask-RESTful compatible responses.

    Usage:
        class MyResponse(BaseRespModel):
            id: str
            name: str

        # In your API endpoint:
        def get(self):
            return MyResponse(id="123", name="Example")

        # Or with a status code:
        def post(self):
            return MyResponse(id="123", name="Example"), 201
    """

    # Configure Pydantic model
    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        extra="ignore",
        arbitrary_types_allowed=True,
    )

    @classmethod
    def from_dict(cls: type[T], data: dict[str, Any]) -> T:
        """
        Create a model instance from a dictionary.

        Args:
            data: Dictionary containing model data

        Returns:
            An instance of the model
        """
        return cls(**data)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the model to a dictionary.

        Returns:
            A dictionary representation of the model
        """
        # Use model_dump with custom encoder for datetime objects
        return self.model_dump(exclude_none=True, mode="json")

    def to_response(
        self, status_code: Optional[int] = None
    ) -> Union[dict[str, Any], tuple[dict[str, Any], int]]:
        """
        Convert the model to a Flask-RESTful compatible response.

        Args:
            status_code: Optional HTTP status code

        Returns:
            A Flask-RESTful compatible response
        """
        response_dict = self.to_dict()

        if status_code is not None:
            return response_dict, status_code

        return response_dict
