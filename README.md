# Flask-X-OpenAPI-Schema

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A powerful utility for automatically generating OpenAPI schemas from Flask-RESTful resources, Flask.MethodView classes, and Pydantic models. Simplify your API documentation with minimal effort.

## 📚 Documentation

Full documentation is available in the [docs](./docs) directory.

## 🚀 Quick Start

```bash
# Install the package
pip install flask-x-openapi-schema

# With Flask-RESTful support
pip install flask-x-openapi-schema[restful]
```

## ✨ Features

- **Auto-Generation**: Generate OpenAPI schemas from Flask-RESTful resources and Flask.MethodView classes
- **Pydantic Integration**: Seamlessly convert Pydantic models to OpenAPI schemas
- **Smart Parameter Handling**: Automatically inject request parameters from Pydantic models
- **Type Safety**: Preserve type annotations for better IDE support and validation
- **Multiple Formats**: Output schemas in YAML or JSON format
- **Internationalization**: Built-in i18n support for API documentation
- **File Upload Support**: Simplified handling of file uploads
- **Flexible Architecture**: Optional Flask-RESTful dependency

## 📦 Installation

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
pip install flask-x-openapi-schema[restful]
# or
pip install -e .[restful]
```

## 🛠️ Basic Usage

```python
from flask import Flask
from flask_restful import Resource, Api
from pydantic import BaseModel, Field
from flask_x_openapi_schema import openapi_metadata, OpenAPIIntegrationMixin

# Create a Flask app with OpenAPI support
app = Flask(__name__)
class OpenAPIApi(OpenAPIIntegrationMixin, Api):
    pass
api = OpenAPIApi(app)

# Define a Pydantic model for the request
class ItemRequest(BaseModel):
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
        return {"id": "123", "name": x_request_body.name}, 201

# Register the resource
api.add_resource(ItemResource, "/items")

# Generate OpenAPI schema
with open("openapi.yaml", "w") as f:
    f.write(api.generate_openapi_schema(
        title="Items API",
        version="1.0.0"
    ))
```

See the [Usage Guide](./docs/usage_guide.md) for more detailed examples.

## 📋 Key Features

### Auto-Detection of Parameters

The library automatically detects parameters with special prefixes:

- `x_request_body`: Request body from JSON
- `x_request_query`: Query parameters
- `x_request_path_<name>`: Path parameters
- `x_request_file`: File uploads

### Internationalization Support

```python
from flask_x_openapi_schema import I18nString

@openapi_metadata(
    summary=I18nString({
        "en-US": "Get an item",
        "zh-Hans": "获取一个项目"
    })
)
def get(self, item_id):
    # ...
```

### File Upload Support

```python
@openapi_metadata(
    summary="Upload an image"
)
def post(self, x_request_file: ImageUploadModel):
    # File is automatically injected and validated
    return {"filename": x_request_file.file.filename}
```

## 📖 Documentation

- [Installation Guide](./docs/index.md#installation)
- [Usage Guide](./docs/usage_guide.md)
- [Core Components](./docs/core_components.md)
- [Internationalization](./docs/internationalization.md)
- [File Uploads](./docs/file_uploads.md)
- [Examples](./examples/)

## 🧩 Components

- **Decorators**: `openapi_metadata` for adding metadata to endpoints
- **Schema Generator**: Converts resources to OpenAPI schemas
- **Integration Mixins**: Extends Flask-RESTful and Flask Blueprint
- **Response Models**: Type-safe response handling
- **Utility Functions**: Simplifies schema creation

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
