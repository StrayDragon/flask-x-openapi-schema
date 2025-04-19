# Flask-X-OpenAPI-Schema

[![Python](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Coverage](https://img.shields.io/badge/coverage-needs%20improvement-yellow.svg)](htmlcov/index.html)
[![GitHub](https://img.shields.io/badge/github-flask--x--openapi--schema-lightgrey.svg)](https://github.com/StrayDragon/flask-x-openapi-schema)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

A powerful utility for automatically generating OpenAPI schemas from Flask and Flask-RESTful applications. Seamlessly integrates with Flask.MethodView classes and Pydantic models to simplify API documentation with minimal effort.

## 📚 Documentation

Full documentation is available in the [docs](./docs) directory.

## 🚀 Quick Start

```bash
# Install the package
pip install flask-x-openapi-schema

# With Flask-RESTful support
pip install flask-x-openapi-schema[flask-restful]
```

## ✨ Features

- **Framework Support**: Works with both Flask and Flask-RESTful applications
- **Auto-Generation**: Generate OpenAPI schemas from Flask-RESTful resources and Flask.MethodView classes
- **Pydantic Integration**: Seamlessly convert Pydantic models to OpenAPI schemas
- **Smart Parameter Handling**: Automatically inject request parameters from Pydantic models with configurable prefixes
- **Type Safety**: Preserve type annotations for better IDE support and validation
- **Multiple Formats**: Output schemas in YAML or JSON format
- **Internationalization**: Built-in i18n support for API documentation with thread-safe language switching
- **File Upload Support**: Simplified handling of file uploads with validation
- **Flexible Architecture**: Modular design with framework-specific implementations
- **Performance Optimized**: Caching of static information for improved performance

## 📦 Installation

### Basic Installation

```bash
# Install from PyPI
pip install flask-x-openapi-schema

# From the repository root using uv (recommended)
uv pip install -e .

# Or using pip
pip install -e .
```

### Optional Dependencies

By default, only Flask, Pydantic, and PyYAML are installed. For Flask-RESTful integration:

```bash
# Using uv (recommended)
uv pip install flask-x-openapi-schema[flask-restful]
# or for development
uv pip install -e .[flask-restful]

# Using pip
pip install flask-x-openapi-schema[flask-restful]
# or
pip install -e .[flask-restful]
```

### Development Setup

This project uses `uv` for package management and `ruff` for linting and formatting:

```bash
# Install uv if you don't have it
pip install uv

# Install all dependencies including development ones
uv pip install -e .[dev,flask-restful]
# or using dependency groups
uv sync --all-extras

# Format and lint code
just format-and-lintfix
```

## 🛠️ Basic Usage

### Flask-RESTful Example

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

See the [Usage Guide](./docs/usage_guide.md) for more detailed examples.

## 📋 Key Features

### Framework-Specific Implementations

The library provides separate implementations for Flask and Flask-RESTful:

```python
# For Flask.MethodView
from flask_x_openapi_schema.x.flask import openapi_metadata, OpenAPIMethodViewMixin

# For Flask-RESTful
from flask_x_openapi_schema.x.flask_restful import openapi_metadata, OpenAPIIntegrationMixin
```

### Auto-Detection of Parameters

The library automatically detects parameters with special prefixes:

- `x_request_body`: Request body from JSON
- `x_request_query`: Query parameters
- `x_request_path_<param_name>`: Path parameters
- `x_request_file`: File uploads

### Configurable Parameter Prefixes

```python
from flask_x_openapi_schema import ConventionalPrefixConfig, configure_prefixes

# Create a custom configuration
custom_config = ConventionalPrefixConfig(
    request_body_prefix="req_body",
    request_query_prefix="req_query",
    request_path_prefix="req_path",
    request_file_prefix="req_file"
)

# Configure globally
configure_prefixes(custom_config)

# Or per-function
@openapi_metadata(
    summary="Test endpoint",
    prefix_config=custom_config
)
def my_function(req_body: MyModel, req_query: QueryModel):
    # Use custom prefixes
    return {"message": "Success"}
```

### Internationalization Support

```python
from flask_x_openapi_schema import I18nStr, set_current_language

# Set the current language
set_current_language("zh-Hans")

@openapi_metadata(
    summary=I18nStr({
        "en-US": "Get an item",
        "zh-Hans": "获取一个项目",
        "ja-JP": "アイテムを取得する"
    })
)
def get(self, item_id):
    # ...
```

### File Upload Support

```python
from flask_x_openapi_schema import ImageUploadModel

@openapi_metadata(
    summary="Upload an image"
)
def post(self, x_request_file: ImageUploadModel):
    # File is automatically injected and validated
    return {"filename": x_request_file.file.filename}
```

### Response Models

```python
from flask_x_openapi_schema import BaseRespModel
from pydantic import Field

class ItemResponse(BaseRespModel):
    id: str = Field(..., description="Item ID")
    name: str = Field(..., description="Item name")
    price: float = Field(..., description="Item price")
    
    # Will be automatically converted to a Flask response
    # return ItemResponse(id="123", name="Example", price=10.99), 200
```

## 🧪 Testing and Coverage

This project uses `pytest` for testing and `pytest-cov` for coverage reporting:

```bash
# Run tests with coverage report
just test

# Or manually
uv run pytest

# Run specific tests
uv run pytest tests/flask/

# View HTML coverage report
# Open htmlcov/index.html in your browser
```

## 📊 Benchmarking

The project includes benchmarking tools to measure performance:

```bash
# Run benchmarks and generate report
just benchmark

# View benchmark results
cat results/report.txt

# View performance charts
open results/performance_charts.png
```

## 📖 Documentation

- [Installation Guide](./docs/index.md#installation)
- [Usage Guide](./docs/usage_guide.md)
- [Core Components](./docs/core_components.md)
- [Internationalization](./docs/internationalization.md)
- [File Uploads](./docs/file_uploads.md)
- [Examples](./examples/)

## 🧩 Components

- **Core**: Base functionality shared across all implementations
  - **Schema Generator**: Converts resources to OpenAPI schemas
  - **Configuration**: Configurable parameter prefixes and settings
  - **Cache**: Performance optimization for schema generation
- **Framework-Specific**:
  - **Flask**: Support for Flask.MethodView classes
  - **Flask-RESTful**: Support for Flask-RESTful resources
- **Models**:
  - **Base Models**: Type-safe response handling
  - **File Models**: Simplified file upload handling
- **Internationalization**:
  - **I18nStr**: Multilingual string support
  - **Language Management**: Thread-safe language switching
- **Utilities**: Helper functions for schema creation and manipulation

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.