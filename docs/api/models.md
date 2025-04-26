# Models API Reference

This section provides detailed documentation for the models components of Flask-X-OpenAPI-Schema.

## Base Models

The base models module provides base classes for response models.

```python
from flask_x_openapi_schema.models.base import BaseRespModel
from pydantic import Field

class ItemResponse(BaseRespModel):
    id: str = Field(..., description="Item ID")
    name: str = Field(..., description="Item name")
    price: float = Field(..., description="Item price")

# Usage in a route
@app.route("/items/<item_id>")
def get_item(item_id):
    # Return a response model
    return ItemResponse(id=item_id, name="Example Item", price=10.99), 200
```

## File Models

The file models module provides models for handling file uploads.

```python
from flask_x_openapi_schema.models.file_models import FileUploadModel, ImageUploadModel

@app.route("/upload", methods=["POST"])
@openapi_metadata(
    summary="Upload a file"
)
def upload_file(_x_file: FileUploadModel):
    # File is automatically injected and validated
    return {"filename": _x_file.file.filename}

@app.route("/upload/image", methods=["POST"])
@openapi_metadata(
    summary="Upload an image"
)
def upload_image(_x_file: ImageUploadModel):
    # Image file is automatically injected and validated
    return {"filename": _x_file.file.filename}
```

## Response Models

The response models module provides models for standardized API responses.

```python
from flask_x_openapi_schema.models.responses import OpenAPIMetaResponse, ResponseModel

class SuccessResponse(ResponseModel):
    message: str
    data: dict

# Define responses in the decorator
@openapi_metadata(
    summary="Create an item",
    responses=OpenAPIMetaResponse({
        201: SuccessResponse,
        400: ErrorResponse
    })
)
def create_item():
    # Function implementation
    return SuccessResponse(message="Item created", data={"id": "123"}), 201
```
