# Flask-X-OpenAPI-Schema Examples

This directory contains examples demonstrating how to use Flask-X-OpenAPI-Schema with different Flask frameworks.

## Examples Overview

1. **Flask MethodView Examples**:
   - `app.py` - Basic example with Flask MethodView
   - `response_example.py` - Example demonstrating structured responses with OpenAPIMetaResponse

2. **Flask-RESTful Examples**:
   - `app.py` - Basic example with Flask-RESTful
   - `response_example.py` - Example demonstrating structured responses with OpenAPIMetaResponse

All examples implement a simple Product API with the following features:

- CRUD operations for products
- Parameter binding (path, query, body)
- Request and response validation using Pydantic models
- OpenAPI schema generation
- Swagger UI for API documentation
- Rich console output for request/response visualization

## Prerequisites

Make sure you have installed Flask-X-OpenAPI-Schema with all required dependencies:

```bash
# Install the package with Flask-RESTful support
pip install -e .[flask-restful]

# Install rich for pretty console output
pip install rich
```

## Running the Examples

You can run the examples using the provided scripts:

```bash
# Run the basic Flask MethodView example
just run-example-flask

# Run the basic Flask-RESTful example
just run-example-flask-restful

# Run both basic examples sequentially
just run-examples

# Run the Flask MethodView response example
just run-response-example-flask

# Run the Flask-RESTful response example
just run-response-example-flask-restful

# Run both response examples sequentially
just run-response-examples
```

Alternatively, you can run each example directly:

```bash
# Run the basic Flask MethodView example
python -m examples.flask.app

# Run the basic Flask-RESTful example
python -m examples.flask_restful.app

# Run the Flask MethodView response example
python -m examples.flask.response_example

# Run the Flask-RESTful response example
python -m examples.flask_restful.response_example
```

## API Endpoints

All examples implement the same API endpoints:

- `GET /products` or `GET /api/products`: Get all products with optional filtering
- `POST /products` or `POST /api/products`: Create a new product
- `GET /products/<product_id>` or `GET /api/products/<product_id>`: Get a product by ID
- `PUT /products/<product_id>` or `PUT /api/products/<product_id>`: Update a product (basic examples only)
- `DELETE /products/<product_id>` or `DELETE /api/products/<product_id>`: Delete a product
- `POST /products/<product_id>/images` or `POST /api/products/<product_id>/images`: Upload product images
- `POST /products/<product_id>/documents` or `POST /api/products/<product_id>/documents`: Upload product documents
- `POST /products/<product_id>/audio` or `POST /api/products/<product_id>/audio`: Upload product audio files
- `POST /products/<product_id>/video` or `POST /api/products/<product_id>/video`: Upload product video files

## OpenAPI Documentation

When running any example, you can access the OpenAPI documentation:

- Swagger UI: http://localhost:5000/
- Raw OpenAPI YAML: http://localhost:5000/openapi.yaml

## Example Structure

```
examples/
├── common/                  # Shared code between examples
│   ├── models.py            # Pydantic models
│   └── utils.py             # Utility functions for rich output
├── flask/                   # Flask MethodView examples
│   ├── app.py               # Basic Flask application
│   └── response_example.py  # Flask application with structured responses
├── flask_restful/           # Flask-RESTful examples
│   ├── app.py               # Basic Flask-RESTful application
│   └── response_example.py  # Flask-RESTful application with structured responses
├── run_examples.py          # Script to run basic examples
└── run_response_examples.py # Script to run response examples
```

## Key Features Demonstrated

1. **Parameter Binding**:
   - Path parameters: `product_id`
   - Query parameters: Filtering and pagination
   - Request body: Creating and updating products

2. **OpenAPI Metadata**:
   - Adding summary, description, tags, etc.
   - Defining responses
   - Generating OpenAPI schema

3. **Pydantic Models**:
   - Request validation
   - Response serialization
   - Schema generation

4. **File Uploads**:
   - Image uploads with validation
   - Document uploads (PDF, DOC, etc.)
   - Audio file uploads (MP3, WAV, etc.)
   - Video file uploads (MP4, AVI, etc.)
   - File size and type validation

5. **Internationalization**:
   - Multilingual API documentation
   - Language switching
   - Localized error messages

6. **Rich Console Output**:
   - Visualizing requests and responses
   - Formatted tables and JSON

7. **Structured Responses**:
   - Using OpenAPIMetaResponse for defining response schemas
   - Defining success and error responses
   - Associating response models with status codes

## Testing the API

You can use tools like `curl`, Postman, or the built-in Swagger UI to test the API endpoints.

Example curl commands:

```bash
# Get all products
curl http://localhost:5000/products

# Create a new product
curl -X POST http://localhost:5000/products \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Product",
    "description": "A test product",
    "price": 29.99,
    "category": "electronics",
    "tags": ["test", "example"],
    "in_stock": true,
    "quantity": 10,
    "attributes": {
      "color": "black"
    }
  }'

# Get a product by ID (replace <product_id> with an actual ID)
curl http://localhost:5000/products/<product_id>

# Delete a product (replace <product_id> with an actual ID)
curl -X DELETE http://localhost:5000/products/<product_id>

# Upload a product image (replace <product_id> with an actual ID)
curl -X POST http://localhost:5000/products/<product_id>/images \
  -F "image=@/path/to/image.jpg"

# Upload a product document (replace <product_id> with an actual ID)
curl -X POST http://localhost:5000/products/<product_id>/documents \
  -F "document=@/path/to/document.pdf"

# Upload a product audio file (replace <product_id> with an actual ID)
curl -X POST http://localhost:5000/products/<product_id>/audio \
  -F "audio=@/path/to/audio.mp3"

# Upload a product video file (replace <product_id> with an actual ID)
curl -X POST http://localhost:5000/products/<product_id>/video \
  -F "video=@/path/to/video.mp4"
```

## Documentation

For more detailed information about the library and its features, please refer to the [online documentation](https://straydragon.github.io/flask-x-openapi-schema/) or the [Examples Guide](https://straydragon.github.io/flask-x-openapi-schema/examples/).
