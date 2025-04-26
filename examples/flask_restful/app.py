"""Flask-RESTful example for Flask-X-OpenAPI-Schema.

This example demonstrates how to use Flask-X-OpenAPI-Schema with Flask-RESTful.
"""

import os
import uuid
from datetime import datetime
from pathlib import Path

import yaml
from flask import Flask, send_file
from flask_restful import Api, Resource

from examples.common.models import (
    ErrorResponse,
    FileResponse,
    ProductAudioUpload,
    ProductCategory,
    ProductDocumentUpload,
    ProductImageUpload,
    ProductQueryParams,
    ProductRequest,
    ProductResponse,
    ProductStatus,
    ProductVideoUpload,
)
from examples.common.utils import (
    print_request_info,
    print_response_info,
    print_section_header,
)
from flask_x_openapi_schema import (
    OpenAPIMetaResponse,
    OpenAPIMetaResponseItem,
    set_current_language,
)
from flask_x_openapi_schema.x.flask_restful import (
    OpenAPIIntegrationMixin,
    openapi_metadata,
)

# Create a Flask app
app = Flask(__name__)

# Configure file uploads
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max upload size
app.config["UPLOAD_FOLDER"] = "uploads"

# Create uploads directory if it doesn't exist
uploads_dir = Path(app.config["UPLOAD_FOLDER"])
uploads_dir.mkdir(exist_ok=True)


# Create an OpenAPI-enabled API
class OpenAPIApi(OpenAPIIntegrationMixin, Api):
    pass


api = OpenAPIApi(app)

# In-memory databases
products_db = {}
files_db = {}


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
            },
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
                filtered_products = [p for p in filtered_products if p["category"] == _x_query.category]

            if _x_query.min_price is not None:
                filtered_products = [p for p in filtered_products if p["price"] >= _x_query.min_price]

            if _x_query.max_price is not None:
                filtered_products = [p for p in filtered_products if p["price"] <= _x_query.max_price]

            if _x_query.in_stock is not None:
                filtered_products = [p for p in filtered_products if p["in_stock"] == _x_query.in_stock]

            # Apply sorting
            if _x_query.sort_by and _x_query.sort_by in filtered_products[0] if filtered_products else False:
                reverse = _x_query.sort_order.lower() == "desc"
                filtered_products.sort(key=lambda x: x[_x_query.sort_by], reverse=reverse)

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
            },
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
            },
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
            },
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
            },
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
            },
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


class FileDownloadResource(Resource):
    """Resource for downloading files."""

    @openapi_metadata(
        summary="Download a file",
        description="Download a file by its ID",
        tags=["files"],
        operation_id="downloadFile",
        responses=OpenAPIMetaResponse(
            responses={
                "200": OpenAPIMetaResponseItem(
                    description="File downloaded successfully",
                ),
                "404": OpenAPIMetaResponseItem(
                    model=ErrorResponse,
                    description="File not found",
                ),
                "500": OpenAPIMetaResponseItem(
                    model=ErrorResponse,
                    description="Internal server error",
                ),
            },
        ),
    )
    def get(self, file_id: str):
        """Download a file by its ID."""
        # Print request information
        print_request_info(
            method="GET",
            path=f"/files/{file_id}",
            path_params={"file_id": file_id},
        )

        # Check if file exists
        if file_id not in files_db:
            error = ErrorResponse(
                error_code="FILE_NOT_FOUND",
                message=f"File with ID {file_id} not found",
            )

            # Print response information
            print_response_info(
                status_code=404,
                data=error.model_dump(),
            )

            return error.to_response(404)

        # Get file metadata
        file_data = files_db[file_id]
        file_path = file_data["path"]
        filename = file_data["filename"]
        content_type = file_data["content_type"]

        # Print response information
        print_response_info(
            status_code=200,
            data={"file": filename, "content_type": content_type},
        )

        # Send the file
        return send_file(
            file_path,
            mimetype=content_type,
            as_attachment=True,
            download_name=filename,
        )


