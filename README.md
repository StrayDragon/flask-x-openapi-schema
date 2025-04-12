# Dify OpenAPI Schema Generator

This module provides utilities for generating OpenAPI schemas from Flask-RESTful resources and Pydantic models. It can be used as a standalone package or as part of the Dify platform.

## Features

- Generate OpenAPI schemas from Flask-RESTful resources
- Convert Pydantic models to OpenAPI schemas
- Automatically inject request parameters from Pydantic models
- Preserve type annotations from Pydantic models for better IDE support
- Output schemas in YAML or JSON format
- Support for internationalization (i18n) in API documentation
- Handle file uploads with automatic parameter injection

## Installation

### As Part of Dify

This module is included in the Dify platform and can be used directly.

### As a Standalone Package

To install as a standalone package:

```bash
# From the repository root
cd api/core/openapi
pip install -e .
```

Or install from GitHub:

```bash
pip install git+https://github.com/langgenius/dify.git#subdirectory=api/core/openapi
```

## Usage

### Decorating API Endpoints with Auto-Detection

Use the `openapi_metadata` decorator to add OpenAPI metadata to your API endpoints. The decorator automatically detects parameters with special prefixes and their types:

```python
from typing import Optional
from pydantic import BaseModel, Field
from flask_x_openapi_schema import openapi_metadata

# Define a Pydantic model for the request body
class CreateItemRequest(BaseModel):
    """Request model for creating an item."""
    name: str = Field(..., description="The name of the item")
    price: float = Field(..., description="The price of the item")

# Use the decorator on your API endpoint
# No need to specify request_body - it will be auto-detected from x_request_body parameter
@openapi_metadata(
    summary="Create a new item",
    description="Create a new item with the given data",
    tags=["Items"],
    operation_id="createItem",
    responses={
        "201": {"description": "Item created successfully"},
        "400": {"description": "Invalid request"},
    },
)
def post(self, tenant_id: str, x_request_body: CreateItemRequest):
    # Access the request body as a Pydantic model
    name = x_request_body.name
    price = x_request_body.price

    # Return the created item
    return {"id": "123", "name": name, "price": price}, 201
```

### Using Special Parameter Prefixes with Auto-Detection

The decorator automatically detects parameters with special prefixes and their types:

- `x_request_body`: Automatically detected as the request body model based on its type annotation
- `x_request_query`: Automatically detected as the query parameters model based on its type annotation
- `x_request_path_<param_name>`: Automatically detected as a path parameter
- `x_request_file`: Automatically detected as a file object

You don't need to explicitly specify `request_body`, `query_model`, or `path_params` in the decorator - they will be automatically detected from your function parameters.

```python
# Define a Pydantic model for query parameters
class ItemQueryParams(BaseModel):
    """Query parameters for item operations."""
    skip: int = Field(0, description="Number of items to skip")
    limit: int = Field(100, description="Maximum number of items to return")

# Use the decorator with query parameters
# No need to specify query_model - it will be auto-detected from x_request_query parameter
@openapi_metadata(
    summary="Get items",
    description="Get a list of items",
    tags=["Items"],
    operation_id="getItems",
)
def get(self, tenant_id: str, x_request_query: ItemQueryParams):
    # Access the query parameters as a Pydantic model
    skip = x_request_query.skip
    limit = x_request_query.limit

    # Return a list of items
    return {
        "items": [...],
        "pagination": {
            "skip": skip,
            "limit": limit
        }
    }, 200
```

### Using Path Parameters with Auto-Detection

Path parameters are automatically detected from function parameters with the `x_request_path_<param_name>` prefix:

```python
# No need to specify path_params - they will be auto-detected from x_request_path_item_id parameter
@openapi_metadata(
    summary="Get an item",
    description="Get an item by ID",
    tags=["Items"],
    operation_id="getItem",
)
def get(self, tenant_id: str, item_id: str, x_request_path_item_id: str):
    # Access the path parameter
    item_id_from_path = x_request_path_item_id

    # Return the item
    return {"id": item_id_from_path, "name": "Example Item"}, 200
```

### Using File Objects with Auto-Detection

File objects are automatically detected from function parameters with the `x_request_file` prefix:

