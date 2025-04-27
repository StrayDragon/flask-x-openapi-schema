"""Flask MethodView example for Flask-X-OpenAPI-Schema.

This example demonstrates how to use Flask-X-OpenAPI-Schema with Flask MethodView.
"""

import os
import uuid
from datetime import datetime
from pathlib import Path

import yaml
from flask import Blueprint, Flask, jsonify, send_file, url_for
from flask.views import MethodView

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
from flask_x_openapi_schema.core.config import OpenAPIConfig, configure_openapi
from flask_x_openapi_schema.x.flask import OpenAPIMethodViewMixin, openapi_metadata
from flask_x_openapi_schema.x.flask.views import MethodViewOpenAPISchemaGenerator

# Create a Flask app
app = Flask(__name__)

# Create a blueprint
blueprint = Blueprint("api", __name__, url_prefix="/api")

# Create uploads directory if it doesn't exist
uploads_dir = Path(os.path.dirname(os.path.abspath(__file__))) / "uploads"
uploads_dir.mkdir(exist_ok=True)

# In-memory database for products and files
products_db = {}
files_db = {}


class ProductView(OpenAPIMethodViewMixin, MethodView):
    """Product API endpoints using Flask MethodView."""

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
            path="/api/products",
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

        # Convert datetime objects to ISO format strings
        for product in filtered_products:
            if "created_at" in product and isinstance(product["created_at"], datetime):
                product["created_at"] = product["created_at"].isoformat()
            if "updated_at" in product and isinstance(product["updated_at"], datetime):
                product["updated_at"] = product["updated_at"].isoformat()

        # Print response information
        print_response_info(
            status_code=200,
            data=filtered_products,
        )

        return jsonify(filtered_products), 200

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
            path="/api/products",
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


class ProductDetailView(OpenAPIMethodViewMixin, MethodView):
    """Product detail API endpoints using Flask MethodView."""

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
            path=f"/api/products/{product_id}",
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
            path=f"/api/products/{product_id}",
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
            path=f"/api/products/{product_id}",
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


