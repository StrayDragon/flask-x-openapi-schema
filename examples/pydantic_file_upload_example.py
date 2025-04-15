"""
Example of how to use Pydantic models for file uploads with the OpenAPI decorator.

This example demonstrates how to:
1. Define Pydantic models for file uploads with validation
2. Use the models with the x_request_file parameter
3. Generate OpenAPI documentation for file upload endpoints
4. Process uploaded files with validation in Flask-RESTful resources
"""

from flask import Flask
from flask_restful import Api, Resource  # type: ignore
from werkzeug.utils import secure_filename

from flask_x_openapi_schema import (
    DocumentUploadModel,
    FileUploadModel,
    I18nStr,
    ImageUploadModel,
    OpenAPIIntegrationMixin,
    openapi_metadata,
    responses_schema,
)


# Create a Flask app and API
app = Flask(__name__)
api = Api(app)


# Add OpenAPI integration to the API
class OpenAPIApi(OpenAPIIntegrationMixin, Api):
    pass


# Replace the API with the OpenAPI-enabled version
api = OpenAPIApi(app)


# Define a custom file upload model with validation
class CustomImageUploadModel(ImageUploadModel):
    """Custom image upload model with specific validation rules."""

    allowed_extensions = ["jpg", "jpeg", "png"]  # Only allow these extensions
    max_size = 5 * 1024 * 1024  # 5MB maximum size


# Define a resource for file uploads using Pydantic models
class FileUploadResource(Resource):
    @openapi_metadata(
        summary=I18nStr(
            {
                "en-US": "Upload a file",
                "zh-Hans": "上传文件",
                "ja-JP": "ファイルをアップロードする",
            }
        ),
        description=I18nStr(
            {
                "en-US": "Upload a file to the server with validation",
                "zh-Hans": "将文件上传到服务器并进行验证",
                "ja-JP": "検証付きでサーバーにファイルをアップロードする",
            }
        ),
        tags=["Files"],
        operation_id="uploadFile",
        responses=responses_schema(
            success_responses={
                "200": {
                    "description": I18nStr(
                        {
                            "en-US": "File uploaded successfully",
                            "zh-Hans": "文件上传成功",
                            "ja-JP": "ファイルが正常にアップロードされました",
                        }
                    ),
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "filename": {"type": "string"},
                                    "size": {"type": "integer"},
                                    "content_type": {"type": "string"},
                                },
                            }
                        }
                    },
                },
            },
            errors={
                "400": I18nStr(
                    {
                        "en-US": "Invalid file or validation failed",
                        "zh-Hans": "无效的文件或验证失败",
                        "ja-JP": "無効なファイルまたは検証に失敗しました",
                    }
                ),
            },
        ),
    )
    def post(self, x_request_file: FileUploadModel):
        """
        Upload a file to the server with basic validation.

        This endpoint accepts a file upload and returns information about the uploaded file.
        The file is automatically injected into the method via the x_request_file parameter
        as a FileUploadModel instance.
        """
        # The file is already validated by the Pydantic model
        file = x_request_file.file

        # Process the uploaded file
        filename = secure_filename(file.filename)
        content_type = file.content_type

        # Read the file to get its size
        file.seek(0, 2)  # Seek to the end of the file
        file_size = file.tell()  # Get the position (size)
        file.seek(0)  # Rewind to the beginning

        # Return information about the uploaded file
        return {
            "filename": filename,
            "size": file_size,
            "content_type": content_type,
        }


