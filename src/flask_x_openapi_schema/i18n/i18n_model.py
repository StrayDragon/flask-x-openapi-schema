"""Internationalization support for Pydantic models."""

from typing import Any, ClassVar, TypeVar, get_type_hints

from pydantic import BaseModel, ConfigDict, create_model, field_serializer

from .i18n_string import I18nStr, get_current_language

T = TypeVar("T", bound="I18nBaseModel")


class I18nBaseModel(BaseModel):
    """Base model for Pydantic models with internationalization support.

    This class provides methods for working with internationalized fields in Pydantic models.
    Fields that should be internationalized should be annotated with I18nString.

    Examples:
        ```python
        class MyModel(I18nBaseModel):
            name: str
            description: I18nString
        ```

    """

    __i18n_fields__: ClassVar[list[str]] = []

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_serializer("*")
    def serialize_i18n_string(self, v, _):  # noqa: ANN001, ANN201, D102
        if isinstance(v, I18nStr):
            return str(v)
        return v

    def __init_subclass__(cls, **kwargs):  # noqa: ANN204
        """Initialize a subclass of I18nBaseModel.

        This method is called when a subclass of I18nBaseModel is created.
        It identifies fields that are annotated with I18nString and stores them
        in the __i18n_fields__ class variable.
        """
        super().__init_subclass__(**kwargs)

        hints = get_type_hints(cls)

        i18n_fields = []
        for field_name, field_type in hints.items():
            if field_type == I18nStr:
                i18n_fields.append(field_name)

        cls.__i18n_fields__ = i18n_fields

    def model_dump(self, **kwargs) -> dict[str, Any]:
        """Convert the model to a dictionary.

        This method overrides the default model_dump method to convert I18nString fields
        to strings in the current language.

        Args:
            **kwargs: Additional arguments to pass to the parent model_dump method

        Returns:
            A dictionary representation of the model

        """
        data = super().model_dump(**kwargs)

        for field_name in self.__i18n_fields__:
            if field_name in data and isinstance(data[field_name], I18nStr):
                data[field_name] = str(data[field_name])

        return data

    @classmethod
    def model_json_schema(cls, **kwargs) -> dict[str, Any]:
        """Generate a JSON schema for the model.

        This method overrides the default model_json_schema method to handle I18nString fields.
        I18nString fields are converted to string fields in the schema.

        Args:
            **kwargs: Additional arguments to pass to the parent model_json_schema method

        Returns:
            A JSON schema for the model

        """
        schema = super().model_json_schema(**kwargs)

        properties = schema.get("properties", {})
        for field_name in cls.__i18n_fields__:
            if field_name in properties:
                properties[field_name]["type"] = "string"

                properties[field_name]["description"] = (
                    properties[field_name].get("description", "") + " (Internationalized field)"
                )

        return schema

    @classmethod
    def for_language(cls, language: str | None = None) -> type[BaseModel]:
        """Create a new model class with I18nString fields converted to string fields.

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

        hints = get_type_hints(cls)

        fields = {}
        for field_name, field_type in hints.items():
            if field_name in cls.__i18n_fields__:
                fields[field_name] = (str, ...)
            else:
                fields[field_name] = (field_type, ...)

        return create_model(
            f"{cls.__name__}_{language}",
            **fields,
            __base__=BaseModel,
        )
