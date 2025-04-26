# Flask-X-OpenAPI-Schema

A powerful utility for automatically generating OpenAPI schemas from Flask-RESTful resources, Flask.MethodView classes, and Pydantic models to simplify API documentation with minimal effort.

## Features

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

## Installation

```bash
# Install the package
uv pip install flask-x-openapi-schema

# With Flask-RESTful support
uv pip install flask-x-openapi-schema[flask-restful]
```

## Quick Start

Check out the [Getting Started](getting_started.md) guide for a quick introduction to using Flask-X-OpenAPI-Schema.

## Components

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

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/StrayDragon/flask-x-openapi-schema/blob/main/LICENSE) file for details.