class ProductImageResource(Resource):
    """Resource for uploading product images."""

    @openapi_metadata(
        summary="Upload a product image",
        description="Upload an image for a specific product",
        tags=["files"],
        operation_id="uploadProductImage",
        responses=OpenAPIMetaResponse(
            responses={
                "201": OpenAPIMetaResponseItem(
                    model=FileResponse,
                    description="Image uploaded successfully",
                ),
                "400": OpenAPIMetaResponseItem(
                    model=ErrorResponse,
                    description="Invalid request data",
                ),
                "404": OpenAPIMetaResponseItem(
                    model=ErrorResponse,
                    description="Product not found",
                ),
                "500": OpenAPIMetaResponseItem(
                    model=ErrorResponse,
                    description="Internal server error",
                ),
            },
        ),
    )
    def post(self, product_id: str, _x_file: ProductImageUpload):
        """Upload a product image file."""
        # The file is automatically injected into _x_file.file by the decorator
        file = _x_file.file

        # Print request information
        print_request_info(
            method="POST",
            path=f"/products/{product_id}/images",
            path_params={"product_id": product_id},
            file={
                "filename": file.filename if file and hasattr(file, "filename") else None,
                "description": _x_file.description,
                "is_primary": _x_file.is_primary,
            },
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

        # Save the file
        file_id = str(uuid.uuid4())
        filename = file.filename
        content_type = file.content_type or "application/octet-stream"

        # Create product-specific directory
        product_dir = uploads_dir / product_id
        product_dir.mkdir(exist_ok=True)

        # Save file to disk
        file_path = product_dir / f"{file_id}_{filename}"
        file.save(file_path)

        # Get file size
        size = os.path.getsize(file_path)

        # Create file metadata
        now = datetime.now()
        file_data = {
            "id": file_id,
            "product_id": product_id,
            "filename": filename,
            "content_type": content_type,
            "size": size,
            "path": str(file_path),
            "upload_date": now,
            "description": _x_file.description,
            "is_primary": _x_file.is_primary,
            "type": "image",
        }

        # Save to in-memory database
        files_db[file_id] = file_data

        # Create response
        response = FileResponse(
            id=file_id,
            filename=filename,
            content_type=content_type,
            size=size,
            upload_date=now,
            url=f"/files/{file_id}",
        )

        # Print response information
        print_response_info(
            status_code=201,
            data=response.model_dump(),
        )

        return response.to_response(201)


class ProductDocumentResource(Resource):
    """Resource for uploading product documents."""

    @openapi_metadata(
        summary="Upload a product document",
        description="Upload a document (manual, spec sheet, etc.) for a specific product",
        tags=["files"],
        operation_id="uploadProductDocument",
        responses=OpenAPIMetaResponse(
            responses={
                "201": OpenAPIMetaResponseItem(
                    model=FileResponse,
                    description="Document uploaded successfully",
                ),
                "400": OpenAPIMetaResponseItem(
                    model=ErrorResponse,
                    description="Invalid request data",
                ),
                "404": OpenAPIMetaResponseItem(
                    model=ErrorResponse,
                    description="Product not found",
                ),
                "500": OpenAPIMetaResponseItem(
                    model=ErrorResponse,
                    description="Internal server error",
                ),
            },
        ),
    )
    def post(self, product_id: str, _x_file: ProductDocumentUpload):
        """Upload a product document file."""
        # The file is automatically injected into _x_file.file by the decorator
        file = _x_file.file

        # Print request information
        print_request_info(
            method="POST",
            path=f"/products/{product_id}/documents",
            path_params={"product_id": product_id},
            file={
                "filename": file.filename if file and hasattr(file, "filename") else None,
                "title": _x_file.title,
                "document_type": _x_file.document_type,
            },
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

        # Save the file
        file_id = str(uuid.uuid4())
        filename = file.filename
        content_type = file.content_type or "application/octet-stream"

        # Create product-specific directory
        product_dir = uploads_dir / product_id
        product_dir.mkdir(exist_ok=True)

        # Save file to disk
        file_path = product_dir / f"{file_id}_{filename}"
        file.save(file_path)

        # Get file size
        size = os.path.getsize(file_path)

        # Create file metadata
        now = datetime.now()
        file_data = {
            "id": file_id,
            "product_id": product_id,
            "filename": filename,
            "content_type": content_type,
            "size": size,
            "path": str(file_path),
            "upload_date": now,
            "title": _x_file.title,
            "document_type": _x_file.document_type,
            "type": "document",
        }

        # Save to in-memory database
        files_db[file_id] = file_data

        # Create response
        response = FileResponse(
            id=file_id,
            filename=filename,
            content_type=content_type,
            size=size,
            upload_date=now,
            url=f"/files/{file_id}",
        )

        # Print response information
        print_response_info(
            status_code=201,
            data=response.model_dump(),
        )

        return response.to_response(201)


# Register the resources
api.add_resource(ProductListResource, "/products")
api.add_resource(ProductResource, "/products/<string:product_id>")
api.add_resource(ProductImageResource, "/products/<string:product_id>/images")
api.add_resource(ProductDocumentResource, "/products/<string:product_id>/documents")
api.add_resource(FileDownloadResource, "/files/<string:file_id>")

# Debug: Print registered resources
print("\nRegistered Resources:")
for resource, urls, _ in api.resources:
    print(f"Resource: {resource.__name__}, URLs: {urls}")


@app.route("/openapi.yaml")
def get_openapi_spec():
    """Generate and return the OpenAPI specification."""
    # Manually register models
    from flask_x_openapi_schema.core.utils import pydantic_to_openapi_schema

    # Generate the schema with output_format="json" to get a dictionary
    schema = api.generate_openapi_schema(
        title="Product API",
        version="1.0.0",
        description="API for managing products",
        output_format="json",
    )

    # Manually register file upload models
    if "components" not in schema:
        schema["components"] = {}
    if "schemas" not in schema["components"]:
        schema["components"]["schemas"] = {}

    # Register file models
    for model in [
        ProductImageUpload,
        ProductDocumentUpload,
        ProductAudioUpload,
        ProductVideoUpload,
        FileResponse,
    ]:
        model_schema = pydantic_to_openapi_schema(model)
        schema["components"]["schemas"][model.__name__] = model_schema

    # Debug: Print the schema to console
    print("\nOpenAPI Schema:")
    print(f"openapi version: {schema.get('openapi', 'NOT FOUND')}")
    print(f"info: {schema.get('info', {})}")
    print(f"paths: {len(schema.get('paths', {}))} endpoints")
    for path in schema.get("paths", {}):
        print(f"  - {path}")
    print(f"components: {len(schema.get('components', {}).get('schemas', {}))} schemas")
    for schema_name in schema.get("components", {}).get("schemas", {}):
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
        # Create a product request model
        product_request = ProductRequest(**product_data)

        # Create a product
        product_id = str(uuid.uuid4())
        now = datetime.now()

        # Determine product status
        if not product_request.in_stock or product_request.quantity == 0:
            status = ProductStatus.OUT_OF_STOCK
        else:
            status = ProductStatus.AVAILABLE

        # Create the product
        product = {
            "id": product_id,
            "name": product_request.name,
            "description": product_request.description,
            "price": product_request.price,
            "category": product_request.category,
            "status": status,
            "tags": product_request.tags,
            "in_stock": product_request.in_stock,
            "quantity": product_request.quantity,
            "attributes": product_request.attributes,
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
    print("This example demonstrates how to use Flask-X-OpenAPI-Schema with Flask-RESTful.")
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
    app.run(debug=True, port=5001)  # noqa: S201
