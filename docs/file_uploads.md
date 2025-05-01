# File Upload Support in Flask-X-OpenAPI-Schema

This document explains how to use the file upload functionality in Flask-X-OpenAPI-Schema with both Flask and Flask-RESTful applications.

## Overview

Flask-X-OpenAPI-Schema provides built-in support for file uploads, making it easy to handle file uploads in your API endpoints. The library includes:

1. **File Upload Models**: Pre-defined Pydantic models for common file types
2. **Automatic File Injection**: Files are automatically injected into your handler functions
3. **OpenAPI Schema Generation**: File upload fields are properly documented in the OpenAPI schema
4. **Validation**: File uploads can be validated based on content type, size, etc.

## File Upload Models

Flask-X-OpenAPI-Schema provides several pre-defined file upload models:

```python
from flask_x_openapi_schema import (
    FileUploadModel,          # Generic file upload
    ImageUploadModel,         # Image files (png, jpg, etc.)
    DocumentUploadModel,      # Document files (pdf, docx, etc.)
    AudioUploadModel,         # Audio files (mp3, wav, etc.)
    VideoUploadModel,         # Video files (mp4, avi, etc.)
)
```

You can also create custom file upload models by extending the base `FileUploadModel` class:

```python
from flask_x_openapi_schema import FileUploadModel
from pydantic import Field

class CustomFileUpload(FileUploadModel):
    description: str = Field(..., description="File description")
    category: str = Field(..., description="File category")

    # Customize allowed content types
    allowed_content_types = ["application/pdf", "application/msword"]

    # Customize maximum file size (in bytes)
    max_size = 10 * 1024 * 1024  # 10 MB
```

## Basic Usage

### With Flask.MethodView

```python
from flask.views import MethodView
from flask_x_openapi_schema.x.flask import openapi_metadata, OpenAPIMethodViewMixin
from flask_x_openapi_schema import ImageUploadModel, OpenAPIMetaResponse, OpenAPIMetaResponseItem

class FileUploadView(OpenAPIMethodViewMixin, MethodView):
    @openapi_metadata(
        summary="Upload an image",
        description="Upload an image file",
        tags=["files"],
        operation_id="uploadImage",
        responses=OpenAPIMetaResponse(
            responses={
                "201": OpenAPIMetaResponseItem(
                    model=FileResponse,
                    description="File uploaded successfully",
                ),
                "400": OpenAPIMetaResponseItem(
                    model=ErrorResponse,
                    description="Invalid file",
                ),
            }
        ),
    )
    def post(self, _x_file: ImageUploadModel):
        # The file is automatically injected into _x_file.file
        file = _x_file.file

        # Access file properties
        filename = file.filename
        content_type = file.content_type

        # Save the file
        file.save(f"uploads/{filename}")

        # Return response
        return {
            "filename": filename,
            "content_type": content_type,
            "size": os.path.getsize(f"uploads/{filename}"),
        }, 201

# Register the view
FileUploadView.register_to_blueprint(blueprint, "/upload", "file_upload")
```

### With Flask-RESTful

```python
from flask_restful import Resource
from flask_x_openapi_schema.x.flask_restful import openapi_metadata
from flask_x_openapi_schema import DocumentUploadModel, OpenAPIMetaResponse, OpenAPIMetaResponseItem

class DocumentUploadResource(Resource):
    @openapi_metadata(
        summary="Upload a document",
        description="Upload a document file (PDF, DOCX, etc.)",
        tags=["files"],
        operation_id="uploadDocument",
        responses=OpenAPIMetaResponse(
            responses={
                "201": OpenAPIMetaResponseItem(
                    model=FileResponse,
                    description="File uploaded successfully",
                ),
                "400": OpenAPIMetaResponseItem(
                    model=ErrorResponse,
                    description="Invalid file",
                ),
            }
        ),
    )
    def post(self, _x_file: DocumentUploadModel):
        # The file is automatically injected into _x_file.file
        file = _x_file.file

        # Access file properties
        filename = file.filename
        content_type = file.content_type

        # Save the file
        file.save(f"uploads/{filename}")

        # Return response
        return {
            "filename": filename,
            "content_type": content_type,
            "size": os.path.getsize(f"uploads/{filename}"),
        }, 201

# Register the resource
api.add_resource(DocumentUploadResource, "/upload/document")
```

## Advanced Usage

### Custom File Parameter Names

By default, Flask-X-OpenAPI-Schema uses the parameter name `_x_file` for file uploads. You can customize this by using a different parameter name with the `_x_file_` prefix:

```python
@openapi_metadata(
    summary="Upload a profile picture",
    # ...
)
def post(self, _x_file_profile_picture: ImageUploadModel):
    # The file is automatically injected into _x_file_profile_picture.file
    file = _x_file_profile_picture.file
    # ...
```

### Multiple File Uploads

You can handle multiple file uploads by using different parameter names:

```python
@openapi_metadata(
    summary="Upload product files",
    # ...
)
def post(
    self,
    _x_file_image: ImageUploadModel,
    _x_file_document: DocumentUploadModel,
    _x_file_video: VideoUploadModel
):
    # Access each file
    image = _x_file_image.file
    document = _x_file_document.file
    video = _x_file_video.file

    # Process files
    # ...
```

### File Validation

File upload models include built-in validation for content type and file size:

```python
from flask_x_openapi_schema import FileUploadModel
from pydantic import Field, validator

class StrictPDFUpload(FileUploadModel):
    title: str = Field(..., description="Document title")

    # Define allowed content types
    allowed_content_types = ["application/pdf"]

    # Define maximum file size (5 MB)
    max_size = 5 * 1024 * 1024

    # Custom validation
    @validator("file")
    def validate_file(cls, file):
        if not file or not hasattr(file, "filename"):
            raise ValueError("File is required")

        if not file.filename.lower().endswith(".pdf"):
            raise ValueError("Only PDF files are allowed")

        return file
```

