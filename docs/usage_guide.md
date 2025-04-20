# Flask-X-OpenAPI-Schema Usage Guide

This guide provides detailed instructions on how to use Flask-X-OpenAPI-Schema in your Flask applications.

## Installation

```bash
# From the repository root
pip install -e .

# Or install from GitHub
pip install git+https://github.com/langgenius/dify.git#subdirectory=api/core/openapi
```

## Basic Setup

### 1. Initialize Your Flask Application

```python
from flask import Flask
from flask_restful import Api
# For Flask-RESTful
from flask_x_openapi_schema.x.flask_restful import OpenAPIIntegrationMixin

# Create a Flask app
app = Flask(__name__)

# Create an OpenAPI-enabled API
class OpenAPIApi(OpenAPIIntegrationMixin, Api):
    pass

# Initialize the API
api = OpenAPIApi(app)

# For Flask.MethodView
from flask import Flask, Blueprint
from flask.views import MethodView
from flask_x_openapi_schema.x.flask import OpenAPIMethodViewMixin

# Create a Flask app
app = Flask(__name__)

# Create a blueprint
blueprint = Blueprint("api", __name__)
```

### 2. Define Pydantic Models

```python
from pydantic import BaseModel, Field
from flask_x_openapi_schema.models.base import BaseRespModel

# Request model
class ItemRequest(BaseModel):
    """Request model for creating an item."""
    name: str = Field(..., description="The name of the item")
    price: float = Field(..., description="The price of the item")
    description: str = Field("", description="The description of the item")

# Response model
class ItemResponse(BaseRespModel):
    """Response model for an item."""
    id: str = Field(..., description="The ID of the item")
    name: str = Field(..., description="The name of the item")
    price: float = Field(..., description="The price of the item")
    created_at: str = Field(..., description="The creation timestamp")
```

### 3. Create API Resources

```python
# Flask-RESTful example
from flask_restful import Resource
from flask_x_openapi_schema.x.flask_restful import openapi_metadata
from flask_x_openapi_schema import responses_schema, success_response

class ItemResource(Resource):
    @openapi_metadata(
        summary="Create a new item",
        description="Create a new item with the given data",
        tags=["Items"],
        operation_id="createItem",
        responses=responses_schema(
            success_responses={
                "201": success_response(
                    model=ItemResponse,
                    description="Item created successfully",
                ),
            },
            errors={
                "400": "Invalid request",
            },
        ),
    )
    def post(self, _x_body: ItemRequest):
        # Access the request body as a Pydantic model
        name = _x_body.name
        price = _x_body.price
        description = _x_body.description

        # Create the item (in a real app, this would interact with a database)
        item_id = "123"  # Example ID
        created_at = "2023-01-01T12:00:00Z"  # Example timestamp

        # Return the created item using the response model
        return ItemResponse(
            id=item_id,
            name=name,
            price=price,
            created_at=created_at,
        ), 201

# Flask.MethodView example
from flask.views import MethodView
from flask_x_openapi_schema.x.flask import openapi_metadata, OpenAPIMethodViewMixin

class ItemView(OpenAPIMethodViewMixin, MethodView):
    @openapi_metadata(
        summary="Create a new item",
        description="Create a new item with the given data",
        tags=["Items"],
        operation_id="createItem",
        responses=responses_schema(
            success_responses={
                "201": success_response(
                    model=ItemResponse,
                    description="Item created successfully",
                ),
            },
            errors={
                "400": "Invalid request",
            },
        ),
    )
    def post(self, _x_body: ItemRequest):
        # Access the request body as a Pydantic model
        name = _x_body.name
        price = _x_body.price
        description = _x_body.description

        # Create the item (in a real app, this would interact with a database)
        item_id = "123"  # Example ID
        created_at = "2023-01-01T12:00:00Z"  # Example timestamp

        # Return the created item using the response model
        return ItemResponse(
            id=item_id,
            name=name,
            price=price,
            created_at=created_at,
        ), 201
```

### 4. Register Resources with the API

```python
# For Flask-RESTful
api.add_resource(ItemResource, "/items")

# For Flask.MethodView
blueprint.add_url_rule("/items", view_func=ItemView.as_view("items"))
app.register_blueprint(blueprint)
```

### 5. Generate OpenAPI Schema

```python
# For Flask-RESTful
schema = api.generate_openapi_schema(
    title="Items API",
    version="1.0.0",
    description="API for managing items",
    output_format="yaml",  # or "json"
)

# Save the schema to a file
with open("openapi.yaml", "w") as f:
    f.write(schema)

# For Flask.MethodView with OpenAPISchemaGenerator
from flask_x_openapi_schema import OpenAPISchemaGenerator

# Create a schema generator
generator = OpenAPISchemaGenerator(
    title="Items API",
    version="1.0.0",
    description="API for managing items"
)

# Scan the blueprint
generator.scan_blueprint(blueprint)

# Generate the schema
schema = generator.generate_schema()

# Convert to YAML or JSON
import yaml
with open("openapi.yaml", "w") as f:
    yaml.dump(schema, f)
```