# Define a resource for image uploads with validation
class ImageUploadResource(Resource):
    @openapi_metadata(
        summary=I18nStr(
            {
                "en-US": "Upload an image",
                "zh-Hans": "上传图片",
                "ja-JP": "画像をアップロードする",
            }
        ),
        description=I18nStr(
            {
                "en-US": "Upload an image with validation for file type and size",
                "zh-Hans": "上传图片并验证文件类型和大小",
                "ja-JP": "ファイルタイプとサイズの検証付きで画像をアップロードする",
            }
        ),
        tags=["Images"],
        operation_id="uploadImage",
        responses=responses_schema(
            success_responses={
                "200": {
                    "description": I18nStr(
                        {
                            "en-US": "Image uploaded successfully",
                            "zh-Hans": "图片上传成功",
                            "ja-JP": "画像が正常にアップロードされました",
                        }
                    ),
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "filename": {"type": "string"},
                                    "size": {"type": "integer"},
                                    "content_type": {"type": "string"},
                                    "dimensions": {
                                        "type": "object",
                                        "properties": {
                                            "width": {"type": "integer"},
                                            "height": {"type": "integer"},
                                        },
                                    },
                                },
                            }
                        }
                    },
                },
            },
            errors={
                "400": I18nStr(
                    {
                        "en-US": "Invalid image or validation failed",
                        "zh-Hans": "无效的图片或验证失败",
                        "ja-JP": "無効な画像または検証に失敗しました",
                    }
                ),
            },
        ),
    )
    def post(self, x_request_file: CustomImageUploadModel):
        """
        Upload an image with validation.

        This endpoint accepts an image upload and returns information about the uploaded image.
        The image is automatically injected into the method via the x_request_file parameter
        as a CustomImageUploadModel instance, which validates the file type and size.
        """
        try:
            # The file is already validated by the Pydantic model
            file = x_request_file.file

            # Process the uploaded file
            filename = secure_filename(file.filename)
            content_type = file.content_type

            # Read the file to get its size
            file.seek(0, 2)  # Seek to the end of the file
            file_size = file.tell()  # Get the position (size)
            file.seek(0)  # Rewind to the beginning

            # For images, we could get dimensions (mock implementation)
            dimensions = {
                "width": 800,
                "height": 600,
            }  # In a real app, use PIL or similar

            # Return information about the uploaded image
            return {
                "filename": filename,
                "size": file_size,
                "content_type": content_type,
                "dimensions": dimensions,
            }
        except ValueError as e:
            # Handle validation errors
            return {"error": str(e)}, 400


# Define a resource for document uploads
class DocumentUploadResource(Resource):
    @openapi_metadata(
        summary=I18nStr(
            {
                "en-US": "Upload a document",
                "zh-Hans": "上传文档",
                "ja-JP": "文書をアップロードする",
            }
        ),
        description=I18nStr(
            {
                "en-US": "Upload a document with validation for file type and size",
                "zh-Hans": "上传文档并验证文件类型和大小",
                "ja-JP": "ファイルタイプとサイズの検証付きで文書をアップロードする",
            }
        ),
        tags=["Documents"],
        operation_id="uploadDocument",
        responses=responses_schema(
            success_responses={
                "200": {
                    "description": I18nStr(
                        {
                            "en-US": "Document uploaded successfully",
                            "zh-Hans": "文档上传成功",
                            "ja-JP": "文書が正常にアップロードされました",
                        }
                    ),
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "filename": {"type": "string"},
                                    "size": {"type": "integer"},
                                    "content_type": {"type": "string"},
                                },
                            }
                        }
                    },
                },
            },
            errors={
                "400": I18nStr(
                    {
                        "en-US": "Invalid document or validation failed",
                        "zh-Hans": "无效的文档或验证失败",
                        "ja-JP": "無効な文書または検証に失敗しました",
                    }
                ),
            },
        ),
    )
    def post(self, x_request_file: DocumentUploadModel):
        """
        Upload a document with validation.

        This endpoint accepts a document upload and returns information about the uploaded document.
        The document is automatically injected into the method via the x_request_file parameter
        as a DocumentUploadModel instance, which validates the file type and size.
        """
        try:
            # The file is already validated by the Pydantic model
            file = x_request_file.file

            # Process the uploaded file
            filename = secure_filename(file.filename)
            content_type = file.content_type

            # Read the file to get its size
            file.seek(0, 2)  # Seek to the end of the file
            file_size = file.tell()  # Get the position (size)
            file.seek(0)  # Rewind to the beginning

            # Return information about the uploaded document
            return {
                "filename": filename,
                "size": file_size,
                "content_type": content_type,
            }
        except ValueError as e:
            # Handle validation errors
            return {"error": str(e)}, 400


# Register the resources with the API
api.add_resource(FileUploadResource, "/upload")
api.add_resource(ImageUploadResource, "/upload/image")
api.add_resource(DocumentUploadResource, "/upload/document")


if __name__ == "__main__":
    # Generate OpenAPI schema
    schema = api.generate_openapi_schema(
        title="File Upload API with Pydantic Models",
        version="1.0.0",
        description="API for uploading files with validation using Pydantic models",
        output_format="yaml",
    )

    # Save the schema to a file
    with open("openapi_pydantic.yaml", "w") as f:
        f.write(schema)

    # Run the app
    app.run(debug=True)
