"""Content type handling for OpenAPI schema generation.

This module provides models and utilities for handling different content types
in request and response bodies. It supports dynamic content type selection based
on request parameters and provides a flexible way to define content type handlers.
"""

from collections.abc import Callable
from enum import Enum
from typing import Any, ClassVar

from pydantic import BaseModel, Field

from flask_x_openapi_schema.models.file_models import FileField


class ContentTypeCategory(str, Enum):
    """Categories of content types for OpenAPI schema."""

    JSON = "json"
    FORM = "form"
    MULTIPART = "multipart"
    TEXT = "text"
    BINARY = "binary"
    EVENT_STREAM = "event-stream"
    CUSTOM = "custom"


class EncodingInfo(BaseModel):
    """Encoding information for a content type part.

    This class defines encoding information for a part of a multipart content type.
    It corresponds to the 'encoding' field in OpenAPI specification.

    Attributes:
        content_type: The content type of the part.
        headers: Additional headers for the part.
        style: How the parameter value will be serialized.
        explode: Whether arrays and objects should generate separate parameters.
        allow_reserved: Whether reserved characters should be allowed.

    """

    content_type: str | None = Field(None, description="Content type of this part")
    headers: dict[str, Any] | None = Field(None, description="Additional headers")
    style: str | None = Field(None, description="How parameter values are serialized")
    explode: bool | None = Field(None, description="Whether arrays/objects generate separate parameters")
    allow_reserved: bool | None = Field(None, description="Whether reserved characters are allowed")


class ContentTypeHandler(BaseModel):
    """Handler for a specific content type.

    This class defines how to handle a specific content type for request and response bodies.
    It includes information about the content type, how to extract data from requests,
    and how to generate OpenAPI schema for the content type.

    Attributes:
        content_type: The MIME type (e.g., "application/json").
        category: The category of the content type.
        schema_ref: Reference to the schema in OpenAPI components.
        schema_definition: Inline schema definition.
        description: Description of the content type.
        example: Example of the content type.
        encoding: Encoding information for parts of multipart content.
        extract_func: Custom function to extract data from request.
        serialize_func: Custom function to serialize data for response.

    """

    content_type: str = Field(..., description="MIME type (e.g., 'application/json')")
    category: ContentTypeCategory = Field(..., description="Category of the content type")
    schema_ref: str | None = Field(None, description="Reference to schema in OpenAPI components")
    schema_definition: dict[str, Any] | None = Field(None, description="Inline schema definition")
    description: str | None = Field(None, description="Description of the content type")
    example: Any | None = Field(None, description="Example of the content type")
    encoding: dict[str, EncodingInfo] | None = Field(None, description="Encoding for multipart content")
    extract_func: Callable | None = Field(None, description="Custom function to extract data from request")
    serialize_func: Callable | None = Field(None, description="Custom function to serialize data for response")

    JSON: ClassVar["ContentTypeHandler"]
    MULTIPART_FORM_DATA: ClassVar["ContentTypeHandler"]
    MULTIPART_MIXED: ClassVar["ContentTypeHandler"]
    FORM_URLENCODED: ClassVar["ContentTypeHandler"]
    TEXT_PLAIN: ClassVar["ContentTypeHandler"]
    TEXT_HTML: ClassVar["ContentTypeHandler"]
    TEXT_EVENT_STREAM: ClassVar["ContentTypeHandler"]
    OCTET_STREAM: ClassVar["ContentTypeHandler"]
    IMAGE_PNG: ClassVar["ContentTypeHandler"]
    IMAGE_JPEG: ClassVar["ContentTypeHandler"]


class ContentTypeMapping(BaseModel):
    """Mapping between content types and models.

    This class defines a mapping between content types and the models used to validate
    request or response bodies. It allows for dynamic content type selection based on
    request parameters.

    Attributes:
        content_types: Dictionary mapping content types to models.
        default_content_type: Default content type to use if none is specified.
        content_type_resolver: Function to determine content type based on request.

    """

    content_types: dict[str, type[BaseModel]] = Field(..., description="Mapping of content types to models")
    default_content_type: str = Field(
        "application/json", description="Default content type to use if none is specified"
    )
    content_type_resolver: Callable | None = Field(
        None, description="Function to determine content type based on request"
    )


ContentTypeHandler.JSON = ContentTypeHandler(
    content_type="application/json",
    category=ContentTypeCategory.JSON,
    description="JSON data",
)

ContentTypeHandler.MULTIPART_FORM_DATA = ContentTypeHandler(
    content_type="multipart/form-data",
    category=ContentTypeCategory.MULTIPART,
    description="Multipart form data, typically used for file uploads",
)

ContentTypeHandler.MULTIPART_MIXED = ContentTypeHandler(
    content_type="multipart/mixed",
    category=ContentTypeCategory.MULTIPART,
    description="Multipart mixed content, containing multiple parts with different content types",
)

ContentTypeHandler.FORM_URLENCODED = ContentTypeHandler(
    content_type="application/x-www-form-urlencoded",
    category=ContentTypeCategory.FORM,
    description="URL-encoded form data",
)

