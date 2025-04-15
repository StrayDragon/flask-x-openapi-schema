"""
Internationalization support for Pydantic models.
"""

from typing import Any, ClassVar, Optional, TypeVar, get_type_hints

from pydantic import BaseModel, ConfigDict, create_model, field_serializer

from .i18n_string import I18nStr, get_current_language

T = TypeVar("T", bound="I18nBaseModel")


class I18nBaseModel(BaseModel):
    """
    Base model for Pydantic models with internationalization support.

    This class provides methods for working with internationalized fields in Pydantic models.
    Fields that should be internationalized should be annotated with I18nString.

    Example:
        ```python
        class MyModel(I18nBaseModel):
            name: str
            description: I18nString
        ```
    """

    # Class variable to store i18n field names
    __i18n_fields__: ClassVar[list[str]] = []

    # Configure Pydantic model to allow arbitrary types
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Serialize I18nString fields to strings
    @field_serializer("*")
    def serialize_i18n_string(self, v, _):
        if isinstance(v, I18nStr):
            return str(v)
        return v

    def __init_subclass__(cls, **kwargs):
        """
        Initialize a subclass of I18nBaseModel.

        This method is called when a subclass of I18nBaseModel is created.
        It identifies fields that are annotated with I18nString and stores them
        in the __i18n_fields__ class variable.
        """
        super().__init_subclass__(**kwargs)

        # Get type hints for the class
        hints = get_type_hints(cls)

        # Find fields that are annotated with I18nString
        i18n_fields = []
        for field_name, field_type in hints.items():
            if field_type == I18nStr:
                i18n_fields.append(field_name)

        # Store the i18n field names in the class
        cls.__i18n_fields__ = i18n_fields

    def model_dump(self, **kwargs) -> dict[str, Any]:
        """
        Convert the model to a dictionary.

        This method overrides the default model_dump method to convert I18nString fields
        to strings in the current language.

        Args:
            **kwargs: Additional arguments to pass to the parent model_dump method

        Returns:
            A dictionary representation of the model
        """
        # Get the dictionary representation of the model
        data = super().model_dump(**kwargs)

        # Convert I18nString fields to strings in the current language
        for field_name in self.__i18n_fields__:
            if field_name in data and isinstance(data[field_name], I18nStr):
                data[field_name] = str(data[field_name])

        return data

    @classmethod
    def model_json_schema(cls, **kwargs) -> dict[str, Any]:
        """
        Generate a JSON schema for the model.

        This method overrides the default model_json_schema method to handle I18nString fields.
        I18nString fields are converted to string fields in the schema.

        Args:
            **kwargs: Additional arguments to pass to the parent model_json_schema method

        Returns:
            A JSON schema for the model
        """
        # Get the JSON schema for the model
        schema = super().model_json_schema(**kwargs)

        # Update the schema for I18nString fields
        properties = schema.get("properties", {})
        for field_name in cls.__i18n_fields__:
            if field_name in properties:
                # Convert I18nString fields to string fields in the schema
                properties[field_name]["type"] = "string"
                # Add a note about internationalization
                properties[field_name]["description"] = (
                    properties[field_name].get("description", "")
                    + " (Internationalized field)"
                )

        return schema

    @classmethod
    def for_language(cls: type[T], language: Optional[str] = None) -> type[BaseModel]:
        """
        Create a new model class with I18nString fields converted to string fields.

        This method creates a new Pydantic model class where I18nString fields are
        converted to string fields. This is useful for generating schemas for a specific language.

        Args:
            language: The language to use for I18nString fields.
                     If None, uses the current language.

        Returns:
            A new Pydantic model class with I18nString fields converted to string fields
        """
        if language is None:
            language = get_current_language()

        # Get type hints for the class
        hints = get_type_hints(cls)

        # Create field definitions for the new model
        fields = {}
        for field_name, field_type in hints.items():
            if field_name in cls.__i18n_fields__:
                # Convert I18nString fields to string fields
                fields[field_name] = (str, ...)
            else:
                # Keep other fields as they are
                fields[field_name] = (field_type, ...)

        # Create a new model class
        return create_model(
            f"{cls.__name__}_{language}",
            **fields,
            __base__=BaseModel,
        )
