# Usage Guide for Flask-X-OpenAPI-Schema

This guide provides comprehensive examples and best practices for using Flask-X-OpenAPI-Schema in your Flask and Flask-RESTful applications.

## Table of Contents

- [Basic Setup](#basic-setup)
- [Flask.MethodView Integration](#flaskmethodview-integration)
- [Flask-RESTful Integration](#flask-restful-integration)
- [Parameter Binding](#parameter-binding)
- [Response Handling](#response-handling)
- [File Uploads](#file-uploads)
- [Internationalization](#internationalization)
- [Schema Generation](#schema-generation)
- [Best Practices](#best-practices)

## Basic Setup

### Installation

```bash
# Basic installation
pip install flask-x-openapi-schema

# With Flask-RESTful support
pip install flask-x-openapi-schema[flask-restful]
```

### Project Structure

A typical project structure might look like this:

```
my_api/
├── __init__.py
├── app.py
├── models/
│   ├── __init__.py
│   ├── request_models.py
│   └── response_models.py
├── resources/
│   ├── __init__.py
│   ├── user_resource.py
│   └── item_resource.py
├── views/
│   ├── __init__.py
│   ├── user_view.py
│   └── item_view.py
└── utils/
    ├── __init__.py
    └── schema_utils.py
```

### Basic Configuration

```python
# app.py
from flask import Flask
from flask_x_openapi_schema import configure_prefixes, ConventionalPrefixConfig

# Create a Flask app
app = Flask(__name__)

# Configure parameter prefixes (optional)
custom_config = ConventionalPrefixConfig(
    request_body_prefix="_x_body",
    request_query_prefix="_x_query",
    request_path_prefix="_x_path",
    request_file_prefix="_x_file"
)
configure_prefixes(custom_config)
```

## Flask.MethodView Integration

### Basic MethodView Example

```python
# views/user_view.py
from flask.views import MethodView
from flask import jsonify
from flask_x_openapi_schema.x.flask import openapi_metadata, OpenAPIMethodViewMixin
from flask_x_openapi_schema import OpenAPIMetaResponse, OpenAPIMetaResponseItem

from my_api.models.request_models import UserCreateRequest, UserUpdateRequest
from my_api.models.response_models import UserResponse, ErrorResponse

class UserView(OpenAPIMethodViewMixin, MethodView):
    @openapi_metadata(
        summary="Get all users",
        description="Retrieve a list of all users",
        tags=["users"],
        operation_id="getUsers",
        responses=OpenAPIMetaResponse(
            responses={
                "200": OpenAPIMetaResponseItem(
                    model=UserResponse,
                    description="List of users retrieved successfully",
                ),
                "500": OpenAPIMetaResponseItem(
                    model=ErrorResponse,
                    description="Internal server error",
                ),
            }
        ),
    )
    def get(self):
        # Implementation...
        users = [
            {"id": "1", "username": "user1", "email": "user1@example.com"},
            {"id": "2", "username": "user2", "email": "user2@example.com"},
        ]
        return jsonify(users), 200

    @openapi_metadata(
        summary="Create a new user",
        description="Create a new user with the provided information",
        tags=["users"],
        operation_id="createUser",
        responses=OpenAPIMetaResponse(
            responses={
                "201": OpenAPIMetaResponseItem(
                    model=UserResponse,
                    description="User created successfully",
                ),
                "400": OpenAPIMetaResponseItem(
                    model=ErrorResponse,
                    description="Invalid request data",
                ),
                "500": OpenAPIMetaResponseItem(
                    model=ErrorResponse,
                    description="Internal server error",
                ),
            }
        ),
    )
    def post(self, _x_body: UserCreateRequest):
        # Implementation...
        user = {
            "id": "3",
            "username": _x_body.username,
            "email": _x_body.email,
        }
        return jsonify(user), 201
```

### Registering MethodViews

```python
# app.py
from flask import Flask, Blueprint
from my_api.views.user_view import UserView
from my_api.views.item_view import ItemView, ItemDetailView

# Create a Flask app
app = Flask(__name__)

# Create a blueprint
blueprint = Blueprint("api", __name__, url_prefix="/api")

# Register the views
UserView.register_to_blueprint(blueprint, "/users", "users")
ItemView.register_to_blueprint(blueprint, "/items", "items")
ItemDetailView.register_to_blueprint(blueprint, "/items/<item_id>", "item_detail")

# Register the blueprint
app.register_blueprint(blueprint)
```

### Generating OpenAPI Schema

```python
# app.py
from flask_x_openapi_schema.x.flask.views import MethodViewOpenAPISchemaGenerator
import yaml

@app.route("/openapi.yaml")
def get_openapi_spec():
    generator = MethodViewOpenAPISchemaGenerator(
        title="My API",
        version="1.0.0",
        description="API for managing users and items",
    )
    
    # Process MethodView resources
    generator.process_methodview_resources(blueprint)
    
    # Generate the schema
    schema = generator.generate_schema()
    
    # Convert to YAML
    yaml_content = yaml.dump(
        schema,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=True,
    )
    
    return yaml_content, 200, {"Content-Type": "text/yaml"}
```

## Flask-RESTful Integration

### Basic Resource Example

```python
# resources/user_resource.py
from flask_restful import Resource
from flask_x_openapi_schema.x.flask_restful import openapi_metadata
from flask_x_openapi_schema import OpenAPIMetaResponse, OpenAPIMetaResponseItem

from my_api.models.request_models import UserCreateRequest, UserUpdateRequest
from my_api.models.response_models import UserResponse, ErrorResponse

class UserListResource(Resource):
    @openapi_metadata(
        summary="Get all users",
        description="Retrieve a list of all users",
        tags=["users"],
        operation_id="getUsers",
        responses=OpenAPIMetaResponse(
            responses={
                "200": OpenAPIMetaResponseItem(
                    model=UserResponse,
                    description="List of users retrieved successfully",
                ),
                "500": OpenAPIMetaResponseItem(
                    model=ErrorResponse,
                    description="Internal server error",
                ),
            }
        ),
    )
    def get(self):
        # Implementation...
        users = [
            {"id": "1", "username": "user1", "email": "user1@example.com"},
            {"id": "2", "username": "user2", "email": "user2@example.com"},
        ]
        return users, 200

    @openapi_metadata(
        summary="Create a new user",
        description="Create a new user with the provided information",
        tags=["users"],
        operation_id="createUser",
        responses=OpenAPIMetaResponse(
            responses={
                "201": OpenAPIMetaResponseItem(
                    model=UserResponse,
                    description="User created successfully",
                ),
                "400": OpenAPIMetaResponseItem(
                    model=ErrorResponse,
                    description="Invalid request data",
                ),
                "500": OpenAPIMetaResponseItem(
                    model=ErrorResponse,
                    description="Internal server error",
                ),
            }
        ),
    )
    def post(self, _x_body: UserCreateRequest):
        # Implementation...
        user = {
            "id": "3",
            "username": _x_body.username,
            "email": _x_body.email,
        }
        return user, 201

class UserResource(Resource):
    @openapi_metadata(
        summary="Get a user by ID",
        description="Retrieve a user by its unique identifier",
        tags=["users"],
        operation_id="getUser",
        responses=OpenAPIMetaResponse(
            responses={
                "200": OpenAPIMetaResponseItem(
                    model=UserResponse,
                    description="User retrieved successfully",
                ),
                "404": OpenAPIMetaResponseItem(
                    model=ErrorResponse,
                    description="User not found",
                ),
                "500": OpenAPIMetaResponseItem(
                    model=ErrorResponse,
                    description="Internal server error",
                ),
            }
        ),
    )
    def get(self, user_id: str):
        # Implementation...
        if user_id not in ["1", "2"]:
            return {"error_code": "USER_NOT_FOUND", "message": "User not found"}, 404
        
        user = {
            "id": user_id,
            "username": f"user{user_id}",
            "email": f"user{user_id}@example.com",
        }
        return user, 200
```

### Registering Resources

```python
# app.py
from flask import Flask
from flask_restful import Api
from flask_x_openapi_schema.x.flask_restful import OpenAPIIntegrationMixin

from my_api.resources.user_resource import UserListResource, UserResource
from my_api.resources.item_resource import ItemListResource, ItemResource

# Create a Flask app
app = Flask(__name__)

# Create an OpenAPI-enabled API
class OpenAPIApi(OpenAPIIntegrationMixin, Api):
    pass

api = OpenAPIApi(app)

# Register the resources
api.add_resource(UserListResource, "/api/users")
api.add_resource(UserResource, "/api/users/<string:user_id>")
api.add_resource(ItemListResource, "/api/items")
api.add_resource(ItemResource, "/api/items/<string:item_id>")
```

### Generating OpenAPI Schema

```python
# app.py
import yaml

@app.route("/openapi.yaml")
def get_openapi_spec():
    schema = api.generate_openapi_schema(
        title="My API",
        version="1.0.0",
        description="API for managing users and items",
        output_format="json",
    )
    
    # Convert to YAML
    yaml_content = yaml.dump(
        schema,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=True,
    )
    
    return yaml_content, 200, {"Content-Type": "text/yaml"}
```

## Parameter Binding

### Request Body

```python
@openapi_metadata(
    summary="Create a new item",
    # ...
)
def post(self, _x_body: ItemCreateRequest):
    # _x_body is automatically populated from the request JSON
    item = {
        "id": "123",
        "name": _x_body.name,
        "description": _x_body.description,
        "price": _x_body.price,
    }
    return item, 201
```

### Query Parameters

```python
@openapi_metadata(
    summary="Get all items",
    # ...
)
def get(self, _x_query: ItemFilterParams = None):
    # _x_query is automatically populated from the query parameters
    items = [...]
    
    if _x_query:
        if _x_query.category:
            items = [item for item in items if item["category"] == _x_query.category]
        
        if _x_query.min_price is not None:
            items = [item for item in items if item["price"] >= _x_query.min_price]
        
        if _x_query.max_price is not None:
            items = [item for item in items if item["price"] <= _x_query.max_price]
        
        # Apply pagination
        items = items[_x_query.offset:_x_query.offset + _x_query.limit]
    
    return items, 200
```

### Path Parameters

```python
@openapi_metadata(
    summary="Get an item by ID",
    # ...
)
def get(self, item_id: str):
    # item_id is automatically populated from the path parameter
    if item_id not in ["123", "456"]:
        return {"error_code": "ITEM_NOT_FOUND", "message": "Item not found"}, 404
    
    item = {
        "id": item_id,
        "name": f"Item {item_id}",
        "description": f"Description for item {item_id}",
        "price": float(item_id),
    }
    return item, 200
```

### File Uploads

```python
@openapi_metadata(
    summary="Upload an item image",
    # ...
)
def post(self, item_id: str, _x_file: ImageUploadModel):
    # _x_file.file is automatically populated from the uploaded file
    file = _x_file.file
    
    # Save the file
    file.save(f"uploads/{item_id}_{file.filename}")
    
    return {"message": "File uploaded successfully"}, 201
```

### Custom Parameter Prefixes

```python
from flask_x_openapi_schema import ConventionalPrefixConfig

# Create a custom configuration
custom_config = ConventionalPrefixConfig(
    request_body_prefix="req_body",
    request_query_prefix="req_query",
    request_path_prefix="req_path",
    request_file_prefix="req_file"
)

@openapi_metadata(
    summary="Create a new item",
    prefix_config=custom_config,
    # ...
)
def post(self, req_body: ItemCreateRequest):
    # req_body is automatically populated from the request JSON
    item = {
        "id": "123",
        "name": req_body.name,
        "description": req_body.description,
        "price": req_body.price,
    }
    return item, 201
```

## Response Handling

### Basic Responses

```python
@openapi_metadata(
    summary="Get all items",
    # ...
)
def get(self):
    # Implementation...
    items = [
        {"id": "123", "name": "Item 1", "price": 10.99},
        {"id": "456", "name": "Item 2", "price": 20.99},
    ]
    return items, 200
```

### Using BaseRespModel

```python
from flask_x_openapi_schema import BaseRespModel
from pydantic import Field

class ItemResponse(BaseRespModel):
    id: str = Field(..., description="Item ID")
    name: str = Field(..., description="Item name")
    description: str = Field(None, description="Item description")
    price: float = Field(..., description="Item price")

@openapi_metadata(
    summary="Get an item by ID",
    # ...
)
def get(self, item_id: str):
    # Implementation...
    if item_id not in ["123", "456"]:
        error = ErrorResponse(
            error_code="ITEM_NOT_FOUND",
            message="Item not found",
        )
        return error.to_response(404)
    
    item = ItemResponse(
        id=item_id,
        name=f"Item {item_id}",
        description=f"Description for item {item_id}",
        price=float(item_id),
    )
    return item.to_response(200)
```

### Documenting Responses

```python
@openapi_metadata(
    summary="Create a new item",
    description="Create a new item with the provided information",
    tags=["items"],
    operation_id="createItem",
    responses=OpenAPIMetaResponse(
        responses={
            "201": OpenAPIMetaResponseItem(
                model=ItemResponse,
                description="Item created successfully",
            ),
            "400": OpenAPIMetaResponseItem(
                model=ErrorResponse,
                description="Invalid request data",
            ),
            "500": OpenAPIMetaResponseItem(
                model=ErrorResponse,
                description="Internal server error",
            ),
        }
    ),
)
def post(self, _x_body: ItemCreateRequest):
    # Implementation...
```

## File Uploads

### Basic File Upload

```python
from flask_x_openapi_schema import ImageUploadModel

@openapi_metadata(
    summary="Upload an item image",
    # ...
)
def post(self, item_id: str, _x_file: ImageUploadModel):
    # _x_file.file is automatically populated from the uploaded file
    file = _x_file.file
    
    # Save the file
    file.save(f"uploads/{item_id}_{file.filename}")
    
    return {"message": "File uploaded successfully"}, 201
```

### Custom File Upload Model

```python
from flask_x_openapi_schema import ImageUploadModel
from pydantic import Field

class ItemImageUpload(ImageUploadModel):
    description: str = Field(..., description="Image description")
    is_primary: bool = Field(False, description="Whether this is the primary item image")

@openapi_metadata(
    summary="Upload an item image",
    # ...
)
def post(self, item_id: str, _x_file: ItemImageUpload):
    # _x_file.file is automatically populated from the uploaded file
    file = _x_file.file
    
    # Access additional fields
    description = _x_file.description
    is_primary = _x_file.is_primary
    
    # Save the file
    file.save(f"uploads/{item_id}_{file.filename}")
    
    return {
        "message": "File uploaded successfully",
        "description": description,
        "is_primary": is_primary,
    }, 201
```

### Multiple File Uploads

```python
@openapi_metadata(
    summary="Upload item files",
    # ...
)
def post(
    self,
    item_id: str,
    _x_file_image: ImageUploadModel,
    _x_file_document: DocumentUploadModel,
):
    # Access each file
    image = _x_file_image.file
    document = _x_file_document.file
    
    # Save the files
    image.save(f"uploads/{item_id}_image_{image.filename}")
    document.save(f"uploads/{item_id}_document_{document.filename}")
    
    return {"message": "Files uploaded successfully"}, 201
```

## Internationalization

### Using I18nStr

```python
from flask_x_openapi_schema import I18nStr, set_current_language

# Set the current language
set_current_language("zh-Hans")

@openapi_metadata(
    summary=I18nStr({
        "en-US": "Get an item",
        "zh-Hans": "获取一个项目",
        "ja-JP": "アイテムを取得する",
    }),
    description=I18nStr({
        "en-US": "Get an item by ID from the database",
        "zh-Hans": "通过ID从数据库获取一个项目",
        "ja-JP": "IDからデータベースからアイテムを取得する",
    }),
    tags=["items"],
    operation_id="getItem",
    # ...
)
def get(self, item_id: str):
    # Implementation...
```

### Language Switching

```python
import contextlib
from flask_x_openapi_schema import set_current_language, get_current_language

@contextlib.contextmanager
def language_context(language):
    """Temporarily switch to a different language."""
    previous_language = get_current_language()
    set_current_language(language)
    try:
        yield
    finally:
        set_current_language(previous_language)

# Use the context manager
with language_context("zh-Hans"):
    # Generate schema in Chinese
    schema_zh = generator.generate_schema()

with language_context("ja-JP"):
    # Generate schema in Japanese
    schema_ja = generator.generate_schema()
```

## Schema Generation

### Basic Schema Generation

```python
from flask_x_openapi_schema.x.flask.views import MethodViewOpenAPISchemaGenerator
import yaml

@app.route("/openapi.yaml")
def get_openapi_spec():
    generator = MethodViewOpenAPISchemaGenerator(
        title="My API",
        version="1.0.0",
        description="API for managing resources",
    )
    
    # Process MethodView resources
    generator.process_methodview_resources(blueprint)
    
    # Generate the schema
    schema = generator.generate_schema()
    
    # Convert to YAML
    yaml_content = yaml.dump(
        schema,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=True,
    )
    
    return yaml_content, 200, {"Content-Type": "text/yaml"}
```

### Serving Swagger UI

```python
@app.route("/")
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>API Documentation</title>
        <link rel="stylesheet" type="text/css" href="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/5.9.1/swagger-ui.min.css">
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/5.9.1/swagger-ui-bundle.min.js"></script>
        <script>
            window.onload = function() {
                SwaggerUIBundle({
                    url: "/openapi.yaml",
                    dom_id: "#swagger-ui",
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIBundle.SwaggerUIStandalonePreset
                    ],
                    layout: "BaseLayout",
                    validatorUrl: null,
                    displayRequestDuration: true,
                    syntaxHighlight: {
                        activated: true,
                        theme: "agate"
                    }
                });
            }
        </script>
    </body>
    </html>
    """
```

## Best Practices

### 1. Use Descriptive Operation IDs

Operation IDs should be unique and descriptive:

```python
@openapi_metadata(
    summary="Get all users",
    operation_id="getAllUsers",  # Good
    # ...
)
```

Instead of:

```python
@openapi_metadata(
    summary="Get all users",
    operation_id="get",  # Bad - not descriptive
    # ...
)
```

### 2. Group Related Operations with Tags

Use tags to group related operations:

```python
@openapi_metadata(
    summary="Get all users",
    tags=["users"],  # Group with other user operations
    # ...
)
```

### 3. Provide Comprehensive Response Documentation

Document all possible response types:

```python
@openapi_metadata(
    summary="Create a new user",
    responses=OpenAPIMetaResponse(
        responses={
            "201": OpenAPIMetaResponseItem(
                model=UserResponse,
                description="User created successfully",
            ),
            "400": OpenAPIMetaResponseItem(
                model=ErrorResponse,
                description="Invalid request data",
            ),
            "409": OpenAPIMetaResponseItem(
                model=ErrorResponse,
                description="Username already exists",
            ),
            "500": OpenAPIMetaResponseItem(
                model=ErrorResponse,
                description="Internal server error",
            ),
        }
    ),
    # ...
)
```

### 4. Use Pydantic Field Descriptions

Add descriptions to all Pydantic fields:

```python
from pydantic import BaseModel, Field

class UserCreateRequest(BaseModel):
    username: str = Field(..., description="User's username")
    email: str = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")
    full_name: str = Field(None, description="User's full name")
```

### 5. Centralize Model Definitions

Keep model definitions in a central location:

```
my_api/
├── models/
│   ├── __init__.py
│   ├── request_models.py
│   └── response_models.py
```

### 6. Use Consistent Naming Conventions

Use consistent naming conventions for models and endpoints:

- Request models: `{Resource}CreateRequest`, `{Resource}UpdateRequest`
- Response models: `{Resource}Response`
- Error models: `ErrorResponse`
- List resources: `{Resource}ListResource`
- Individual resources: `{Resource}Resource`

### 7. Implement Proper Error Handling

Use structured error responses:

```python
from flask_x_openapi_schema import BaseRespModel
from pydantic import Field

class ErrorResponse(BaseRespModel):
    error_code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: dict = Field(None, description="Additional error details")

@openapi_metadata(
    summary="Get a user by ID",
    # ...
)
def get(self, user_id: str):
    if user_id not in ["1", "2"]:
        error = ErrorResponse(
            error_code="USER_NOT_FOUND",
            message=f"User with ID {user_id} not found",
        )
        return error.to_response(404)
    
    # ...
```

### 8. Use Pagination for List Endpoints

Implement pagination for list endpoints:

```python
from pydantic import BaseModel, Field

class PaginationParams(BaseModel):
    page: int = Field(1, description="Page number")
    per_page: int = Field(10, description="Items per page")

class UserFilterParams(PaginationParams):
    username: str = Field(None, description="Filter by username")
    email: str = Field(None, description="Filter by email")

@openapi_metadata(
    summary="Get all users",
    # ...
)
def get(self, _x_query: UserFilterParams = None):
    # Implementation with pagination
    # ...
```

### 9. Use Enums for Fixed Values

Use enums for fields with fixed values:

```python
from enum import Enum
from pydantic import BaseModel, Field

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

class UserCreateRequest(BaseModel):
    username: str = Field(..., description="User's username")
    email: str = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")
    role: UserRole = Field(UserRole.USER, description="User's role")
```

### 10. Implement Validation

Use Pydantic validators for custom validation:

```python
from pydantic import BaseModel, Field, validator
import re

class UserCreateRequest(BaseModel):
    username: str = Field(..., description="User's username")
    email: str = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")
    
    @validator("username")
    def username_must_be_valid(cls, v):
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("Username must contain only letters, numbers, and underscores")
        return v
    
    @validator("email")
    def email_must_be_valid(cls, v):
        if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", v):
            raise ValueError("Email must be a valid email address")
        return v
    
    @validator("password")
    def password_must_be_strong(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v
```