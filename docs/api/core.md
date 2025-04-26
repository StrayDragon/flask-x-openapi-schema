# Core API Reference

This section provides detailed documentation for the core components of Flask-X-OpenAPI-Schema.

## Configuration

The core configuration module provides classes and functions for configuring the behavior of the library.

```python
from flask_x_openapi_schema.core.config import ConventionalPrefixConfig, configure_prefixes

# Create a custom configuration
custom_config = ConventionalPrefixConfig(
    request_body_prefix="req_body",
    request_query_prefix="req_query",
    request_path_prefix="req_path",
    request_file_prefix="req_file"
)

# Configure globally
configure_prefixes(custom_config)
```

## Schema Generator

The schema generator is responsible for converting Python types and Pydantic models to OpenAPI schema definitions.

```python
from flask_x_openapi_schema.core.schema_generator import generate_schema_from_model

# Generate schema from a Pydantic model
schema = generate_schema_from_model(MyModel)
```

## Decorator Base

The decorator base provides the foundation for the framework-specific decorators.

```python
from flask_x_openapi_schema.core.decorator_base import OpenAPIMetadataBase

# The base class is not typically used directly, but through framework-specific implementations
```

## Cache

The cache module provides caching mechanisms to improve performance by storing static information.

```python
from flask_x_openapi_schema.core.cache import get_cached_schema, cache_schema

# Cache a schema
cache_schema("my_model", schema_dict)

# Get a cached schema
schema = get_cached_schema("my_model")
```

## Utilities

The utilities module provides helper functions for working with types, schemas, and other common operations.

```python
from flask_x_openapi_schema.core.utils import get_type_hints_with_annotations

# Get type hints with annotations
hints = get_type_hints_with_annotations(my_function)
```
