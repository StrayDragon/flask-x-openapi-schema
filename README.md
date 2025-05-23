# Flask-X-OpenAPI-Schema

[![GitHub](https://img.shields.io/badge/github-flask--x--openapi--schema-lightgrey.svg)](https://github.com/StrayDragon/flask-x-openapi-schema)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/flask-x-openapi-schema)](https://pypi.org/project/flask-x-openapi-schema/)
[![PyPI - Version](https://img.shields.io/pypi/v/flask-x-openapi-schema)](https://pypi.org/project/flask-x-openapi-schema/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![CI](https://github.com/StrayDragon/flask-x-openapi-schema/actions/workflows/ci.yaml/badge.svg?branch=main)](https://github.com/StrayDragon/flask-x-openapi-schema/actions/workflows/ci.yaml)
[![Codecov](https://codecov.io/gh/straydragon/flask-x-openapi-schema/branch/main/graph/badge.svg)](https://codecov.io/gh/straydragon/flask-x-openapi-schema)

A powerful utility for automatically generating OpenAPI schemas support Flask(MethodView) and Flask-RESTful(Resource) applications and Pydantic models to simplify API documentation with minimal effort.

## 📚 Documentation

Full documentation is available in the [docs](./docs) directory and online at [https://straydragon.github.io/flask-x-openapi-schema/](https://straydragon.github.io/flask-x-openapi-schema/).

## 📝 Examples

Complete examples are available in the [examples/](https://github.com/StrayDragon/flask-x-openapi-schema/tree/main/examples) directory. These examples demonstrate all the features of the library, including:

- Parameter binding (path, query, body)
- File uploads (images, documents, audio, video)
- Internationalization
- Response models
- OpenAPI schema generation

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

## 🚀 Performance

Flask-X-OpenAPI-Schema is designed with performance in mind. Our benchmarks show minimal overhead when using the library compared to standard Flask and Flask-RESTful applications.

### Benchmark Results

![](./benchmarks/results/performance_charts.png)

| Framework     | Endpoint | Requests | Success Rate | Median (ms) | 95%ile (ms) | Avg (ms) | RPS    | Overhead |
|---------------|----------|----------|--------------|-------------|-------------|----------|--------|----------|
| Flask         | Standard | 7930     | 100.00%      | 270.00      | 270.00      | 306.01   | 132.18 | baseline |
| Flask         | OpenAPI  | 7797     | 100.00%      | 280.00      | 280.00      | 312.85   | 129.96 | +2.23%   |
| Flask-RESTful | Standard | 7654     | 100.00%      | 310.00      | 310.00      | 348.35   | 127.30 | baseline |
| Flask-RESTful | OpenAPI  | 7603     | 99.68%       | 310.00      | 310.00      | 358.92   | 126.45 | +3.03%   |

These benchmarks were conducted using Locust with 200 concurrent users and a ramp-up rate of 20 users per second over a 60-second test period. The tests measured the performance of identical endpoints implemented with and without Flask-X-OpenAPI-Schema.

For more detailed benchmarks and to run your own performance tests, see the [benchmarks](./benchmarks) directory.

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

# Run tests in parallel for faster execution
just test-parallel

# Run tests in parallel with specific number of workers
just test-parallel '' 4

# View HTML coverage report
# Open htmlcov/index.html in your browser
```
See [Testing Guide](./docs/testing.md) for more details on testing.

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