## Advanced Usage

### Parameter Binding with Special Prefixes

The `openapi_metadata` decorator binds parameters with special prefixes:

- `_x_body`: Binds the entire request body object
- `_x_query`: Binds the entire query parameters object
- `_x_path_<param_name>`: Binds a path parameter
- `_x_file`: Binds a file object

These prefixes can be customized using the `ConventionalPrefixConfig` class:

```python
# Query parameters
class ItemQueryParams(BaseModel):
    """Query parameters for item operations."""
    skip: int = Field(0, description="Number of items to skip")
    limit: int = Field(100, description="Maximum number of items to return")

@openapi_metadata(
    summary="Get items",
    description="Get a list of items",
    tags=["Items"],
    operation_id="getItems",
)
def get(self, _x_query: ItemQueryParams):
    # Access the query parameters as a Pydantic model
    skip = _x_query.skip
    limit = _x_query.limit

    # Return a list of items
    return {
        "items": [...],
        "pagination": {
            "skip": skip,
            "limit": limit
        }
    }, 200

# Path parameters
@openapi_metadata(
    summary="Get an item",
    description="Get an item by ID",
    tags=["Items"],
    operation_id="getItem",
)
def get(self, item_id: str, _x_path_item_id: str):
    # Access the path parameter
    item_id_from_path = _x_path_item_id

    # Return the item
    return {"id": item_id_from_path, "name": "Example Item"}, 200
```

### Internationalization Support

```python
from flask_x_openapi_schema import I18nStr, set_current_language

# Create internationalized strings
summary = I18nStr({
    "en-US": "Get an item",
    "zh-Hans": "获取一个项目",
    "ja-JP": "アイテムを取得する",
})

# Set the current language
set_current_language("zh-Hans")

# Use in decorator
@openapi_metadata(
    summary=summary,
    description=I18nStr({
        "en-US": "Get an item by ID from the database",
        "zh-Hans": "通过ID从数据库获取一个项目",
        "ja-JP": "IDからデータベースからアイテムを取得する",
    }),
    tags=["Items"],
    operation_id="getItem",
)
def get(self, item_id: str):
    # ...
```

### File Upload Handling

```python
from werkzeug.datastructures import FileStorage
from flask_x_openapi_schema import openapi_metadata, FileUploadModel

# Simple file upload
@openapi_metadata(
    summary="Upload a file",
    description="Upload a file to the server",
    tags=["Files"],
    operation_id="uploadFile",
)
def post(self, _x_file: FileStorage):
    # The file is automatically injected from request.files
    filename = _x_file.filename
    # Process the file...
    return {"filename": filename}

# Multiple file uploads
@openapi_metadata(
    summary="Upload multiple files",
    description="Upload multiple files to the server",
    tags=["Files"],
    operation_id="uploadMultipleFiles",
)
def post(self, x_request_file_document: FileStorage, x_request_file_image: FileStorage):
    # Process multiple files...
    return {"files": [document_info, image_info]}

# Using Pydantic models for file uploads
@openapi_metadata(
    summary="Upload an image",
    description="Upload an image with validation",
    tags=["Images"],
    operation_id="uploadImage",
)
def post(self, _x_file: FileUploadModel):
    # The file is automatically injected and validated
    file = _x_file.file
    # Process the file...
    return {"filename": file.filename}
```

### Using Flask CLI Commands

Flask-X-OpenAPI-Schema provides CLI commands for generating OpenAPI schemas:

```bash
# Generate OpenAPI schema for the service_api blueprint
flask generate-openapi --blueprint service_api --output openapi.yaml

# Generate OpenAPI schema in JSON format
flask generate-openapi --blueprint service_api --output openapi.json --format json
```

To register the commands with your Flask application:

```python
from flask_x_openapi_schema.commands import register_commands

# Register the commands with your Flask application
register_commands(app)
```

## Best Practices

### 1. Organize Models by Domain

Group your Pydantic models by domain or functionality:

```python
# user_models.py
class UserRequest(BaseModel):
    # ...

class UserResponse(BaseRespModel):
    # ...

# item_models.py
class ItemRequest(BaseModel):
    # ...

class ItemResponse(BaseRespModel):
    # ...
```

### 2. Use Descriptive Field Descriptions

Always provide clear descriptions for your model fields:

```python
class UserRequest(BaseModel):
    username: str = Field(..., description="The user's unique username (3-20 characters)")
    email: str = Field(..., description="The user's email address for notifications and recovery")
    password: str = Field(..., description="The user's password (min 8 characters)")
```

### 3. Leverage Response Schema Utilities

Use the response schema utilities to create consistent responses:

```python
from flask_x_openapi_schema import responses_schema, success_response

@openapi_metadata(
    # ...
    responses=responses_schema(
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
        errors={
            "400": "Invalid request",
            "404": "Item not found",
            "500": "Internal server error",
        },
    ),
)
```

### 4. Use BaseRespModel for Responses

