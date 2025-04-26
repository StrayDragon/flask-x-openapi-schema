"""Common models for Flask-X-OpenAPI-Schema examples.

This module contains Pydantic models used in both Flask and Flask-RESTful examples.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from flask_x_openapi_schema import BaseRespModel, I18nStr
from flask_x_openapi_schema.models.file_models import (
    AudioField,
    ImageField,
    PDFField,
    VideoField,
)


class ProductCategory(str, Enum):
    """Product category enumeration."""

    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    BOOKS = "books"
    HOME = "home"
    FOOD = "food"
    OTHER = "other"


class ProductStatus(str, Enum):
    """Product status enumeration."""

    AVAILABLE = "available"
    OUT_OF_STOCK = "out_of_stock"
    DISCONTINUED = "discontinued"


class ProductRequest(BaseModel):
    """Request model for creating or updating a product."""

    name: str = Field(..., description="Product name")
    description: str = Field(..., description="Product description")
    price: float = Field(..., description="Product price", gt=0)
    category: ProductCategory = Field(..., description="Product category")
    tags: list[str] = Field(default=[], description="Product tags")
    in_stock: bool = Field(True, description="Whether the product is in stock")
    quantity: int = Field(0, description="Available quantity", ge=0)
    attributes: dict[str, Any] = Field(default={}, description="Additional product attributes")


class ProductQueryParams(BaseModel):
    """Query parameters for product endpoints."""

    category: ProductCategory | None = Field(None, description="Filter by category")
    min_price: float | None = Field(None, description="Minimum price", gt=0)
    max_price: float | None = Field(None, description="Maximum price", gt=0)
    in_stock: bool | None = Field(None, description="Filter by stock status")
    sort_by: str | None = Field(None, description="Sort field")
    sort_order: str | None = Field("asc", description="Sort order (asc or desc)")
    limit: int | None = Field(10, description="Maximum number of results", ge=1, le=100)
    offset: int | None = Field(0, description="Result offset for pagination", ge=0)


class ProductResponse(BaseRespModel):
    """Response model for product endpoints."""

    id: str = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
    description: str = Field(..., description="Product description")
    price: float = Field(..., description="Product price")
    category: ProductCategory = Field(..., description="Product category")
    status: ProductStatus = Field(..., description="Product status")
    tags: list[str] = Field(default=[], description="Product tags")
    in_stock: bool = Field(..., description="Whether the product is in stock")
    quantity: int = Field(..., description="Available quantity")
    attributes: dict[str, Any] = Field(default={}, description="Additional product attributes")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")


class ErrorResponse(BaseRespModel):
    """Error response model."""

    error_code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: dict[str, Any] | None = Field(None, description="Error details")


# File upload models


class ProductImageUpload(BaseModel):
    """Model for product image uploads."""

    file: ImageField = Field(..., description="The image file to upload")
    description: str | None = Field(None, description="Image description")
    is_primary: str | None = Field("false", description="Whether this is the primary product image (true/false)")
    allowed_extensions: str | None = Field(
        default="jpg,jpeg,png,gif,webp,svg",
        description="Allowed file extensions (comma-separated)",
    )

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_schema_extra={
            "multipart/form-data": True,  # Indicate this model is for multipart/form-data
        },
    )

    @field_validator("is_primary")
    @classmethod
    def parse_is_primary(cls, v):
        """Convert string boolean to actual boolean."""
        if v is None:
            return False
        if isinstance(v, str):
            return v.lower() in ("true", "t", "yes", "y", "1")
        return bool(v)

    @field_validator("allowed_extensions")
    @classmethod
    def parse_allowed_extensions(cls, v):
        """Convert comma-separated string to list if needed."""
        if v is None:
            return ["jpg", "jpeg", "png", "gif", "webp", "svg"]
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v


class ProductDocumentUpload(BaseModel):
    """Model for product document uploads (manuals, specifications, etc.)."""

    file: PDFField = Field(..., description="The document file to upload")
    title: str = Field(..., description="Document title")
    document_type: str = Field(..., description="Type of document (manual, spec sheet, etc.)")
    allowed_extensions: str | None = Field(
        default="pdf,doc,docx,txt,rtf,md",
        description="Allowed file extensions (comma-separated)",
    )

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_schema_extra={
            "multipart/form-data": True,  # Indicate this model is for multipart/form-data
        },
    )

    @field_validator("allowed_extensions")
    @classmethod
    def parse_allowed_extensions(cls, v):
        """Convert comma-separated string to list if needed."""
        if v is None:
            return ["pdf", "doc", "docx", "txt", "rtf", "md"]
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v


class ProductAudioUpload(BaseModel):
    """Model for product audio uploads (sound samples, etc.)."""

    file: AudioField = Field(..., description="The audio file to upload")
    title: str = Field(..., description="Audio title")
    duration_seconds: str | None = Field(None, description="Duration in seconds")
    allowed_extensions: str | None = Field(
        default="mp3,wav,ogg,m4a,flac",
        description="Allowed file extensions (comma-separated)",
    )

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_schema_extra={
            "multipart/form-data": True,  # Indicate this model is for multipart/form-data
        },
    )

    @field_validator("duration_seconds")
    @classmethod
    def parse_duration_seconds(cls, v):
        """Convert string number to integer."""
        if v is None or v == "":
            return None
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                return None
        return v

    @field_validator("allowed_extensions")
    @classmethod
    def parse_allowed_extensions(cls, v):
        """Convert comma-separated string to list if needed."""
        if v is None:
            return ["mp3", "wav", "ogg", "m4a", "flac"]
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v


class ProductVideoUpload(BaseModel):
    """Model for product video uploads (demos, tutorials, etc.)."""

    file: VideoField = Field(..., description="The video file to upload")
    title: str = Field(..., description="Video title")
    duration_seconds: str | None = Field(None, description="Duration in seconds")
    resolution: str | None = Field(None, description="Video resolution (e.g., 1080p, 4K)")
    allowed_extensions: str | None = Field(
        default="mp4,mov,avi,mkv,webm",
        description="Allowed file extensions (comma-separated)",
    )

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_schema_extra={
            "multipart/form-data": True,  # Indicate this model is for multipart/form-data
        },
    )

    @field_validator("duration_seconds")
    @classmethod
    def parse_duration_seconds(cls, v):
        """Convert string number to integer."""
        if v is None or v == "":
            return None
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                return None
        return v

    @field_validator("allowed_extensions")
    @classmethod
    def parse_allowed_extensions(cls, v):
        """Convert comma-separated string to list if needed."""
        if v is None:
            return ["mp4", "mov", "avi", "mkv", "webm"]
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v


class FileResponse(BaseRespModel):
    """Response model for file metadata."""

    id: str = Field(..., description="File ID")
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="File content type")
    size: int = Field(..., description="File size in bytes")
    upload_date: datetime = Field(..., description="Upload timestamp")
    url: str = Field(..., description="URL to download the file")


# Internationalization examples
product_descriptions = {
    "electronics": I18nStr({"en-US": "Electronic devices and accessories", "zh-Hans": "电子设备和配件"}),
    "clothing": I18nStr({"en-US": "Clothing and fashion items", "zh-Hans": "服装和时尚物品"}),
    "books": I18nStr({"en-US": "Books and publications", "zh-Hans": "书籍和出版物"}),
    "home": I18nStr({"en-US": "Home goods and furniture", "zh-Hans": "家居用品和家具"}),
    "food": I18nStr({"en-US": "Food and beverages", "zh-Hans": "食品和饮料"}),
    "other": I18nStr({"en-US": "Other miscellaneous items", "zh-Hans": "其他杂项物品"}),
}