### Custom File Processing

You can add custom processing logic to your file upload models:

```python
from flask_x_openapi_schema import ImageUploadModel
from PIL import Image
import io

class ResizedImageUpload(ImageUploadModel):
    width: int = Field(..., description="Target width")
    height: int = Field(..., description="Target height")

    def process_image(self):
        """Resize the uploaded image to the specified dimensions."""
        if not self.file:
            return None

        # Read the image
        img = Image.open(self.file)

        # Resize the image
        resized_img = img.resize((self.width, self.height))

        # Save to a buffer
        buffer = io.BytesIO()
        resized_img.save(buffer, format=img.format)
        buffer.seek(0)

        return buffer
```

## OpenAPI Schema Generation

Flask-X-OpenAPI-Schema automatically generates the correct OpenAPI schema for file upload endpoints. File upload fields are rendered as file upload buttons in Swagger UI, making it easy for users to test your API.

### Example Schema

```yaml
paths:
  /upload:
    post:
      summary: Upload an image
      description: Upload an image file
      tags:
        - files
      operationId: uploadImage
      requestBody:
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                file:
                  type: string
                  format: binary
                  description: Image file to upload
      responses:
        '201':
          description: File uploaded successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/FileResponse'
        '400':
          description: Invalid file
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
```

## Complete Example

Here's a complete example of a file upload endpoint with Flask.MethodView:

```python
import os
import uuid
from pathlib import Path
from flask import Flask, Blueprint, url_for
from flask.views import MethodView
from flask_x_openapi_schema.x.flask import openapi_metadata, OpenAPIMethodViewMixin
from flask_x_openapi_schema import (
    ImageUploadModel,
    OpenAPIMetaResponse,
    OpenAPIMetaResponseItem,
    BaseRespModel,
)
from pydantic import Field
from datetime import datetime

# Create uploads directory
uploads_dir = Path("uploads")
uploads_dir.mkdir(exist_ok=True)

# Define response model
class FileResponse(BaseRespModel):
    id: str = Field(..., description="File ID")
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="File content type")
    size: int = Field(..., description="File size in bytes")
    upload_date: datetime = Field(..., description="Upload date and time")
    url: str = Field(..., description="File download URL")

# Define error response model
class ErrorResponse(BaseRespModel):
    error_code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")

# Define custom image upload model
class ProductImageUpload(ImageUploadModel):
    description: str = Field(..., description="Image description")
    is_primary: bool = Field(False, description="Whether this is the primary product image")

# Create a view for image uploads
class ProductImageView(OpenAPIMethodViewMixin, MethodView):
    @openapi_metadata(
        summary="Upload a product image",
        description="Upload an image for a specific product",
        tags=["files"],
        operation_id="uploadProductImage",
        responses=OpenAPIMetaResponse(
            responses={
                "201": OpenAPIMetaResponseItem(
                    model=FileResponse,
                    description="Image uploaded successfully",
                ),
                "400": OpenAPIMetaResponseItem(
                    model=ErrorResponse,
                    description="Invalid request data",
                ),
                "404": OpenAPIMetaResponseItem(
                    model=ErrorResponse,
                    description="Product not found",
                ),
            }
        ),
    )
    def post(self, product_id: str, _x_file_image: ProductImageUpload):
        # The file is automatically injected into _x_file_image.file
        file = _x_file_image.file

        # Check if product exists (in a real app, you would query a database)
        if product_id not in ["123", "456", "789"]:
            error = ErrorResponse(
                error_code="PRODUCT_NOT_FOUND",
                message=f"Product with ID {product_id} not found",
            )
            return error.to_response(404)

        # Save the file
        file_id = str(uuid.uuid4())
        filename = file.filename
        content_type = file.content_type or "application/octet-stream"

        # Create product-specific directory
        product_dir = uploads_dir / product_id
        product_dir.mkdir(exist_ok=True)

        # Save file to disk
        file_path = product_dir / f"{file_id}_{filename}"
        file.save(file_path)

        # Get file size
        size = os.path.getsize(file_path)

        # Create response
        response = FileResponse(
            id=file_id,
            filename=filename,
            content_type=content_type,
            size=size,
            upload_date=datetime.now(),
            url=url_for("api.download_file", file_id=file_id, _external=True),
        )

        return response.to_response(201)
```

## Working Examples

For complete working examples of file uploads, check out the example applications in the repository:

- [Flask MethodView File Upload Example](https://github.com/StrayDragon/flask-x-openapi-schema/tree/main/examples/flask/app.py#L461-L520): Demonstrates image, document, audio, and video uploads using Flask.MethodView
- [Flask-RESTful File Upload Example](https://github.com/StrayDragon/flask-x-openapi-schema/tree/main/examples/flask_restful/app.py#L534-L593): Demonstrates image, document, audio, and video uploads using Flask-RESTful

These examples show how to:

- Define file upload models for different file types
- Handle file uploads with validation
- Save uploaded files to disk
- Return appropriate responses
- Generate OpenAPI schema for file upload endpoints

You can run the examples using the provided justfile commands:

```bash
# Run the Flask MethodView example
just run-example-flask

# Run the Flask-RESTful example
just run-example-flask-restful
```

## Conclusion

Flask-X-OpenAPI-Schema provides comprehensive support for file uploads in both Flask and Flask-RESTful applications. By using the built-in file upload models and automatic file injection, you can easily handle file uploads in your API endpoints with minimal code. The library also generates the correct OpenAPI schema for file upload endpoints, making it easy for users to test your API.
