# Getting Started with Flask-X-OpenAPI-Schema

This guide will help you get started with Flask-X-OpenAPI-Schema, a powerful utility for automatically generating OpenAPI schemas from Flask and Flask-RESTful applications.

## Installation

### Basic Installation

```bash
# Using pip
pip install flask-x-openapi-schema

# Using uv
uv pip install flask-x-openapi-schema
```

### With Flask-RESTful Support

```bash
# Using pip
pip install flask-x-openapi-schema[flask-restful]

# Using uv
uv pip install flask-x-openapi-schema[flask-restful]
```

## Basic Usage

Flask-X-OpenAPI-Schema provides separate implementations for Flask and Flask-RESTful. Choose the one that matches your application.

### With Flask.MethodView

```python
from flask import Flask, Blueprint, jsonify
from flask.views import MethodView
from pydantic import BaseModel, Field

from flask_x_openapi_schema.x.flask import openapi_metadata, OpenAPIMethodViewMixin
from flask_x_openapi_schema import OpenAPIMetaResponse, OpenAPIMetaResponseItem

# Define request and response models
class ItemRequest(BaseModel):
    name: str = Field(..., description="Item name")
    description: str = Field(None, description="Item description")
    price: float = Field(..., description="Item price")

class ItemResponse(BaseModel):
    id: str = Field(..., description="Item ID")
    name: str = Field(..., description="Item name")
    description: str = Field(None, description="Item description")
    price: float = Field(..., description="Item price")

# Create a Flask app
app = Flask(__name__)
blueprint = Blueprint("api", __name__, url_prefix="/api")

# Create a MethodView class
class ItemView(OpenAPIMethodViewMixin, MethodView):
    @openapi_metadata(
        summary="Get all items",
        description="Retrieve a list of all items",
        tags=["items"],
        operation_id="getItems",
        responses=OpenAPIMetaResponse(
            responses={
                "200": OpenAPIMetaResponseItem(
                    model=ItemResponse,
                    description="List of items retrieved successfully",
                ),
            }
        ),
    )
    def get(self):
        # Implementation...
        items = [
            {"id": "1", "name": "Item 1", "description": "First item", "price": 10.99},
            {"id": "2", "name": "Item 2", "description": "Second item", "price": 20.99},
        ]
        return jsonify(items), 200

    @openapi_metadata(
        summary="Create a new item",
        description="Create a new item with the provided information",
        tags=["items"],
        operation_id="createItem",
        responses=OpenAPIMetaResponse(
            responses={
                "201": OpenAPIMetaResponseItem(
                    model=ItemResponse,
                    description="Item created successfully",
                ),
                "400": OpenAPIMetaResponseItem(
                    description="Invalid request data",
                ),
            }
        ),
    )
    def post(self, _x_body: ItemRequest):
        # Implementation...
        # _x_body is automatically populated from the request JSON
        item = {
            "id": "3",
            "name": _x_body.name,
            "description": _x_body.description,
            "price": _x_body.price,
        }
        return jsonify(item), 201

# Register the view
ItemView.register_to_blueprint(blueprint, "/items", "items")

# Register the blueprint
app.register_blueprint(blueprint)

# Generate OpenAPI schema
@app.route("/openapi.yaml")
def get_openapi_spec():
    from flask_x_openapi_schema.x.flask.views import MethodViewOpenAPISchemaGenerator
    import yaml

    generator = MethodViewOpenAPISchemaGenerator(
        title="My API",
        version="1.0.0",
        description="API for managing items",
    )

    # Process MethodView resources
    generator.process_methodview_resources(blueprint)

    # Generate the schema
    schema = generator.generate_schema()

    # Convert to YAML
    yaml_content = yaml.dump(schema, sort_keys=False, default_flow_style=False)

    return yaml_content, 200, {"Content-Type": "text/yaml"}

# Serve Swagger UI
@app.route("/")
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>API Documentation</title>
        <link rel="stylesheet" type="text/css" href="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/5.9.1/swagger-ui.min.css">
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/5.9.1/swagger-ui-bundle.min.js"></script>
        <script>
            window.onload = function() {
                SwaggerUIBundle({
                    url: "/openapi.yaml",
                    dom_id: "#swagger-ui",
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIBundle.SwaggerUIStandalonePreset
                    ],
                    layout: "BaseLayout"
                });
            }
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(debug=True)
```

### With Flask-RESTful