class ProductImageView(OpenAPIMethodViewMixin, MethodView):
    """Product image upload and download endpoints."""

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
    def post(self, product_id: str, _x_file_image: ProductImageUpload):
        """Upload a product image."""
        # The file is automatically injected into _x_file_image.file by the decorator
        file = _x_file_image.file

        # Print request information
        print_request_info(
            method="POST",
            path=f"/api/products/{product_id}/images",
            path_params={"product_id": product_id},
            file={
                "filename": file.filename if file and hasattr(file, "filename") else None,
                "description": _x_file_image.description,
                "is_primary": _x_file_image.is_primary,
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
            "description": _x_file_image.description,
            "is_primary": _x_file_image.is_primary,
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
            url=url_for("api.download_file", file_id=file_id, _external=True),
        )

        # Print response information
        print_response_info(
            status_code=201,
            data=response.model_dump(),
        )

        return response.to_response(201)


class ProductDocumentView(OpenAPIMethodViewMixin, MethodView):
    """Product document upload and download endpoints."""

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
    def post(self, product_id: str, _x_file_document: ProductDocumentUpload):
        """Upload a product document."""
        # The file is automatically injected into _x_file_document.file by the decorator
        file = _x_file_document.file

        # Print request information
        print_request_info(
            method="POST",
            path=f"/api/products/{product_id}/documents",
            path_params={"product_id": product_id},
            file={
                "filename": file.filename if file and hasattr(file, "filename") else None,
                "title": _x_file_document.title,
                "document_type": _x_file_document.document_type,
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
            "title": _x_file_document.title,
            "document_type": _x_file_document.document_type,
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
            url=url_for("api.download_file", file_id=file_id, _external=True),
        )

        # Print response information
        print_response_info(
            status_code=201,
            data=response.model_dump(),
        )

        return response.to_response(201)


# Add file download endpoint to the blueprint
@blueprint.route("/files/<file_id>", methods=["GET"])
def download_file(file_id):
    """Download a file by ID."""
    # Print request information
    print_request_info(
        method="GET",
        path=f"/api/files/{file_id}",
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

    # Return the file
    return send_file(
        file_path,
        mimetype=content_type,
        as_attachment=True,
        download_name=filename,
    )


class ProductAudioView(OpenAPIMethodViewMixin, MethodView):
    """Product audio upload and download endpoints."""

    @openapi_metadata(
        summary="Upload a product audio",
        description="Upload an audio file for a specific product",
        tags=["files"],
        operation_id="uploadProductAudio",
        responses=OpenAPIMetaResponse(
            responses={
                "201": OpenAPIMetaResponseItem(
                    model=FileResponse,
                    description="Audio uploaded successfully",
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
    def post(self, product_id: str, _x_file_audio: ProductAudioUpload):
        """Upload a product audio file."""
        # The file is automatically injected into _x_file_audio.file by the decorator
        file = _x_file_audio.file

        # Print request information
        print_request_info(
            method="POST",
            path=f"/api/products/{product_id}/audio",
            path_params={"product_id": product_id},
            file={
                "filename": file.filename if file and hasattr(file, "filename") else None,
                "title": _x_file_audio.title,
                "duration_seconds": _x_file_audio.duration_seconds,
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
            "title": _x_file_audio.title,
            "duration_seconds": _x_file_audio.duration_seconds,
            "type": "audio",
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
            url=url_for("api.download_file", file_id=file_id, _external=True),
        )

        # Print response information
        print_response_info(
            status_code=201,
            data=response.model_dump(),
        )

        return response.to_response(201)


class ProductVideoView(OpenAPIMethodViewMixin, MethodView):
    """Product video upload and download endpoints."""

    @openapi_metadata(
        summary="Upload a product video",
        description="Upload a video file for a specific product",
        tags=["files"],
        operation_id="uploadProductVideo",
        responses=OpenAPIMetaResponse(
            responses={
                "201": OpenAPIMetaResponseItem(
                    model=FileResponse,
                    description="Video uploaded successfully",
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
    def post(self, product_id: str, _x_file_video: ProductVideoUpload):
        """Upload a product video file."""
        # The file is automatically injected into _x_file_video.file by the decorator
        file = _x_file_video.file

        # Print request information
        print_request_info(
            method="POST",
            path=f"/api/products/{product_id}/video",
            path_params={"product_id": product_id},
            file={
                "filename": file.filename if file and hasattr(file, "filename") else None,
                "title": _x_file_video.title,
                "duration_seconds": _x_file_video.duration_seconds,
                "resolution": _x_file_video.resolution,
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
            "title": _x_file_video.title,
            "duration_seconds": _x_file_video.duration_seconds,
            "resolution": _x_file_video.resolution,
            "type": "video",
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
            url=url_for("api.download_file", file_id=file_id, _external=True),
        )

        # Print response information
        print_response_info(
            status_code=201,
            data=response.model_dump(),
        )

        return response.to_response(201)


# Register the views using OpenAPIMethodViewMixin's register_to_blueprint method
ProductView.register_to_blueprint(blueprint, "/products", "products")
ProductDetailView.register_to_blueprint(blueprint, "/products/<product_id>", "product_detail")
ProductImageView.register_to_blueprint(blueprint, "/products/<product_id>/images", "product_images")
ProductDocumentView.register_to_blueprint(blueprint, "/products/<product_id>/documents", "product_documents")
ProductAudioView.register_to_blueprint(blueprint, "/products/<product_id>/audio", "product_audio")
ProductVideoView.register_to_blueprint(blueprint, "/products/<product_id>/video", "product_video")

# Register the blueprint
app.register_blueprint(blueprint)


@app.route("/openapi.yaml")
def get_openapi_spec():
    """Generate and return the OpenAPI specification."""
    # Create a schema generator for MethodView classes

    # Configure OpenAPI with 3.1.0 version and additional features
    configure_openapi(
        OpenAPIConfig(
            title="Product API",
            version="1.0.0",
            description="API for managing products",
            openapi_version="3.1.0",
            servers=[
                {"url": "http://localhost:5002", "description": "Development server"},
                {"url": "https://api.example.com", "description": "Production server"},
            ],
            external_docs={"description": "Find more info here", "url": "https://example.com/docs"},
        )
    )

    generator = MethodViewOpenAPISchemaGenerator(
        title="Product API",
        version="1.0.0",
        description="API for managing products",
    )

    # Add a webhook example (OpenAPI 3.1 feature)
    generator.add_webhook(
        "newProduct",
        {
            "post": {
                "summary": "New product webhook",
                "description": "Triggered when a new product is created",
                "requestBody": {
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ProductResponse"}}}
                },
                "responses": {"200": {"description": "Webhook received successfully"}},
            }
        },
    )

    # Manually register response models and enums
    generator._register_model(ProductResponse)
    generator._register_model(ErrorResponse)
    generator._register_model(ProductCategory)
    generator._register_model(ProductStatus)
    generator._register_model(ProductImageUpload)
    generator._register_model(ProductDocumentUpload)
    generator._register_model(ProductAudioUpload)
    generator._register_model(ProductVideoUpload)
    generator._register_model(FileResponse)

    # Process MethodView resources
    generator.process_methodview_resources(blueprint)

    # Generate the schema
    schema = generator.generate_schema()

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
    if "webhooks" in schema:
        print(f"webhooks: {len(schema.get('webhooks', {}))} webhooks")
        for webhook_name in schema.get("webhooks", {}):
            print(f"  - {webhook_name}")

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
                    supportedSubmitMethods: ['get', 'put', 'post', 'delete', 'options', 'head', 'patch', 'trace'],
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
            "name": "Smartphone X",
            "description": "Latest smartphone with advanced features",
            "price": 999.99,
            "category": ProductCategory.ELECTRONICS,
            "tags": ["smartphone", "tech", "mobile"],
            "in_stock": True,
            "quantity": 50,
            "attributes": {
                "color": "black",
                "storage": "128GB",
                "screen_size": "6.5 inches",
            },
        },
        {
            "name": "Classic T-Shirt",
            "description": "Comfortable cotton t-shirt",
            "price": 19.99,
            "category": ProductCategory.CLOTHING,
            "tags": ["t-shirt", "casual", "cotton"],
            "in_stock": True,
            "quantity": 100,
            "attributes": {"color": "white", "size": "M", "material": "100% cotton"},
        },
        {
            "name": "Python Programming Guide",
            "description": "Comprehensive guide to Python programming",
            "price": 39.99,
            "category": ProductCategory.BOOKS,
            "tags": ["programming", "python", "education"],
            "in_stock": True,
            "quantity": 30,
            "attributes": {"pages": 450, "format": "hardcover", "language": "English"},
        },
    ]

    for product_data in sample_products:
        # Create a request model
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
    print_section_header("Flask MethodView Example")
    print("This example demonstrates how to use Flask-X-OpenAPI-Schema with Flask MethodView.")
    print("The API provides endpoints for managing products.")
    print()
    print("Available endpoints:")
    print("- GET    /api/products")
    print("- POST   /api/products")
    print("- GET    /api/products/<product_id>")
    print("- PUT    /api/products/<product_id>")
    print("- DELETE /api/products/<product_id>")
    print()
    print("OpenAPI documentation is available at:")
    print("- /openapi.yaml (Raw YAML)")
    print("- / (Swagger UI)")
    print()
    print("Starting server on http://localhost:5002")

    # Run the app on a different port
    app.run(debug=True, port=5002)  # noqa: S201