ContentTypeHandler.TEXT_PLAIN = ContentTypeHandler(
    content_type="text/plain",
    category=ContentTypeCategory.TEXT,
    description="Plain text",
)

ContentTypeHandler.TEXT_HTML = ContentTypeHandler(
    content_type="text/html",
    category=ContentTypeCategory.TEXT,
    description="HTML content",
)

ContentTypeHandler.TEXT_EVENT_STREAM = ContentTypeHandler(
    content_type="text/event-stream",
    category=ContentTypeCategory.EVENT_STREAM,
    description="Server-sent events stream",
)

ContentTypeHandler.OCTET_STREAM = ContentTypeHandler(
    content_type="application/octet-stream",
    category=ContentTypeCategory.BINARY,
    description="Binary data",
)

ContentTypeHandler.IMAGE_PNG = ContentTypeHandler(
    content_type="image/png",
    category=ContentTypeCategory.BINARY,
    description="PNG image",
)

ContentTypeHandler.IMAGE_JPEG = ContentTypeHandler(
    content_type="image/jpeg",
    category=ContentTypeCategory.BINARY,
    description="JPEG image",
)


def detect_content_type_from_model(model: type[BaseModel]) -> str:
    """Detect appropriate content type based on model fields.

    Args:
        model: The Pydantic model to analyze.

    Returns:
        str: The detected content type.

    """
    has_file_fields = False
    if hasattr(model, "model_fields"):
        for field_info in model.model_fields.values():
            field_type = field_info.annotation

            if isinstance(field_type, type) and issubclass(field_type, FileField):
                has_file_fields = True
                break

            origin = getattr(field_type, "__origin__", None)
            if origin is list or origin is list:
                args = getattr(field_type, "__args__", [])
                if args and isinstance(args[0], type) and issubclass(args[0], FileField):
                    has_file_fields = True
                    break

            field_schema = getattr(field_info, "json_schema_extra", None)
            if field_schema is not None and field_schema.get("format") == "binary":
                has_file_fields = True
                break

    is_multipart = False
    if hasattr(model, "model_config"):
        config = getattr(model, "model_config", {})
        if isinstance(config, dict) and config.get("json_schema_extra", {}).get("multipart/form-data", False):
            is_multipart = True
    elif hasattr(model, "Config") and hasattr(model.Config, "json_schema_extra"):
        config_extra = getattr(model.Config, "json_schema_extra", {})
        is_multipart = config_extra.get("multipart/form-data", False)

    if has_file_fields or is_multipart:
        return "multipart/form-data"
    return "application/json"


class RequestContentTypes(BaseModel):
    """Content types for request bodies.

    This class defines the content types that can be used for request bodies in an API endpoint.
    It allows for multiple content types to be specified, with different models for each.

    Attributes:
        content_types: Dictionary mapping content types to models.
        default_content_type: Default content type to use if none is specified.
        content_type_resolver: Function to determine content type based on request.

    """

    content_types: dict[str, type[BaseModel] | dict[str, Any]] = Field(
        default_factory=dict, description="Mapping of content types to models or schemas"
    )
    default_content_type: str | None = Field(None, description="Default content type to use if none is specified")
    content_type_resolver: Callable | None = Field(
        None, description="Function to determine content type based on request"
    )

    def to_openapi_dict(self) -> dict[str, Any]:
        """Convert to OpenAPI requestBody object.

        Returns:
            dict[str, Any]: OpenAPI requestBody object.

        """
        content = {}
        for content_type, model in self.content_types.items():
            if isinstance(model, type) and issubclass(model, BaseModel):
                content[content_type] = {"schema": {"$ref": f"#/components/schemas/{model.__name__}"}}
            else:
                content[content_type] = {"schema": model}

        return {
            "content": content,
            "required": True,
        }


class ResponseContentTypes(BaseModel):
    """Content types for response bodies.

    This class defines the content types that can be used for response bodies in an API endpoint.
    It allows for multiple content types to be specified, with different models for each.

    Attributes:
        content_types: Dictionary mapping content types to models.
        default_content_type: Default content type to use if none is specified.
        content_type_resolver: Function to determine content type based on request.

    """

    content_types: dict[str, type[BaseModel] | dict[str, Any]] = Field(
        default_factory=dict, description="Mapping of content types to models or schemas"
    )
    default_content_type: str | None = Field(None, description="Default content type to use if none is specified")
    content_type_resolver: Callable | None = Field(
        None, description="Function to determine content type based on request"
    )

    def to_openapi_dict(self) -> dict[str, Any]:
        """Convert to OpenAPI content object.

        Returns:
            dict[str, Any]: OpenAPI content object.

        """
        content = {}
        for content_type, model in self.content_types.items():
            if isinstance(model, type) and issubclass(model, BaseModel):
                content[content_type] = {"schema": {"$ref": f"#/components/schemas/{model.__name__}"}}
            else:
                content[content_type] = {"schema": model}

        return content