```python
from flask import Flask
from flask_restful import Resource
from pydantic import BaseModel, Field

from flask_x_openapi_schema.x.flask_restful import openapi_metadata, OpenAPIIntegrationMixin
from flask_x_openapi_schema import OpenAPIMetaResponse, OpenAPIMetaResponseItem

# Define request and response models
class ItemRequest(BaseModel):
    name: str = Field(..., description="Item name")
    description: str = Field(None, description="Item description")
    price: float = Field(..., description="Item price")

class ItemResponse(BaseModel):
    id: str = Field(..., description="Item ID")
    name: str = Field(..., description="Item name")
    description: str = Field(None, description="Item description")
    price: float = Field(..., description="Item price")

# Create a Flask app
app = Flask(__name__)

# Create an OpenAPI-enabled API
class OpenAPIApi(OpenAPIIntegrationMixin, Api):
    pass

api = OpenAPIApi(app)

# Create a resource
class ItemListResource(Resource):
    @openapi_metadata(
        summary="Get all items",
        description="Retrieve a list of all items",
        tags=["items"],
        operation_id="getItems",
        responses=OpenAPIMetaResponse(
            responses={
                "200": OpenAPIMetaResponseItem(
                    model=ItemResponse,
                    description="List of items retrieved successfully",
                ),
            }
        ),
    )
    def get(self):
        # Implementation...
        items = [
            {"id": "1", "name": "Item 1", "description": "First item", "price": 10.99},
            {"id": "2", "name": "Item 2", "description": "Second item", "price": 20.99},
        ]
        return items, 200

    @openapi_metadata(
        summary="Create a new item",
        description="Create a new item with the provided information",
        tags=["items"],
        operation_id="createItem",
        responses=OpenAPIMetaResponse(
            responses={
                "201": OpenAPIMetaResponseItem(
                    model=ItemResponse,
                    description="Item created successfully",
                ),
                "400": OpenAPIMetaResponseItem(
                    description="Invalid request data",
                ),
            }
        ),
    )
    def post(self, _x_body: ItemRequest):
        # Implementation...
        # _x_body is automatically populated from the request JSON
        item = {
            "id": "3",
            "name": _x_body.name,
            "description": _x_body.description,
            "price": _x_body.price,
        }
        return item, 201

class ItemResource(Resource):
    @openapi_metadata(
        summary="Get an item by ID",
        description="Retrieve an item by its unique identifier",
        tags=["items"],
        operation_id="getItem",
        responses=OpenAPIMetaResponse(
            responses={
                "200": OpenAPIMetaResponseItem(
                    model=ItemResponse,
                    description="Item retrieved successfully",
                ),
                "404": OpenAPIMetaResponseItem(
                    description="Item not found",
                ),
            }
        ),
    )
    def get(self, item_id: str):
        # Implementation...
        if item_id not in ["1", "2"]:
            return {"error": "Item not found"}, 404

        item = {
            "id": item_id,
            "name": f"Item {item_id}",
            "description": f"Item {item_id} description",
            "price": float(item_id) * 10.99,
        }
        return item, 200

# Register the resources
api.add_resource(ItemListResource, "/api/items")
api.add_resource(ItemResource, "/api/items/<string:item_id>")

# Generate OpenAPI schema
@app.route("/openapi.yaml")
def get_openapi_spec():
    import yaml

    schema = api.generate_openapi_schema(
        title="My API",
        version="1.0.0",
        description="API for managing items",
        output_format="json",
    )

    # Convert to YAML
    yaml_content = yaml.dump(schema, sort_keys=False, default_flow_style=False)

    return yaml_content, 200, {"Content-Type": "text/yaml"}

# Serve Swagger UI
@app.route("/")
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>API Documentation</title>
        <link rel="stylesheet" type="text/css" href="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/5.9.1/swagger-ui.min.css">
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/5.9.1/swagger-ui-bundle.min.js"></script>
        <script>
            window.onload = function() {
                SwaggerUIBundle({
                    url: "/openapi.yaml",
                    dom_id: "#swagger-ui",
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIBundle.SwaggerUIStandalonePreset
                    ],
                    layout: "BaseLayout"
                });
            }
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(debug=True)
```

## Parameter Binding

Flask-X-OpenAPI-Schema uses special prefixes to bind request parameters to function arguments:

### Request Body

Use the `_x_body` prefix to bind the request body:

```python
@openapi_metadata(
    summary="Create a new item",
    # ...
)
def post(self, _x_body: ItemRequest):
    # _x_body is automatically populated from the request JSON
    item = {
        "id": "3",
        "name": _x_body.name,
        "description": _x_body.description,
        "price": _x_body.price,
    }
    return item, 201
```

### Query Parameters

Use the `_x_query` prefix to bind query parameters:

```python
class ItemQueryParams(BaseModel):
    category: str = Field(None, description="Filter by category")
    min_price: float = Field(None, description="Minimum price")
    max_price: float = Field(None, description="Maximum price")

@openapi_metadata(
    summary="Get all items",
    # ...
)
def get(self, _x_query: ItemQueryParams = None):
    # _x_query is automatically populated from the query parameters
    items = [...]

    if _x_query:
        if _x_query.category:
            items = [item for item in items if item["category"] == _x_query.category]

        if _x_query.min_price is not None:
            items = [item for item in items if item["price"] >= _x_query.min_price]

        if _x_query.max_price is not None:
            items = [item for item in items if item["price"] <= _x_query.max_price]

    return items, 200
```

### Path Parameters

Path parameters are automatically bound to function arguments with matching names:

```python
@openapi_metadata(
    summary="Get an item by ID",
    # ...
)
def get(self, item_id: str):
    # item_id is automatically populated from the path parameter
    if item_id not in ["1", "2"]:
        return {"error": "Item not found"}, 404

    item = {
        "id": item_id,
        "name": f"Item {item_id}",
        "description": f"Item {item_id} description",
        "price": float(item_id) * 10.99,
    }
    return item, 200
```

### File Uploads

Use the `_x_file` prefix to bind file uploads:

```python
from flask_x_openapi_schema import ImageUploadModel

@openapi_metadata(
    summary="Upload an item image",
    # ...
)
def post(self, item_id: str, _x_file: ImageUploadModel):
    # _x_file.file is automatically populated from the uploaded file
    file = _x_file.file

    # Save the file
    file.save(f"uploads/{item_id}_{file.filename}")

    return {"message": "File uploaded successfully"}, 201
```

## Response Models

Flask-X-OpenAPI-Schema provides a `BaseRespModel` class for creating response models that can be automatically converted to Flask responses:

```python
from flask_x_openapi_schema import BaseRespModel
from pydantic import Field

class ItemResponse(BaseRespModel):
    id: str = Field(..., description="Item ID")
    name: str = Field(..., description="Item name")
    description: str = Field(None, description="Item description")
    price: float = Field(..., description="Item price")

@openapi_metadata(
    summary="Get an item by ID",
    # ...
)
def get(self, item_id: str):
    # ...
    response = ItemResponse(
        id=item_id,
        name=f"Item {item_id}",
        description=f"Item {item_id} description",
        price=float(item_id) * 10.99,
    )

    # Convert to Flask response
    return response.to_response(200)
```

## Complete Examples

For complete working examples, check out the example applications in the repository:

- [Flask MethodView Example](https://github.com/StrayDragon/flask-x-openapi-schema/tree/main/examples/flask/app.py): A complete example using Flask.MethodView
- [Flask-RESTful Example](https://github.com/StrayDragon/flask-x-openapi-schema/tree/main/examples/flask_restful/app.py): A complete example using Flask-RESTful
- [Response Example (Flask)](https://github.com/StrayDragon/flask-x-openapi-schema/tree/main/examples/flask/response_example.py): Example demonstrating structured responses with OpenAPIMetaResponse
- [Response Example (Flask-RESTful)](https://github.com/StrayDragon/flask-x-openapi-schema/tree/main/examples/flask_restful/response_example.py): Example demonstrating structured responses with OpenAPIMetaResponse

These examples demonstrate all the features of the library, including:

- Parameter binding (path, query, body)
- File uploads (images, documents, audio, video)
- Internationalization
- Response models
- OpenAPI schema generation

You can run the examples using the provided justfile commands:

```bash
# Run the basic Flask MethodView example
just run-example-flask

# Run the basic Flask-RESTful example
just run-example-flask-restful
```

## Next Steps

Now that you've learned the basics of Flask-X-OpenAPI-Schema, you can explore more advanced features:

- [Core Components](./core_components.md): Learn about the core components of Flask-X-OpenAPI-Schema
- [File Uploads](./file_uploads.md): Learn how to handle file uploads
- [Internationalization](./internationalization.md): Learn how to create multilingual API documentation