```python
# No need to specify any special parameters - file objects are auto-detected
@openapi_metadata(
    summary="Upload a file",
    description="Upload a file to the server",
    tags=["Files"],
    operation_id="uploadFile",
)
def post(self, tenant_id: str, x_request_file: Any):
    # Access the file object
    file_content = x_request_file.read()

    # Return the file info
    return {"size": len(file_content)}, 201
```

### Using BaseRespModel for Responses

You can use `BaseRespModel` to create response models that are automatically converted to Flask-RESTful compatible responses:

```python
from flask_x_openapi_schema.models.base import BaseRespModel
from pydantic import Field

# Define a response model that extends BaseRespModel
class ItemResponse(BaseRespModel):
    """Response model for an item."""
    id: str = Field(..., description="The ID of the item")
    name: str = Field(..., description="The name of the item")
    price: float = Field(..., description="The price of the item")

# Use the decorator with BaseRespModel
@openapi_metadata(
    summary="Get an item",
    description="Get an item by ID",
    tags=["Items"],
    operation_id="getItem",
)
def get(self, tenant_id: str, item_id: str):
    # Return a response model instance
    return ItemResponse(
        id=item_id,
        name="Example Item",
        price=9.99,
    )

    # Or with a status code
    # return ItemResponse(id=item_id, name="Example Item", price=9.99), 200
```

### Using Response Schema Utility Functions

You can use the response schema utility functions to simplify the definition of responses in the OpenAPI metadata:

```python
from flask_x_openapi_schema import openapi_metadata, responses_schema, success_response
from flask_x_openapi_schema.models.base import BaseRespModel
from pydantic import Field

# Define a response model that extends BaseRespModel
class ItemResponse(BaseRespModel):
    """Response model for an item."""
    id: str = Field(..., description="The ID of the item")
    name: str = Field(..., description="The name of the item")
    price: float = Field(..., description="The price of the item")

# Use the decorator with responses_schema
@openapi_metadata(
    summary="Get an item",
    description="Get an item by ID",
    tags=["Items"],
    operation_id="getItem",
    responses=responses_schema(
        success_responses={
            "200": success_response(
                model=ItemResponse,
                description="Item retrieved successfully",
            ),
        },
        errors={
            "404": "Item not found",
        },
    ),
)
def get(self, tenant_id: str, item_id: str):
    # Return a response model instance
    return ItemResponse(
        id=item_id,
        name="Example Item",
        price=9.99,
    )
```

### Using Multiple Success Responses

You can define multiple success responses with different status codes and models:

```python
from flask_x_openapi_schema import openapi_metadata, responses_schema, success_response
from flask_x_openapi_schema.models.base import BaseRespModel
from pydantic import Field

# Define response models that extend BaseRespModel
class ItemResponse(BaseRespModel):
    """Response model for an item."""
    id: str = Field(..., description="The ID of the item")
    name: str = Field(..., description="The name of the item")

class ItemCreatedResponse(BaseRespModel):
    """Response model for a created item."""
    id: str = Field(..., description="The ID of the created item")
    created_at: str = Field(..., description="The creation timestamp")

# Use the decorator with multiple success responses
@openapi_metadata(
    summary="Get or create an item",
    description="Get an existing item or create a new one if it doesn't exist",
    tags=["Items"],
    operation_id="getOrCreateItem",
    responses=responses_schema(
        # Multiple success responses with different status codes
        success_responses={
            "200": success_response(
                model=ItemResponse,
                description="Item retrieved successfully",
            ),
            "201": success_response(
                model=ItemCreatedResponse,
                description="Item created successfully",
            ),
        },
        # Error responses
        errors={
            "400": "Invalid request",
        },
    ),
)
def post(self, tenant_id: str, item_id: str):
    # Check if the item exists
    item_exists = False  # In a real implementation, this would check the database

    if item_exists:
        # Return an existing item with 200 status code
        return ItemResponse(
            id=item_id,
            name="Example Item",
        ), 200
    else:
        # Create a new item and return with 201 status code
        return ItemCreatedResponse(
            id=item_id,
            created_at="2023-01-01T12:00:00Z",
        ), 201
```

### Generating OpenAPI Schemas

Use the `generate-openapi` command to generate OpenAPI schemas:

