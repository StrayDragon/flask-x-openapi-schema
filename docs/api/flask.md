# Flask API Reference

This section provides detailed documentation for the Flask-specific components of Flask-X-OpenAPI-Schema.

## Decorators

The Flask decorators module provides decorators for adding OpenAPI metadata to Flask routes and MethodView classes.

```python
from flask_x_openapi_schema.x.flask import openapi_metadata

@openapi_metadata(
    summary="Get an item by ID",
    description="Retrieve a specific item by its unique identifier",
    tags=["items"]
)
def get_item(item_id):
    # Function implementation
    pass
```

## Views

The views module provides base classes for Flask MethodView with OpenAPI integration.

```python
from flask_x_openapi_schema.x.flask.views import OpenAPIMethodView

class ItemView(OpenAPIMethodView):
    @openapi_metadata(
        summary="Get all items",
        tags=["items"]
    )
    def get(self):
        # Method implementation
        pass
```

## Utilities

The utilities module provides helper functions for working with Flask routes and requests.

```python
from flask_x_openapi_schema.x.flask.utils import extract_path_params

# Extract path parameters from a Flask route
params = extract_path_params("/items/<int:item_id>")
```
