# Flask-X-OpenAPI-Schema

![Python Version from PEP 621 TOML](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2FStrayDragon%2Fflask-x-openapi-schema%2Frefs%2Fheads%2Fmain%2Fpyproject.toml%3Ftoken%3DGHSAT0AAAAAACXCLWMTUK6B6EI7XGMEEZHI2AHLBYA)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![GitHub](https://img.shields.io/badge/github-flask--x--openapi--schema-lightgrey.svg)](https://github.com/StrayDragon/flask-x-openapi-schema)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![CI](https://github.com/StrayDragon/flask-x-openapi-schema/actions/workflows/ci.yaml/badge.svg?branch=main)](https://github.com/StrayDragon/flask-x-openapi-schema/actions/workflows/ci.yaml)
[![Codecov](https://codecov.io/gh/straydragon/flask-x-openapi-schema/branch/main/graph/badge.svg)](https://codecov.io/gh/straydragon/flask-x-openapi-schema)

A powerful utility for automatically generating OpenAPI schemas support Flask(MethodView) and Flask-RESTful(Resource) applications and Pydantic models to simplify API documentation with minimal effort.

## 📚 Documentation

Full documentation is available in the [docs](./docs) directory.

## 🚀 Quick Start

```bash
# Install the package
uv pip install flask-x-openapi-schema

# With Flask-RESTful support
uv pip install flask-x-openapi-schema[flask-restful]
```

## ✨ Features

- **Framework Support**: Works with both Flask and Flask-RESTful applications
- **Auto-Generation**: Generate OpenAPI schemas from Flask-RESTful resources and Flask.MethodView classes
- **Pydantic Integration**: Seamlessly convert Pydantic models to OpenAPI schemas
- **Smart Parameter Handling**: Inject request parameters from Pydantic models with configurable prefixes
- **Type Safety**: Preserve type annotations for better IDE support and validation
- **Multiple Formats**: Output schemas in YAML or JSON format
- **Internationalization**: Built-in i18n support for API documentation with thread-safe language switching
- **File Upload Support**: Simplified handling of file uploads with validation
- **Flexible Architecture**: Modular design with framework-specific implementations
- **Performance Optimized**: Caching of static information for improved performance

## 📦 Installation

### Development Setup

This project uses `uv` for package management and `ruff` for linting and formatting and need `just` for project management:

```bash
# Install all dependencies including development ones
just sync-all-deps

# Format and lint code
just format-and-lintfix
```

## 🛠️ Basic Usage

See the [Usage Guide](./docs/usage_guide.md) for more detailed examples.

### Flask.MethodView Example

(diy) see and run [example](./examples/flask/app.py)

### Flask-RESTful Example

(diy) see and run [example](./examples/flask_restful/app.py)

## 📋 Key Features

### Framework-Specific Implementations

The library provides separate implementations for Flask and Flask-RESTful:

```python
# For Flask.MethodView
from flask_x_openapi_schema.x.flask import openapi_metadata

# For Flask-RESTful
from flask_x_openapi_schema.x.flask_restful import openapi_metadata
```

### Parameter Binding with Special Prefixes

The library binds parameters with special prefixes default, and can custom by yourself:

- `_x_body`: Request body from JSON
- `_x_query`: Query parameters
- `_x_path_<param_name>`: Path parameters
- `_x_file`: File uploads

#### Custom Parameter Prefixes

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

### I18n Support

```python
from flask_x_openapi_schema import I18nStr, set_current_language

# Set the current language
set_current_language("zh-Hans")

@openapi_metadata(
    summary=I18nStr({
        "en-US": "Get an item",
        "zh-Hans": "获取一个项目",
        "ja-JP": "アイテムを取得する"
    }),
    ...
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
def post(self, _x_file: ImageUploadModel):
    # File is automatically injected and validated
    return {"filename": _x_file.file.filename}
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

# View HTML coverage report
# Open htmlcov/index.html in your browser
```

## 📊 Benchmarking

The project includes benchmarking tools to measure performance:

```bash
# Run benchmarks and generate report
just benchmark
```

## 📖 More Docs

- [Core Components](./docs/core_components.md)
- [Internationalization](./docs/internationalization.md)
- [File Uploads](./docs/file_uploads.md)
- [...](./docs/)

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