# Flask-RESTful API Reference

This section provides detailed documentation for the Flask-RESTful-specific components of Flask-X-OpenAPI-Schema.

## Decorators

The Flask-RESTful decorators module provides decorators for adding OpenAPI metadata to Flask-RESTful resources.

```python
from flask_x_openapi_schema.x.flask_restful import openapi_metadata

class ItemResource(Resource):
    @openapi_metadata(
        summary="Get an item by ID",
        description="Retrieve a specific item by its unique identifier",
        tags=["items"]
    )
    def get(self, item_id):
        # Method implementation
        pass
```

## Resources

The resources module provides base classes for Flask-RESTful resources with OpenAPI integration.

```python
from flask_x_openapi_schema.x.flask_restful.resources import OpenAPIResource

class ItemResource(OpenAPIResource):
    @openapi_metadata(
        summary="Get all items",
        tags=["items"]
    )
    def get(self):
        # Method implementation
        pass
```

## Utilities

The utilities module provides helper functions for working with Flask-RESTful resources and requests.

```python
from flask_x_openapi_schema.x.flask_restful.utils import extract_reqparse_args

# Extract arguments from a RequestParser
args = extract_reqparse_args(parser)
```
