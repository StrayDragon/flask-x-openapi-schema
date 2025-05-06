# Core Components of Flask-X-OpenAPI-Schema

This document provides an overview of the core components of Flask-X-OpenAPI-Schema and how they work together to generate OpenAPI schemas for Flask and Flask-RESTful applications.

## Architecture Overview

Flask-X-OpenAPI-Schema is designed with a modular architecture that separates core functionality from framework-specific implementations. This allows for easy extension to support additional frameworks in the future.

```
graph TD
    A[Core Components] --> B[Schema Generator]
    A --> C[Configuration]
    A --> D[Models]
    A --> E[Utilities]

    F[Framework-Specific] --> G[Flask Implementation]
    F --> H[Flask-RESTful Implementation]

    B --> G
    B --> H
    C --> G
    C --> H
    D --> G
    D --> H
    E --> G
    E --> H
```

## Key Components

### 1. Decorators

The `openapi_metadata` decorator is the primary interface for adding OpenAPI metadata to your API endpoints. There are separate implementations for Flask and Flask-RESTful:

```python
# For Flask.MethodView
from flask_x_openapi_schema.x.flask import openapi_metadata

# For Flask-RESTful
from flask_x_openapi_schema.x.flask_restful import openapi_metadata

```

#### Usage

```python
@openapi_metadata(
    summary="Get an item",
    description="Retrieve an item by its ID",
    tags=["items"],
    operation_id="getItem",
    responses=OpenAPIMetaResponse(
        responses={
            "200": OpenAPIMetaResponseItem(
                model=ItemResponse,
                description="Item retrieved successfully",
            ),
            "404": OpenAPIMetaResponseItem(
                model=ErrorResponse,
                description="Item not found",
            ),
        }
    ),
)
def get(self, item_id: str):
    # Implementation...

```

### 2. Schema Generator

The schema generator is responsible for converting your API endpoints into OpenAPI schemas. It handles:

- Converting Pydantic models to OpenAPI schemas
- Processing route information
- Generating path and component definitions
- Handling parameter binding

#### Flask Implementation

```python
from flask_x_openapi_schema.x.flask.views import MethodViewOpenAPISchemaGenerator

generator = MethodViewOpenAPISchemaGenerator(
    title="My API",
    version="1.0.0",
    description="API description",
)

# Process MethodView resources
generator.process_methodview_resources(blueprint)

# Generate the schema
schema = generator.generate_schema()

```

#### Flask-RESTful Implementation

```python
# Create an OpenAPI-enabled API
from flask_x_openapi_schema.x.flask_restful import OpenAPIIntegrationMixin
from flask_restful import Api

class OpenAPIApi(OpenAPIIntegrationMixin, Api):
    pass

api = OpenAPIApi(app)

# Generate the schema
schema = api.generate_openapi_schema(
    title="My API",
    version="1.0.0",
    description="API description",
)

```

### 3. Parameter Binding

Flask-X-OpenAPI-Schema uses special prefixes to bind request parameters to function arguments:

- `_x_body`: Request body from JSON
- `_x_query`: Query parameters
- `_x_path_<param_name>`: Path parameters
- `_x_file`: File uploads

#### Custom Parameter Prefixes

You can customize the parameter prefixes using the `ConventionalPrefixConfig` class:

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

### 4. Response Models

Flask-X-OpenAPI-Schema provides a `BaseRespModel` class for creating response models that can be automatically converted to Flask responses:

```python
from flask_x_openapi_schema import BaseRespModel
from pydantic import Field

class ItemResponse(BaseRespModel):
    id: str = Field(..., description="Item ID")
    name: str = Field(..., description="Item name")
    price: float = Field(..., description="Item price")

# In your endpoint
def get(self, item_id: str):
    # ...
    return ItemResponse(id="123", name="Example", price=10.99).to_response(200)

```

### 5. OpenAPIMetaResponse

The `OpenAPIMetaResponse` class provides a structured way to define response schemas for different status codes:

```python
from flask_x_openapi_schema import OpenAPIMetaResponse, OpenAPIMetaResponseItem

@openapi_metadata(
    summary="Create an item",
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
def post(self, _x_body: ItemRequest):
    # Implementation...

```

## Integration with Flask

### 1. MethodView Integration

Flask-X-OpenAPI-Schema provides the `OpenAPIMethodViewMixin` class for integrating with Flask's `MethodView`:

```python
from flask.views import MethodView
from flask_x_openapi_schema.x.flask import OpenAPIMethodViewMixin, openapi_metadata

class ItemView(OpenAPIMethodViewMixin, MethodView):
    @openapi_metadata(
        summary="Get all items",
        # ...
    )
    def get(self):
        # Implementation...

    @openapi_metadata(
        summary="Create a new item",
        # ...
    )
    def post(self, _x_body: ItemRequest):
        # Implementation...

# Register the view
ItemView.register_to_blueprint(blueprint, "/items", "items")

```

### 2. Schema Generation

```python
from flask_x_openapi_schema.x.flask.views import MethodViewOpenAPISchemaGenerator

@app.route("/openapi.yaml")
def get_openapi_spec():
    generator = MethodViewOpenAPISchemaGenerator(
        title="My API",
        version="1.0.0",
        description="API description",
    )

    # Process MethodView resources
    generator.process_methodview_resources(blueprint)

    # Generate the schema
    schema = generator.generate_schema()

    # Convert to YAML
    import yaml
    yaml_content = yaml.dump(schema, sort_keys=False, default_flow_style=False)

    return yaml_content, 200, {"Content-Type": "text/yaml"}

```

## Integration with Flask-RESTful

### 1. Resource Integration

Flask-X-OpenAPI-Schema integrates with Flask-RESTful's `Resource` class:

```python
from flask_restful import Resource
from flask_x_openapi_schema.x.flask_restful import openapi_metadata

class ItemResource(Resource):
    @openapi_metadata(
        summary="Get an item",
        # ...
    )
    def get(self, item_id: str):
        # Implementation...

    @openapi_metadata(
        summary="Update an item",
        # ...
    )
    def put(self, item_id: str, _x_body: ItemRequest):
        # Implementation...

# Register the resource
api.add_resource(ItemResource, "/items/<string:item_id>")

```

### 2. API Integration

Flask-X-OpenAPI-Schema provides the `OpenAPIIntegrationMixin` class for integrating with Flask-RESTful's `Api`:

```python
from flask_restful import Api
from flask_x_openapi_schema.x.flask_restful import OpenAPIIntegrationMixin

class OpenAPIApi(OpenAPIIntegrationMixin, Api):
    pass

api = OpenAPIApi(app)

# Register resources
# ...

# Generate OpenAPI schema
@app.route("/openapi.yaml")
def get_openapi_spec():
    schema = api.generate_openapi_schema(
        title="My API",
        version="1.0.0",
        description="API description",
    )

    # Convert to YAML
    import yaml
    yaml_content = yaml.dump(schema, sort_keys=False, default_flow_style=False)

    return yaml_content, 200, {"Content-Type": "text/yaml"}

```

## Performance Optimization

Flask-X-OpenAPI-Schema includes several performance optimizations:

1. **Caching**: Static information is cached to improve performance, especially for OpenAPI documentation generation.
1. **Lazy Loading**: Components are loaded only when needed.
1. **Efficient Parameter Binding**: Parameters are bound efficiently using type annotations.

## Conclusion

The core components of Flask-X-OpenAPI-Schema work together to provide a powerful and flexible system for generating OpenAPI schemas from Flask and Flask-RESTful applications. By separating core functionality from framework-specific implementations, the library can be easily extended to support additional frameworks in the future.
