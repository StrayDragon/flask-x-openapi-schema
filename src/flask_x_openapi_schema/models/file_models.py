"""
Pydantic models for file uploads in OpenAPI.

These models provide a structured way to handle file uploads with validation and type hints.
The models are designed to work with OpenAPI 3.0.x specification.
"""

from enum import Enum
from typing import Any, List, Optional

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


class FileField(str):
    """Field for file uploads in OpenAPI schema.

    This class is used as a type annotation for file upload fields in Pydantic models.
    It is a subclass of str, but with additional metadata for OpenAPI schema generation.
    """

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler):
        """Define the Pydantic core schema for this type.

        This is the recommended way to define custom types in Pydantic v2.
        """
        return core_schema.with_info_plain_validator_function(
            cls._validate,
            serialization=core_schema.str_schema(),
        )

    @classmethod
    def _validate(cls, v, info):
        """Validate the value according to Pydantic v2 requirements."""
        if v is None:
            raise ValueError("File is required")
        return v

    @classmethod
    def __get_pydantic_json_schema__(cls, _schema_generator, _field_schema):
        """Define the JSON schema for OpenAPI."""
        return {"type": "string", "format": "binary"}

    def __new__(cls, *args, **kwargs):
        """Create a new instance of the class.

        If a file object is provided, return it directly.
        """
        file_obj = kwargs.get("file")
        if file_obj is not None:
            return file_obj
        return str.__new__(cls, "")


class ImageField(FileField):
    """Field for image file uploads in OpenAPI schema."""

    pass


class AudioField(FileField):
    """Field for audio file uploads in OpenAPI schema."""

    pass


class VideoField(FileField):
    """Field for video file uploads in OpenAPI schema."""

    pass


class PDFField(FileField):
    """Field for PDF file uploads in OpenAPI schema."""

    pass


class TextField(FileField):
    """Field for text file uploads in OpenAPI schema."""

    pass


class FileUploadModel(BaseModel):
    """Base model for file uploads."""

    file: FileStorage = Field(..., description="The uploaded file")

    # Allow arbitrary types for FileStorage
    model_config = ConfigDict(
        arbitrary_types_allowed=True, json_schema_extra={"multipart/form-data": True}
    )

    @field_validator("file")
    def validate_file(cls, v: Any) -> FileStorage:
        """Validate that the file is a FileStorage instance."""
        if not isinstance(v, FileStorage):
            raise ValueError("Not a valid file upload")
        return v


class ImageUploadModel(FileUploadModel):
    """Model for image file uploads with validation."""

    file: FileStorage = Field(..., description="The uploaded image file")
    allowed_extensions: List[str] = Field(
        default=["jpg", "jpeg", "png", "gif", "webp", "svg"],
        description="Allowed file extensions",
    )
    max_size: Optional[int] = Field(
        default=None, description="Maximum file size in bytes"
    )

    @field_validator("file")
    def validate_image_file(cls, v: FileStorage, info) -> FileStorage:
        """Validate that the file is an image with allowed extension and size."""
        # Get values from info.data
        values = info.data
        # Check if it's a valid file
        if not v or not v.filename:
            raise ValueError("No file provided")

        # Check file extension
        allowed_extensions = values.get(
            "allowed_extensions", ["jpg", "jpeg", "png", "gif", "webp", "svg"]
        )
        if "." in v.filename:
            ext = v.filename.rsplit(".", 1)[1].lower()
            if ext not in allowed_extensions:
                raise ValueError(
                    f"File extension '{ext}' not allowed. Allowed extensions: {', '.join(allowed_extensions)}"
                )

        # Check file size if max_size is specified
        max_size = values.get("max_size")
        if max_size is not None:
            v.seek(0, 2)  # Seek to the end of the file
            size = v.tell()  # Get the position (size)
            v.seek(0)  # Rewind to the beginning

            if size > max_size:
                raise ValueError(
                    f"File size ({size} bytes) exceeds maximum allowed size ({max_size} bytes)"
                )

        return v


class DocumentUploadModel(FileUploadModel):
    """Model for document file uploads with validation."""

    file: FileStorage = Field(..., description="The uploaded document file")
    allowed_extensions: List[str] = Field(
        default=["pdf", "doc", "docx", "txt", "rtf", "md"],
        description="Allowed file extensions",
    )
    max_size: Optional[int] = Field(
        default=None, description="Maximum file size in bytes"
    )

    @field_validator("file")
    def validate_document_file(cls, v: FileStorage, info) -> FileStorage:
        """Validate that the file is a document with allowed extension and size."""
        # Get values from info.data
        values = info.data
        # Check if it's a valid file
        if not v or not v.filename:
            raise ValueError("No file provided")

        # Check file extension
        allowed_extensions = values.get(
            "allowed_extensions", ["pdf", "doc", "docx", "txt", "rtf", "md"]
        )
        if "." in v.filename:
            ext = v.filename.rsplit(".", 1)[1].lower()
            if ext not in allowed_extensions:
                raise ValueError(
                    f"File extension '{ext}' not allowed. Allowed extensions: {', '.join(allowed_extensions)}"
                )

        # Check file size if max_size is specified
        max_size = values.get("max_size")
        if max_size is not None:
            v.seek(0, 2)  # Seek to the end of the file
            size = v.tell()  # Get the position (size)
            v.seek(0)  # Rewind to the beginning

            if size > max_size:
                raise ValueError(
                    f"File size ({size} bytes) exceeds maximum allowed size ({max_size} bytes)"
                )

        return v


class MultipleFileUploadModel(BaseModel):
    """Model for multiple file uploads."""

    files: List[FileStorage] = Field(..., description="The uploaded files")

    # Allow arbitrary types for FileStorage
    model_config = {"arbitrary_types_allowed": True}

    @field_validator("files")
    def validate_files(cls, v: List[Any]) -> List[FileStorage]:
        """Validate that all files are FileStorage instances."""
        if not v:
            raise ValueError("No files provided")

        for file in v:
            if not isinstance(file, FileStorage):
                raise ValueError("Not a valid file upload")

        return v
