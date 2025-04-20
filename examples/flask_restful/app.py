"""
Flask-RESTful example for Flask-X-OpenAPI-Schema.

This example demonstrates how to use Flask-X-OpenAPI-Schema with Flask-RESTful.
"""

import uuid
from datetime import datetime

from flask import Flask
from flask_restful import Resource, Api
import yaml

from flask_x_openapi_schema.x.flask_restful import (
    openapi_metadata,
    OpenAPIIntegrationMixin,
)
from flask_x_openapi_schema import (
    set_current_language,
    OpenAPIMetaResponse,
    OpenAPIMetaResponseItem,
)

from examples.common.models import (
    ProductRequest,
    ProductResponse,
    ProductQueryParams,
    ProductCategory,
    ProductStatus,
    ErrorResponse,
)
from examples.common.utils import (
    print_request_info,
    print_response_info,
    print_section_header,
)


# Create a Flask app
app = Flask(__name__)


# Create an OpenAPI-enabled API
class OpenAPIApi(OpenAPIIntegrationMixin, Api):
    pass


api = OpenAPIApi(app)

# In-memory database for products
products_db = {}


class ProductListResource(Resource):
    """Resource for managing product collections."""

    @openapi_metadata(
        summary="Get all products",
        description="Retrieve a list of products with optional filtering",
        tags=["products"],
        operation_id="getProducts",
        responses=OpenAPIMetaResponse(
            responses={
                "200": OpenAPIMetaResponseItem(
                    model=ProductResponse,
                    description="List of products retrieved successfully",
                ),
                "500": OpenAPIMetaResponseItem(
                    model=ErrorResponse,
                    description="Internal server error",
                ),
            }
        ),
    )
    def get(self, _x_query: ProductQueryParams = None):
        """Get all products with optional filtering."""
        # Print request information
        print_request_info(
            method="GET",
            path="/products",
            query_params=_x_query.model_dump() if _x_query else {},
        )

        # Apply filters if provided
        filtered_products = list(products_db.values())

        if _x_query:
            if _x_query.category:
                filtered_products = [
                    p for p in filtered_products if p["category"] == _x_query.category
                ]

            if _x_query.min_price is not None:
                filtered_products = [
                    p for p in filtered_products if p["price"] >= _x_query.min_price
                ]

            if _x_query.max_price is not None:
                filtered_products = [
                    p for p in filtered_products if p["price"] <= _x_query.max_price
                ]

            if _x_query.in_stock is not None:
                filtered_products = [
                    p for p in filtered_products if p["in_stock"] == _x_query.in_stock
                ]

            # Apply sorting
            if (
                _x_query.sort_by and _x_query.sort_by in filtered_products[0]
                if filtered_products
                else False
            ):
                reverse = _x_query.sort_order.lower() == "desc"
                filtered_products.sort(
                    key=lambda x: x[_x_query.sort_by], reverse=reverse
                )

            # Apply pagination
            start = _x_query.offset
            end = start + _x_query.limit
            filtered_products = filtered_products[start:end]

        # Print response information
        print_response_info(
            status_code=200,
            data=filtered_products,
        )

        return filtered_products, 200

    @openapi_metadata(
        summary="Create a new product",
        description="Create a new product with the provided information",
        tags=["products"],
        operation_id="createProduct",
        responses=OpenAPIMetaResponse(
            responses={
                "201": OpenAPIMetaResponseItem(
                    model=ProductResponse,
                    description="Product created successfully",
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
    def post(self, _x_body: ProductRequest):
        """Create a new product."""
        # Print request information
        print_request_info(
            method="POST",
            path="/products",
            body=_x_body.model_dump(),
        )

        # Create a new product
        product_id = str(uuid.uuid4())
        now = datetime.now()

        # Determine product status based on quantity and in_stock flag
        if not _x_body.in_stock or _x_body.quantity == 0:
            status = ProductStatus.OUT_OF_STOCK
        else:
            status = ProductStatus.AVAILABLE

        # Create the product
        product = {
            "id": product_id,
            "name": _x_body.name,
            "description": _x_body.description,
            "price": _x_body.price,
            "category": _x_body.category,
            "status": status,
            "tags": _x_body.tags,
            "in_stock": _x_body.in_stock,
            "quantity": _x_body.quantity,
            "attributes": _x_body.attributes,
            "created_at": now,
            "updated_at": None,
        }

        # Save to in-memory database
        products_db[product_id] = product

        # Create response
        response = ProductResponse(**product)

        # Print response information
        print_response_info(
            status_code=201,
            data=response.model_dump(),
        )

        return response.to_response(201)


class ProductResource(Resource):
    """Resource for managing individual products."""

    @openapi_metadata(
        summary="Get a product by ID",
        description="Retrieve a product by its unique identifier",
        tags=["products"],
        operation_id="getProduct",
        responses=OpenAPIMetaResponse(
            responses={
                "200": OpenAPIMetaResponseItem(
                    model=ProductResponse,
                    description="Product retrieved successfully",
                ),
                "404": OpenAPIMetaResponseItem(
                    model=ErrorResponse,
                    description="Product not found",
                ),
                "500": OpenAPIMetaResponseItem(
                    model=ErrorResponse,
                    description="Internal server error",
                ),
            }
        ),
    )
    def get(self, product_id: str):
        """Get a product by ID."""
        # Print request information
        print_request_info(
            method="GET",
            path=f"/products/{product_id}",
            path_params={"product_id": product_id},
        )

        # Check if product exists
        if product_id not in products_db:
            error = ErrorResponse(
                error_code="PRODUCT_NOT_FOUND",
                message=f"Product with ID {product_id} not found",
            )

            # Print response information
            print_response_info(
                status_code=404,
                data=error.model_dump(),
            )

            return error.to_response(404)

        # Get the product
        product = products_db[product_id]
        response = ProductResponse(**product)

        # Print response information
        print_response_info(
            status_code=200,
            data=response.model_dump(),
        )

        return response.to_response(200)

    @openapi_metadata(
        summary="Update a product",
        description="Update an existing product with new information",
        tags=["products"],
        operation_id="updateProduct",
        responses=OpenAPIMetaResponse(
            responses={
                "200": OpenAPIMetaResponseItem(
                    model=ProductResponse,
                    description="Product updated successfully",
                ),
                "404": OpenAPIMetaResponseItem(
                    model=ErrorResponse,
                    description="Product not found",
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
    def put(self, product_id: str, _x_body: ProductRequest):
        """Update a product."""
        # Print request information
        print_request_info(
            method="PUT",
            path=f"/products/{product_id}",
            path_params={"product_id": product_id},
            body=_x_body.model_dump(),
        )

        # Check if product exists
        if product_id not in products_db:
            error = ErrorResponse(
                error_code="PRODUCT_NOT_FOUND",
                message=f"Product with ID {product_id} not found",
            )

            # Print response information
            print_response_info(
                status_code=404,
                data=error.model_dump(),
            )

            return error.to_response(404)

        # Get the existing product
        product = products_db[product_id]

        # Determine product status based on quantity and in_stock flag
        if not _x_body.in_stock or _x_body.quantity == 0:
            status = ProductStatus.OUT_OF_STOCK
        else:
            status = ProductStatus.AVAILABLE

        # Update the product
        product.update(
            {
                "name": _x_body.name,
                "description": _x_body.description,
                "price": _x_body.price,
                "category": _x_body.category,
                "status": status,
                "tags": _x_body.tags,
                "in_stock": _x_body.in_stock,
                "quantity": _x_body.quantity,
                "attributes": _x_body.attributes,
                "updated_at": datetime.now(),
            }
        )

        # Save to in-memory database
        products_db[product_id] = product

        # Create response
        response = ProductResponse(**product)

        # Print response information
        print_response_info(
            status_code=200,
            data=response.model_dump(),
        )

        return response.to_response(200)

    @openapi_metadata(
        summary="Delete a product",
        description="Delete a product by its unique identifier",
        tags=["products"],
        operation_id="deleteProduct",
        responses=OpenAPIMetaResponse(
            responses={
                "204": OpenAPIMetaResponseItem(
                    description="Product deleted successfully",
                    msg="Product deleted successfully",
                ),
                "404": OpenAPIMetaResponseItem(
                    model=ErrorResponse,
                    description="Product not found",
                ),
                "500": OpenAPIMetaResponseItem(
                    model=ErrorResponse,
                    description="Internal server error",
                ),
            }
        ),
    )
    def delete(self, product_id: str):
        """Delete a product."""
        # Print request information
        print_request_info(
            method="DELETE",
            path=f"/products/{product_id}",
            path_params={"product_id": product_id},
        )

        # Check if product exists
        if product_id not in products_db:
            error = ErrorResponse(
                error_code="PRODUCT_NOT_FOUND",
                message=f"Product with ID {product_id} not found",
            )

            # Print response information
            print_response_info(
                status_code=404,
                data=error.model_dump(),
            )

            return error.to_response(404)

        # Delete the product
        del products_db[product_id]

        # Print response information
        print_response_info(
            status_code=204,
            data={},
        )

        return "", 204


# Register the resources
api.add_resource(ProductListResource, "/products")
api.add_resource(ProductResource, "/products/<string:product_id>")

# Debug: Print registered resources
print("\nRegistered Resources:")
for resource, urls, _ in api.resources:
    print(f"Resource: {resource.__name__}, URLs: {urls}")


@app.route("/openapi.yaml")
def get_openapi_spec():
    """Generate and return the OpenAPI specification."""
    # Generate the schema with output_format="json" to get a dictionary
    schema = api.generate_openapi_schema(
        title="Product API",
        version="1.0.0",
        description="API for managing products",
        output_format="json"
    )

    # Debug: Print the schema to console
    print("\nOpenAPI Schema:")
    print(f"openapi version: {schema.get('openapi', 'NOT FOUND')}")
    print(f"info: {schema.get('info', {})}")
    print(f"paths: {len(schema.get('paths', {}))} endpoints")
    for path in schema.get('paths', {}):
        print(f"  - {path}")
    print(f"components: {len(schema.get('components', {}).get('schemas', {}))} schemas")
    for schema_name in schema.get('components', {}).get('schemas', {}):
        print(f"  - {schema_name}")

    # Convert to YAML with proper settings
    yaml_content = yaml.dump(schema, sort_keys=False, default_flow_style=False, allow_unicode=True)

    return yaml_content, 200, {"Content-Type": "text/yaml"}


@app.route("/")
def index():
    """Render the API documentation."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Product API Documentation</title>
        <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css">
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js"></script>
        <script>
            window.onload = function() {
                SwaggerUIBundle({
                    url: "/openapi.yaml",
                    dom_id: "#swagger-ui",
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIBundle.SwaggerUIStandalonePreset
                    ],
                    layout: "BaseLayout",
                    validatorUrl: null,
                    displayRequestDuration: true,
                    syntaxHighlight: {
                        activated: true,
                        theme: "agate"
                    }
                });
            }
        </script>
    </body>
    </html>
    """


def add_sample_products():
    """Add sample products to the in-memory database."""
    sample_products = [
        {
            "name": "Wireless Headphones",
            "description": "Premium noise-cancelling wireless headphones",
            "price": 249.99,
            "category": ProductCategory.ELECTRONICS,
            "tags": ["headphones", "audio", "wireless"],
            "in_stock": True,
            "quantity": 25,
            "attributes": {
                "color": "silver",
                "battery_life": "30 hours",
                "connectivity": "Bluetooth 5.0",
            },
        },
        {
            "name": "Designer Jeans",
            "description": "Premium denim jeans with modern fit",
            "price": 89.99,
            "category": ProductCategory.CLOTHING,
            "tags": ["jeans", "denim", "fashion"],
            "in_stock": True,
            "quantity": 75,
            "attributes": {
                "color": "blue",
                "size": "32x34",
                "material": "100% cotton denim",
            },
        },
        {
            "name": "Gourmet Coffee Beans",
            "description": "Specialty coffee beans from Ethiopia",
            "price": 14.99,
            "category": ProductCategory.FOOD,
            "tags": ["coffee", "organic", "fair-trade"],
            "in_stock": True,
            "quantity": 100,
            "attributes": {"weight": "12 oz", "roast": "medium", "origin": "Ethiopia"},
        },
    ]

    for product_data in sample_products:
        # Create a request model
        request = ProductRequest(**product_data)

        # Create a product
        product_id = str(uuid.uuid4())
        now = datetime.now()

        # Determine product status
        if not request.in_stock or request.quantity == 0:
            status = ProductStatus.OUT_OF_STOCK
        else:
            status = ProductStatus.AVAILABLE

        # Create the product
        product = {
            "id": product_id,
            "name": request.name,
            "description": request.description,
            "price": request.price,
            "category": request.category,
            "status": status,
            "tags": request.tags,
            "in_stock": request.in_stock,
            "quantity": request.quantity,
            "attributes": request.attributes,
            "created_at": now,
            "updated_at": None,
        }

        # Save to in-memory database
        products_db[product_id] = product


if __name__ == "__main__":
    # Add sample products
    add_sample_products()

    # Set language for i18n
    set_current_language("en-US")

    # Print information about the example
    print_section_header("Flask-RESTful Example")
    print(
        "This example demonstrates how to use Flask-X-OpenAPI-Schema with Flask-RESTful."
    )
    print("The API provides endpoints for managing products.")
    print()
    print("Available endpoints:")
    print("- GET    /products")
    print("- POST   /products")
    print("- GET    /products/<product_id>")
    print("- PUT    /products/<product_id>")
    print("- DELETE /products/<product_id>")
    print()
    print("OpenAPI documentation is available at:")
    print("- /openapi.yaml (Raw YAML)")
    print("- / (Swagger UI)")
    print()
    print("Starting server on http://localhost:5001")

    # Run the app on a different port
    app.run(debug=True, port=5001)
