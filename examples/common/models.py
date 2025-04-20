"""
Common models for Flask-X-OpenAPI-Schema examples.

This module contains Pydantic models used in both Flask and Flask-RESTful examples.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field

from flask_x_openapi_schema import BaseRespModel, I18nStr


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
    tags: List[str] = Field(default=[], description="Product tags")
    in_stock: bool = Field(True, description="Whether the product is in stock")
    quantity: int = Field(0, description="Available quantity", ge=0)
    attributes: Dict[str, Any] = Field(
        default={}, description="Additional product attributes"
    )


class ProductQueryParams(BaseModel):
    """Query parameters for product endpoints."""

    category: Optional[ProductCategory] = Field(None, description="Filter by category")
    min_price: Optional[float] = Field(None, description="Minimum price", gt=0)
    max_price: Optional[float] = Field(None, description="Maximum price", gt=0)
    in_stock: Optional[bool] = Field(None, description="Filter by stock status")
    sort_by: Optional[str] = Field(None, description="Sort field")
    sort_order: Optional[str] = Field("asc", description="Sort order (asc or desc)")
    limit: Optional[int] = Field(
        10, description="Maximum number of results", ge=1, le=100
    )
    offset: Optional[int] = Field(0, description="Result offset for pagination", ge=0)


class ProductResponse(BaseRespModel):
    """Response model for product endpoints."""

    id: str = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
    description: str = Field(..., description="Product description")
    price: float = Field(..., description="Product price")
    category: ProductCategory = Field(..., description="Product category")
    status: ProductStatus = Field(..., description="Product status")
    tags: List[str] = Field(default=[], description="Product tags")
    in_stock: bool = Field(..., description="Whether the product is in stock")
    quantity: int = Field(..., description="Available quantity")
    attributes: Dict[str, Any] = Field(
        default={}, description="Additional product attributes"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")


class ErrorResponse(BaseRespModel):
    """Error response model."""

    error_code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")


# File upload models

class ProductImageUpload(BaseModel):
    """Model for product image uploads."""
    file: str = Field(
        ...,
        description="The image file to upload",
        format="binary",  # This tells Swagger UI to render a file upload button
    )
    description: Optional[str] = Field(None, description="Image description")
    is_primary: bool = Field(False, description="Whether this is the primary product image")
    allowed_extensions: List[str] = Field(
        default=["jpg", "jpeg", "png", "gif", "webp", "svg"],
        description="Allowed file extensions",
    )


class ProductDocumentUpload(BaseModel):
    """Model for product document uploads (manuals, specifications, etc.)."""
    file: str = Field(
        ...,
        description="The document file to upload",
        format="binary",  # This tells Swagger UI to render a file upload button
    )
    title: str = Field(..., description="Document title")
    document_type: str = Field(..., description="Type of document (manual, spec sheet, etc.)")
    allowed_extensions: List[str] = Field(
        default=["pdf", "doc", "docx", "txt", "rtf", "md"],
        description="Allowed file extensions",
    )


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
    "electronics": I18nStr(
        {"en-US": "Electronic devices and accessories", "zh-Hans": "电子设备和配件"}
    ),
    "clothing": I18nStr(
        {"en-US": "Clothing and fashion items", "zh-Hans": "服装和时尚物品"}
    ),
    "books": I18nStr({"en-US": "Books and publications", "zh-Hans": "书籍和出版物"}),
    "home": I18nStr({"en-US": "Home goods and furniture", "zh-Hans": "家居用品和家具"}),
    "food": I18nStr({"en-US": "Food and beverages", "zh-Hans": "食品和饮料"}),
    "other": I18nStr({"en-US": "Other miscellaneous items", "zh-Hans": "其他杂项物品"}),
}
