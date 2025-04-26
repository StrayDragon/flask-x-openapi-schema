"""Pydantic models for file uploads in OpenAPI.

These models provide a structured way to handle file uploads with validation and type hints.
The models are designed to work with OpenAPI 3.0.x specification.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_core import core_schema
from werkzeug.datastructures import FileStorage


class FileType(str, Enum):
    """Enumeration of file types for OpenAPI schema."""

    BINARY = "binary"  # For any binary file
    IMAGE = "image"  # For image files
    AUDIO = "audio"  # For audio files
    VIDEO = "video"  # For video files
    PDF = "pdf"  # For PDF files
    TEXT = "text"  # For text files


class FileField(str):  # noqa: SLOT000
    """Field for file uploads in OpenAPI schema.

    This class is used as a type annotation for file upload fields in Pydantic models.
    It is a subclass of str, but with additional metadata for OpenAPI schema generation.
    """

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler):  # noqa: ANN001, ANN206
        """Define the Pydantic core schema for this type.

        This is the recommended way to define custom types in Pydantic v2.
        """
        return core_schema.with_info_plain_validator_function(
            cls._validate,
            serialization=core_schema.str_schema(),
        )

    @classmethod
    def _validate(cls, v, info):  # noqa: ANN001, ANN206, ARG003
        """Validate the value according to Pydantic v2 requirements."""
        if v is None:
            msg = "File is required"
            raise ValueError(msg)
        return v

    @classmethod
    def __get_pydantic_json_schema__(cls, _schema_generator, _field_schema):  # noqa: ANN001, ANN206
        """Define the JSON schema for OpenAPI."""
        return {"type": "string", "format": "binary"}

    def __new__(cls, *args, **kwargs):  # noqa: ANN204, ARG004
        """Create a new instance of the class.

        If a file object is provided, return it directly.
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

    :param file: The uploaded file
    :type file: FileStorage

    Example:
        >>> from flask_x_openapi_schema import FileUploadModel
        >>>
        >>> @openapi_metadata(summary="Upload a file")
        >>> def post(self, _x_file: FileUploadModel):
        ...     # File is automatically injected and validated
        ...     return {"filename": _x_file.file.filename}

    """

    file: FileStorage = Field(..., description="The uploaded file")

    # Allow arbitrary types for FileStorage
    model_config = ConfigDict(arbitrary_types_allowed=True, json_schema_extra={"multipart/form-data": True})

    @field_validator("file")
    @classmethod
    def validate_file(cls, v: Any) -> FileStorage:
        """Validate that the file is a FileStorage instance.

        :param v: The value to validate
        :type v: Any
        :return: The validated FileStorage instance
        :rtype: FileStorage
        :raises ValueError: If the value is not a FileStorage instance
        """
        if not isinstance(v, FileStorage):
            msg = "Not a valid file upload"
            raise ValueError(msg)  # noqa: TRY004
        return v


class ImageUploadModel(FileUploadModel):
    """Model for image file uploads with validation.

    This model extends FileUploadModel to provide specific validation for image files.
    It validates file extensions and optionally checks file size.

    :param file: The uploaded image file
    :type file: FileStorage
    :param allowed_extensions: List of allowed file extensions (default: ["jpg", "jpeg", "png", "gif", "webp", "svg"])
    :type allowed_extensions: List[str]
    :param max_size: Maximum file size in bytes (default: None)
    :type max_size: Optional[int]

    Example:
        >>> from flask_x_openapi_schema import ImageUploadModel
        >>>
        >>> @openapi_metadata(summary="Upload an image")
        >>> def post(self, _x_file: ImageUploadModel):
        ...     # Image file is automatically injected and validated
        ...     return {"filename": _x_file.file.filename}

    """

    file: FileStorage = Field(..., description="The uploaded image file")
    allowed_extensions: list[str] = Field(
        default=["jpg", "jpeg", "png", "gif", "webp", "svg"],
        description="Allowed file extensions",
    )
    max_size: int | None = Field(default=None, description="Maximum file size in bytes")

    @field_validator("file")
    @classmethod
    def validate_image_file(cls, v: FileStorage, info) -> FileStorage:  # noqa: ANN001
        """Validate that the file is an image with allowed extension and size."""
        # Get values from info.data
        values = info.data
        # Check if it's a valid file
        if not v or not v.filename:
            msg = "No file provided"
            raise ValueError(msg)

        # Check file extension
        allowed_extensions = values.get("allowed_extensions", ["jpg", "jpeg", "png", "gif", "webp", "svg"])
        if "." in v.filename:
            ext = v.filename.rsplit(".", 1)[1].lower()
            if ext not in allowed_extensions:
                msg = f"File extension '{ext}' not allowed. Allowed extensions: {', '.join(allowed_extensions)}"
                raise ValueError(
                    msg,
                )

        # Check file size if max_size is specified
        max_size = values.get("max_size")
        if max_size is not None:
            v.seek(0, 2)  # Seek to the end of the file
            size = v.tell()  # Get the position (size)
            v.seek(0)  # Rewind to the beginning

            if size > max_size:
                msg = f"File size ({size} bytes) exceeds maximum allowed size ({max_size} bytes)"
                raise ValueError(msg)

        return v


class DocumentUploadModel(FileUploadModel):
    """Model for document file uploads with validation."""

    file: FileStorage = Field(..., description="The uploaded document file")
    allowed_extensions: list[str] = Field(
        default=["pdf", "doc", "docx", "txt", "rtf", "md"],
        description="Allowed file extensions",
    )
    max_size: int | None = Field(default=None, description="Maximum file size in bytes")

    @field_validator("file")
    @classmethod
    def validate_document_file(cls, v: FileStorage, info) -> FileStorage:  # noqa: ANN001
        """Validate that the file is a document with allowed extension and size."""
        # Get values from info.data
        values = info.data
        # Check if it's a valid file
        if not v or not v.filename:
            msg = "No file provided"
            raise ValueError(msg)

        # Check file extension
        allowed_extensions = values.get("allowed_extensions", ["pdf", "doc", "docx", "txt", "rtf", "md"])
        if "." in v.filename:
            ext = v.filename.rsplit(".", 1)[1].lower()
            if ext not in allowed_extensions:
                msg = f"File extension '{ext}' not allowed. Allowed extensions: {', '.join(allowed_extensions)}"
                raise ValueError(
                    msg,
                )

        # Check file size if max_size is specified
        max_size = values.get("max_size")
        if max_size is not None:
            v.seek(0, 2)  # Seek to the end of the file
            size = v.tell()  # Get the position (size)
            v.seek(0)  # Rewind to the beginning

            if size > max_size:
                msg = f"File size ({size} bytes) exceeds maximum allowed size ({max_size} bytes)"
                raise ValueError(msg)

        return v


class MultipleFileUploadModel(BaseModel):
    """Model for multiple file uploads.

    This model allows uploading multiple files at once and validates that all files
    are valid FileStorage instances.

    :param files: List of uploaded files
    :type files: List[FileStorage]

    Example:
        >>> from flask_x_openapi_schema import MultipleFileUploadModel
        >>>
        >>> @openapi_metadata(summary="Upload multiple files")
        >>> def post(self, _x_file: MultipleFileUploadModel):
        ...     # Files are automatically injected and validated
        ...     return {"filenames": [f.filename for f in _x_file.files]}

    """

    files: list[FileStorage] = Field(..., description="The uploaded files")

    # Allow arbitrary types for FileStorage
    model_config = {"arbitrary_types_allowed": True}

    @field_validator("files")
    @classmethod
    def validate_files(cls, v: list[Any]) -> list[FileStorage]:
        """Validate that all files are FileStorage instances.

        :param v: List of values to validate
        :type v: List[Any]
        :return: The validated list of FileStorage instances
        :rtype: List[FileStorage]
        :raises ValueError: If the list is empty or contains non-FileStorage objects
        """
        if not v:
            msg = "No files provided"
            raise ValueError(msg)

        for file in v:
            if not isinstance(file, FileStorage):
                msg = "Not a valid file upload"
                raise ValueError(msg)  # noqa: TRY004

        return v
