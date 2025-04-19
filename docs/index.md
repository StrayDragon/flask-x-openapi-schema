# Flask-X-OpenAPI-Schema Documentation

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](../LICENSE)

Welcome to the Flask-X-OpenAPI-Schema documentation! This library simplifies the generation of OpenAPI schemas from Flask and Flask-RESTful applications, providing a seamless integration between Flask, Flask-RESTful, and Pydantic models.

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Documentation](#documentation)
  - [Project Overview](README.md)
  - [Usage Guide](usage_guide.md)
  - [Core Components](core_components.md)
  - [Framework-Specific Implementations](framework_specific.md)
  - [Internationalization](internationalization.md)
  - [File Uploads](file_uploads.md)
- [Examples](#examples)
- [API Reference](#api-reference)

## Installation

### Basic Installation

```bash
# Install from PyPI
pip install flask-x-openapi-schema

# From the repository root
pip install -e .
```

### Optional Dependencies

By default, only Flask, Pydantic, and PyYAML are installed. For Flask-RESTful integration:

```bash
pip install flask-x-openapi-schema[flask-restful]
# or
pip install -e .[flask-restful]
```

## Quick Start

```python
from flask import Flask
from flask_restful import Resource, Api
from pydantic import BaseModel, Field
from flask_x_openapi_schema.x.flask_restful import openapi_metadata, OpenAPIIntegrationMixin
from flask_x_openapi_schema import BaseRespModel

# Create a Flask app with OpenAPI support
app = Flask(__name__)
class OpenAPIApi(OpenAPIIntegrationMixin, Api):
    pass
api = OpenAPIApi(app)

# Define request and response models
class ItemRequest(BaseModel):
    name: str = Field(..., description="Item name")
    price: float = Field(..., description="Item price")

class ItemResponse(BaseRespModel):
    id: str = Field(..., description="Item ID")
    name: str = Field(..., description="Item name")
    price: float = Field(..., description="Item price")

# Create a resource with OpenAPI metadata
class ItemResource(Resource):
    @openapi_metadata(
        summary="Create a new item",
        tags=["Items"],
        operation_id="createItem"
    )
    def post(self, x_request_body: ItemRequest):
        # The request body is automatically parsed and validated
        return ItemResponse(
            id="123",
            name=x_request_body.name,
            price=x_request_body.price
        ), 201

# Register the resource
api.add_resource(ItemResource, "/items")

# Generate OpenAPI schema
with open("openapi.yaml", "w") as f:
    f.write(api.generate_openapi_schema(
        title="Items API",
        version="1.0.0",
        description="API for managing items"
    ))
```

### Flask.MethodView Example

```python
from flask import Flask, Blueprint
from flask.views import MethodView
from pydantic import BaseModel, Field
from flask_x_openapi_schema.x.flask import openapi_metadata, OpenAPIMethodViewMixin
from flask_x_openapi_schema import BaseRespModel

# Create a Flask app
app = Flask(__name__)

# Define request and response models
class ItemRequest(BaseModel):
    name: str = Field(..., description="Item name")
    price: float = Field(..., description="Item price")

class ItemResponse(BaseRespModel):
    id: str = Field(..., description="Item ID")
    name: str = Field(..., description="Item name")
    price: float = Field(..., description="Item price")

# Create a MethodView with OpenAPI metadata
class ItemView(OpenAPIMethodViewMixin, MethodView):
    @openapi_metadata(
        summary="Create a new item",
        tags=["Items"],
        operation_id="createItem"
    )
    def post(self, x_request_body: ItemRequest):
        # The request body is automatically parsed and validated
        return ItemResponse(
            id="123",
            name=x_request_body.name,
            price=x_request_body.price
        ), 201

# Register the view
blueprint = Blueprint("api", __name__)
blueprint.add_url_rule("/items", view_func=ItemView.as_view("items"))
app.register_blueprint(blueprint)
```

## Documentation

### [Project Overview](README.md)
- High-level overview of the project
- Core features and architecture
- Component diagrams

### [Usage Guide](usage_guide.md)
- Basic setup and configuration
- Advanced usage patterns
- Best practices and troubleshooting

### [Core Components](core_components.md)
- Detailed explanation of components
- How components work together
- Implementation details

### [Internationalization](internationalization.md)
- Using I18nString and I18nBaseModel
- Language management
- Advanced i18n techniques

### [File Uploads](file_uploads.md)
- Basic and multiple file uploads
- File validation and security
- Best practices

## Examples

The [examples](../examples/) directory contains complete examples demonstrating various features:

- Basic API with OpenAPI documentation
- Internationalization support
- File upload handling
- Using with Flask.MethodView

## API Reference

### Core Classes

- `openapi_metadata`: Decorator for adding OpenAPI metadata to API endpoints (available in both Flask and Flask-RESTful versions)
- `OpenAPISchemaGenerator`: Generates OpenAPI schemas from Flask resources
- `OpenAPIIntegrationMixin`: Mixin for Flask-RESTful API integration
- `OpenAPIBlueprintMixin`: Mixin for Flask Blueprint integration
- `OpenAPIMethodViewMixin`: Mixin for Flask.MethodView integration
- `BaseRespModel`: Base model for API responses
- `I18nStr`: Internationalized string support
- `FileUploadModel`: Base model for file uploads

### Utility Functions

- `responses_schema`: Creates response schemas for OpenAPI
- `success_response`: Creates success response schemas
- `error_response_schema`: Creates error response schemas
- `pydantic_to_openapi_schema`: Converts Pydantic models to OpenAPI schemas

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.