Always extend `BaseRespModel` for your response models to ensure proper conversion to Flask-RESTful responses:

```python
from flask_x_openapi_schema.models.base import BaseRespModel

class ErrorResponse(BaseRespModel):
    error: str = Field(..., description="Error message")
    code: int = Field(..., description="Error code")

class SuccessResponse(BaseRespModel):
    message: str = Field(..., description="Success message")
    data: dict = Field(..., description="Response data")
```

### 5. Implement Consistent Error Handling

Create a consistent error handling approach:

```python
def handle_error(error_code: int, message: str) -> tuple:
    """Handle API errors consistently."""
    return ErrorResponse(
        error=message,
        code=error_code,
    ), error_code
```

## Troubleshooting

### Common Issues and Solutions

1. **Issue**: Parameters not being bound correctly.
   **Solution**: Ensure you're using the correct parameter prefixes (`_x_body`, `_x_query`, etc.) and that your parameters have type annotations.

2. **Issue**: Pydantic models not showing up in the OpenAPI schema.
   **Solution**: Make sure your models are properly registered with the schema generator by using them in the `openapi_metadata` decorator.

3. **Issue**: File uploads not working.
   **Solution**: Ensure your form is using `enctype="multipart/form-data"` and that you're using the correct parameter prefix (`_x_file`).

4. **Issue**: Internationalized strings not showing up in the correct language.
   **Solution**: Check that you've set the current language using `set_current_language()` before generating the schema.

5. **Issue**: Response models not being converted properly.
   **Solution**: Make sure your response models extend `BaseRespModel` and that you're returning them correctly from your resource methods.

### Configurable Parameter Prefixes

You can customize the parameter prefixes used for auto-detection using the `ConventionalPrefixConfig` class:

```python
from flask_x_openapi_schema import ConventionalPrefixConfig, configure_prefixes, reset_prefixes, GLOBAL_CONFIG_HOLDER

# Create a custom configuration
custom_config = ConventionalPrefixConfig(
    request_body_prefix="req_body",
    request_query_prefix="req_query",
    request_path_prefix="req_path",
    request_file_prefix="req_file"
)

# Configure globally
configure_prefixes(custom_config)

# Reset to default prefixes if needed
reset_prefixes()

# Configure at the API level
api = OpenAPIApi(app)
api.configure_openapi(prefix_config=custom_config)

# Or using keyword arguments (for backward compatibility)
api.configure_openapi(
    request_body_prefix="req_body",
    request_query_prefix="req_query"
)

# Configure at the Blueprint level
blueprint = OpenAPIBlueprint('api', __name__)
blueprint.configure_openapi(prefix_config=custom_config)

# Configure per-function (recommended approach)
@openapi_metadata(
    summary="Test endpoint",
    prefix_config=ConventionalPrefixConfig(
        request_body_prefix="req_body",
        request_query_prefix="req_query"
    )
)
def my_function(req_body: MyModel, req_query: QueryModel):
    # Use custom prefixes
    return {"message": "Success"}
```

The per-function configuration is recommended as it only affects that specific function and doesn't change the global configuration. If you need to modify the global configuration, make sure to reset it to the default values when you're done to avoid affecting other parts of your application.

## Advanced Topics

### Custom Schema Generation

You can customize the schema generation process by extending the `OpenAPISchemaGenerator` class:

```python
from flask_x_openapi_schema import OpenAPISchemaGenerator

class CustomSchemaGenerator(OpenAPISchemaGenerator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add custom initialization

    def generate_schema(self):
        schema = super().generate_schema()
        # Customize the schema
        schema["info"]["x-custom-field"] = "Custom value"
        return schema
```

### Custom Response Formats

You can create custom response formats by extending `BaseRespModel`:

```python
class ApiResponse(BaseRespModel):
    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[dict] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message")

    def to_response(self, status_code: int = 200):
        # Custom response formatting
        response_data = {
            "success": self.success,
            "timestamp": datetime.now().isoformat(),
        }

        if self.data:
            response_data["data"] = self.data

        if self.error:
            response_data["error"] = self.error

        return response_data, status_code
```

### Integration with Other Flask Extensions

Flask-X-OpenAPI-Schema can be integrated with other Flask extensions:

```python
from flask import Flask
from flask_restful import Api
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_x_openapi_schema import OpenAPIIntegrationMixin

app = Flask(__name__)

# Configure extensions
CORS(app)
jwt = JWTManager(app)

# Create OpenAPI-enabled API
class OpenAPIApi(OpenAPIIntegrationMixin, Api):
    pass

api = OpenAPIApi(app)

# Add JWT security scheme
api.add_security_scheme("bearerAuth", {
    "type": "http",
    "scheme": "bearer",
    "bearerFormat": "JWT",
})
```

## Conclusion

Flask-X-OpenAPI-Schema provides a powerful yet easy-to-use solution for generating OpenAPI documentation from Flask-RESTful APIs. By following the guidelines in this document, you can create well-documented APIs with minimal effort.