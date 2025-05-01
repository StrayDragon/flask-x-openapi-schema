"""Pydantic models for file uploads in OpenAPI.

This module provides a structured way to handle file uploads with validation and type hints.
The models are designed to work with OpenAPI 3.0.x specification and provide proper
validation for different file types.
"""

from enum import Enum
from typing import Any, TypeVar

import pydantic
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_core import core_schema
from werkzeug.datastructures import FileStorage

_T = TypeVar("_T")


class FileType(str, Enum):
    """Enumeration of file types for OpenAPI schema."""

    BINARY = "binary"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    PDF = "pdf"
    TEXT = "text"


class FileField(str):
    """Field for file uploads in OpenAPI schema.

    This class is used as a type annotation for file upload fields in Pydantic models.
    It is a subclass of str, but with additional metadata for OpenAPI schema generation.
    """

    __slots__ = ()

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: Any) -> core_schema.PlainValidatorFunctionSchema:
        """Define the Pydantic core schema for this type.

        This is the recommended way to define custom types in Pydantic v2.

        Args:
            _source_type: Source type information from Pydantic.
            _handler: Handler function from Pydantic.

        Returns:
            A Pydantic core schema for this type.

        """
        return core_schema.with_info_plain_validator_function(
            cls._validate,
            serialization=core_schema.str_schema(),
        )

    @classmethod
    def _validate(cls, v: _T, info: pydantic.ValidationInfo) -> _T:  # noqa: ARG003
        """Validate the value according to Pydantic v2 requirements.

        Args:
            v: The value to validate.
            info: Validation context information from Pydantic.

        Returns:
            The validated value.

        Raises:
            ValueError: If the value is None.

        """
        if v is None:
            msg = "File is required"
            raise ValueError(msg)
        return v

    @classmethod
    def __get_pydantic_json_schema__(cls, _schema_generator: Any, _field_schema: Any) -> dict[str, str]:
        """Define the JSON schema for OpenAPI.

        Args:
            _schema_generator: Schema generator from Pydantic.
            _field_schema: Field schema from Pydantic.

        Returns:
            dict: A dictionary representing the JSON schema for this field.

        """
        return {"type": "string", "format": "binary"}

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:  # noqa: ARG004
        """Create a new instance of the class.

        If a file object is provided, return it directly.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            The file object if provided, otherwise a new instance of the class.

        """
        file_obj = kwargs.get("file")
        if file_obj is not None:
            return file_obj
        return str.__new__(cls, "")


class ImageField(FileField):
    """Field for image file uploads in OpenAPI schema."""


class AudioField(FileField):
    """Field for audio file uploads in OpenAPI schema."""


class VideoField(FileField):
    """Field for video file uploads in OpenAPI schema."""


class PDFField(FileField):
    """Field for PDF file uploads in OpenAPI schema."""


class TextField(FileField):
    """Field for text file uploads in OpenAPI schema."""


class FileUploadModel(BaseModel):
    """Base model for file uploads.

    This model provides a structured way to handle file uploads with validation.
    It automatically validates that the uploaded file is a valid FileStorage instance.

    Attributes:
        file: The uploaded file.

    Examples:
        >>> from flask_x_openapi_schema.models.file_models import FileUploadModel
        >>> # Example usage in a Flask route
        >>> # @openapi_metadata(summary="Upload a file")
        >>> # def post(self, _x_file: FileUploadModel):
        >>> #     return {"filename": _x_file.file.filename}

    """

    file: FileStorage = Field(..., description="The uploaded file")

    model_config = ConfigDict(arbitrary_types_allowed=True, json_schema_extra={"multipart/form-data": True})

    @field_validator("file")
    @classmethod
    def validate_file(cls, v: Any) -> FileStorage:
        """Validate that the file is a FileStorage instance.

        Args:
            v: The value to validate.

        Returns:
            FileStorage: The validated FileStorage instance.

        Raises:
            ValueError: If the value is not a FileStorage instance.

        """
        if not isinstance(v, FileStorage):
            msg = "Not a valid file upload"
            raise ValueError(msg)
        return v