```bash
# Generate OpenAPI schema for the service_api blueprint
flask generate-openapi --blueprint service_api --output openapi.yaml

# Generate OpenAPI schema in JSON format
flask generate-openapi --blueprint service_api --output openapi.json --format json
```

## Components

- `decorators.py`: Contains the `openapi_metadata` decorator for adding OpenAPI metadata to API endpoints
- `schema_generator.py`: Contains the `OpenAPISchemaGenerator` class for generating OpenAPI schemas
- `utils.py`: Contains utility functions for converting Pydantic models to OpenAPI schemas
- `restful_utils.py`: Contains utility functions for integrating Pydantic models with Flask-RESTful
- `external_api_extension.py`: Contains the `OpenAPIIntegrationMixin` class for extending the Flask-RESTful API
- `commands.py`: Contains the Flask CLI commands for generating OpenAPI schemas

## Internationalization (i18n) Support

The OpenAPI module provides support for internationalization in API documentation. You can define strings in multiple languages and automatically generate documentation in the appropriate language.

### Using I18nString

The `I18nString` class allows you to define strings in multiple languages:

```python
from flask_x_openapi_schema import I18nString, openapi_metadata

@openapi_metadata(
    summary=I18nString({
        "en-US": "Get an item",
        "zh-Hans": "获取一个项目",
        "ja-JP": "アイテムを取得する",
    }),
    description=I18nString({
        "en-US": "Get an item by ID from the database",
        "zh-Hans": "通过ID从数据库获取一个项目",
        "ja-JP": "IDからデータベースからアイテムを取得する",
    }),
    # ...
)
def get(self, tenant_id: str, item_id: str):
    # ...
```

### Using I18nBaseModel

The `I18nBaseModel` class allows you to define Pydantic models with internationalized fields:

```python
from flask_x_openapi_schema import I18nBaseModel, I18nString
from flask_x_openapi_schema.models.base import BaseRespModel
from pydantic import Field

class ItemI18nResponse(I18nBaseModel, BaseRespModel):
    id: str = Field(..., description="The ID of the item")
    name: str = Field(..., description="The name of the item")
    description: I18nString = Field(
        ...,
        description="The description of the item (internationalized)"
    )
```

### Setting the Current Language

You can set the current language for the thread using the `set_current_language` function:

```python
from flask_x_openapi_schema import set_current_language

# Set the language to Chinese
set_current_language("zh-Hans")

# Now all I18nString instances will return Chinese strings by default
```

### Handling File Uploads

The `openapi_metadata` decorator supports file uploads through the `x_request_file` parameter prefix:

```python
from werkzeug.datastructures import FileStorage
from flask_x_openapi_schema import openapi_metadata

class FileUploadResource(Resource):
    @openapi_metadata(
        summary="Upload a file",
        description="Upload a file to the server",
        tags=["Files"],
        # ... other metadata
    )
    def post(self, x_request_file: FileStorage):
        # The file is automatically injected from request.files
        filename = x_request_file.filename
        # Process the file...
        return {"filename": filename}
```

You can also handle multiple files with specific names:

```python
def post(self, x_request_file_document: FileStorage, x_request_file_image: FileStorage):
    # x_request_file_document will contain the file named "document"
    # x_request_file_image will contain the file named "image"
    # ...
```

#### Using Pydantic Models for File Uploads

For better type checking, validation, and IDE support, you can use Pydantic models for file uploads:

```python
from flask_x_openapi_schema import ImageUploadModel, openapi_metadata

class ImageUploadResource(Resource):
    @openapi_metadata(
        summary="Upload an image",
        description="Upload an image with validation",
        tags=["Images"],
        # ... other metadata
    )
    def post(self, x_request_file: ImageUploadModel):
        # The file is automatically injected and validated
        file = x_request_file.file
        # Process the file...
        return {"filename": file.filename}
```

The OpenAPI module provides several built-in models:

- `FileUploadModel`: Base model for file uploads
- `ImageUploadModel`: Model for image file uploads with validation
- `DocumentUploadModel`: Model for document file uploads with validation
- `MultipleFileUploadModel`: Model for multiple file uploads

See the `examples/file_upload_example.py`, `examples/pydantic_file_upload_example.py`, and `examples/file_upload_readme.md` for more details.

## Examples

See the `examples` directory for complete examples of how to use the OpenAPI schema generator, including internationalization support and file uploads.
