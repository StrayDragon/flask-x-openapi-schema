# Flask-X-OpenAPI-Schema Documentation

Welcome to the Flask-X-OpenAPI-Schema documentation! This library simplifies the generation of OpenAPI schemas from Flask-RESTful resources and Pydantic models, providing a seamless integration between Flask, Flask-RESTful, and Pydantic.

## Table of Contents

1. [Project Overview](README.md)
   - High-level overview of the project
   - Core features
   - Architecture diagrams

2. [Usage Guide](usage_guide.md)
   - Installation instructions
   - Basic setup
   - Advanced usage patterns
   - Best practices
   - Troubleshooting

3. [Core Components](core_components.md)
   - Detailed explanation of core components
   - How components work together
   - Implementation details

4. [Internationalization Support](internationalization.md)
   - Overview of i18n support
   - Using I18nString and I18nBaseModel
   - Language management
   - Advanced i18n techniques

5. [File Upload Handling](file_uploads.md)
   - Basic file uploads
   - Multiple file uploads
   - File upload models
   - Validation and security
   - Best practices

## Quick Start

```python
from flask import Flask
from flask_restful import Resource
from flask_x_openapi_schema import (
    OpenAPIIntegrationMixin,
    openapi_metadata,
    BaseRespModel,
)
from pydantic import BaseModel, Field

# Create a Flask app
app = Flask(__name__)

# Create an OpenAPI-enabled API
class OpenAPIApi(OpenAPIIntegrationMixin, Api):
    pass

# Initialize the API
api = OpenAPIApi(app)

# Define request and response models
class ItemRequest(BaseModel):
    name: str = Field(..., description="The name of the item")
    price: float = Field(..., description="The price of the item")

class ItemResponse(BaseRespModel):
    id: str = Field(..., description="The ID of the item")
    name: str = Field(..., description="The name of the item")
    price: float = Field(..., description="The price of the item")

# Define a resource
class ItemResource(Resource):
    @openapi_metadata(
        summary="Create a new item",
        description="Create a new item with the given data",
        tags=["Items"],
        operation_id="createItem",
    )
    def post(self, x_request_body: ItemRequest):
        # Create the item
        item_id = "123"  # Example ID

        # Return the created item
        return ItemResponse(
            id=item_id,
            name=x_request_body.name,
            price=x_request_body.price,
        ), 201

# Register the resource
api.add_resource(ItemResource, "/items")

# Generate OpenAPI schema
schema = api.generate_openapi_schema(
    title="Items API",
    version="1.0.0",
    description="API for managing items",
)

# Save the schema to a file
with open("openapi.yaml", "w") as f:
    f.write(schema)
```

## Key Features

- **Automatic OpenAPI Schema Generation**: Generate OpenAPI schemas from Flask-RESTful resources
- **Pydantic Integration**: Convert Pydantic models to OpenAPI schemas
- **Parameter Auto-Detection**: Automatically detect and inject request parameters from function signatures
- **Type Preservation**: Preserve type annotations from Pydantic models for better IDE support
- **Multiple Output Formats**: Output schemas in YAML or JSON format
- **Internationalization Support**: Support for i18n in API documentation
- **File Upload Handling**: Simplified handling of file uploads with automatic parameter injection

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the terms of the license included in the repository.