class ImageUploadModel(FileUploadModel):
    """Model for image file uploads with validation.

    This model extends FileUploadModel to provide specific validation for image files.
    It validates file extensions and optionally checks file size.

    Attributes:
        file: The uploaded image file.
        allowed_extensions: List of allowed file extensions.
        max_size: Maximum file size in bytes.

    Examples:
        >>> from flask_x_openapi_schema.models.file_models import ImageUploadModel
        >>> # Example usage in a Flask route
        >>> # @openapi_metadata(summary="Upload an image")
        >>> # def post(self, _x_file: ImageUploadModel):
        >>> #     return {"filename": _x_file.file.filename}

    """

    file: FileStorage = Field(..., description="The uploaded image file")
    allowed_extensions: list[str] = Field(
        default=["jpg", "jpeg", "png", "gif", "webp", "svg"],
        description="Allowed file extensions",
    )
    max_size: int | None = Field(default=None, description="Maximum file size in bytes")

    @field_validator("file")
    @classmethod
    def validate_image_file(cls, v: FileStorage, info: pydantic.ValidationInfo) -> FileStorage:
        """Validate that the file is an image with allowed extension and size.

        Args:
            v: The file to validate.
            info: Validation context information.

        Returns:
            FileStorage: The validated file.

        Raises:
            ValueError: If the file is invalid, has a disallowed extension, or exceeds the maximum size.

        """
        values = info.data

        if not v or not v.filename:
            msg = "No file provided"
            raise ValueError(msg)

        allowed_extensions = values.get("allowed_extensions", ["jpg", "jpeg", "png", "gif", "webp", "svg"])
        if "." in v.filename:
            ext = v.filename.rsplit(".", 1)[1].lower()
            if ext not in allowed_extensions:
                msg = f"File extension '{ext}' not allowed. Allowed extensions: {', '.join(allowed_extensions)}"
                raise ValueError(
                    msg,
                )

        max_size = values.get("max_size")
        if max_size is not None:
            v.seek(0, 2)
            size = v.tell()
            v.seek(0)

            if size > max_size:
                msg = f"File size ({size} bytes) exceeds maximum allowed size ({max_size} bytes)"
                raise ValueError(msg)

        return v


class DocumentUploadModel(FileUploadModel):
    """Model for document file uploads with validation.

    This model extends FileUploadModel to provide specific validation for document files.
    It validates file extensions and optionally checks file size.

    Attributes:
        file: The uploaded document file.
        allowed_extensions: List of allowed file extensions.
        max_size: Maximum file size in bytes.

    """

    file: FileStorage = Field(..., description="The uploaded document file")
    allowed_extensions: list[str] = Field(
        default=["pdf", "doc", "docx", "txt", "rtf", "md"],
        description="Allowed file extensions",
    )
    max_size: int | None = Field(default=None, description="Maximum file size in bytes")

    @field_validator("file")
    @classmethod
    def validate_document_file(cls, v: FileStorage, info: pydantic.ValidationInfo) -> FileStorage:
        """Validate that the file is a document with allowed extension and size.

        Args:
            v: The file to validate.
            info: Validation context information.

        Returns:
            FileStorage: The validated file.

        Raises:
            ValueError: If the file is invalid, has a disallowed extension, or exceeds the maximum size.

        """
        values = info.data

        if not v or not v.filename:
            msg = "No file provided"
            raise ValueError(msg)

        allowed_extensions = values.get("allowed_extensions", ["pdf", "doc", "docx", "txt", "rtf", "md"])
        if "." in v.filename:
            ext = v.filename.rsplit(".", 1)[1].lower()
            if ext not in allowed_extensions:
                msg = f"File extension '{ext}' not allowed. Allowed extensions: {', '.join(allowed_extensions)}"
                raise ValueError(
                    msg,
                )

        max_size = values.get("max_size")
        if max_size is not None:
            v.seek(0, 2)
            size = v.tell()
            v.seek(0)

            if size > max_size:
                msg = f"File size ({size} bytes) exceeds maximum allowed size ({max_size} bytes)"
                raise ValueError(msg)

        return v


class MultipleFileUploadModel(BaseModel):
    """Model for multiple file uploads.

    This model allows uploading multiple files at once and validates that all files
    are valid FileStorage instances.

    Attributes:
        files: List of uploaded files.

    Examples:
        >>> from flask_x_openapi_schema.models.file_models import MultipleFileUploadModel
        >>> # Example usage in a Flask route
        >>> # @openapi_metadata(summary="Upload multiple files")
        >>> # def post(self, _x_file: MultipleFileUploadModel):
        >>> #     return {"filenames": [f.filename for f in _x_file.files]}

    """

    files: list[FileStorage] = Field(..., description="The uploaded files")

    model_config = {"arbitrary_types_allowed": True}

    @field_validator("files")
    @classmethod
    def validate_files(cls, v: list[Any]) -> list[FileStorage]:
        """Validate that all files are FileStorage instances.

        Args:
            v: List of values to validate.

        Returns:
            list[FileStorage]: The validated list of FileStorage instances.

        Raises:
            ValueError: If the list is empty or contains non-FileStorage objects.

        """
        if not v:
            msg = "No files provided"
            raise ValueError(msg)

        for file in v:
            if not isinstance(file, FileStorage):
                msg = "Not a valid file upload"
                raise ValueError(msg)

        return v
