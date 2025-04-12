"""
Example of how to use the file upload functionality with the OpenAPI decorator.

This example demonstrates how to:
1. Use the x_request_file parameter to handle file uploads
2. Generate OpenAPI documentation for file upload endpoints
3. Process uploaded files in Flask-RESTful resources
"""

from flask import Flask, request
from flask_restful import Api, Resource  # type: ignore
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from flask_x_openapi_schema import (
    I18nString,
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


# Define a resource for file uploads
class FileUploadResource(Resource):
    @openapi_metadata(
        summary=I18nString({
            "en-US": "Upload a file",
            "zh-Hans": "上传文件",
            "ja-JP": "ファイルをアップロードする",
        }),
        description=I18nString({
            "en-US": "Upload a file to the server",
            "zh-Hans": "将文件上传到服务器",
            "ja-JP": "サーバーにファイルをアップロードする",
        }),
        tags=["Files"],
        operation_id="uploadFile",
        responses=responses_schema(
            success_responses={
                "200": {
                    "description": I18nString({
                        "en-US": "File uploaded successfully",
                        "zh-Hans": "文件上传成功",
                        "ja-JP": "ファイルが正常にアップロードされました",
                    }),
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
                "400": I18nString({
                    "en-US": "No file provided",
                    "zh-Hans": "未提供文件",
                    "ja-JP": "ファイルが提供されていません",
                }),
            },
        ),
    )
    def post(self, x_request_file: FileStorage):
        """
        Upload a file to the server.

        This endpoint accepts a file upload and returns information about the uploaded file.
        The file is automatically injected into the method via the x_request_file parameter.
        """
        if not x_request_file:
            return {"error": "No file provided"}, 400

        # Process the uploaded file
        filename = secure_filename(x_request_file.filename)
        content_type = x_request_file.content_type
        file_size = 0

        # Read the file to get its size
        x_request_file.seek(0, 2)  # Seek to the end of the file
        file_size = x_request_file.tell()  # Get the position (size)
        x_request_file.seek(0)  # Rewind to the beginning

        # Return information about the uploaded file
        return {
            "filename": filename,
            "size": file_size,
            "content_type": content_type,
        }


# Define a resource for multiple file uploads
class MultipleFileUploadResource(Resource):
    @openapi_metadata(
        summary=I18nString({
            "en-US": "Upload multiple files",
            "zh-Hans": "上传多个文件",
            "ja-JP": "複数のファイルをアップロードする",
        }),
        description=I18nString({
            "en-US": "Upload multiple files to the server",
            "zh-Hans": "将多个文件上传到服务器",
            "ja-JP": "サーバーに複数のファイルをアップロードする",
        }),
        tags=["Files"],
        operation_id="uploadMultipleFiles",
        responses=responses_schema(
            success_responses={
                "200": {
                    "description": I18nString({
                        "en-US": "Files uploaded successfully",
                        "zh-Hans": "文件上传成功",
                        "ja-JP": "ファイルが正常にアップロードされました",
                    }),
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "files": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "filename": {"type": "string"},
                                                "size": {"type": "integer"},
                                                "content_type": {"type": "string"},
                                            },
                                        },
                                    },
                                },
                            }
                        }
                    },
                },
            },
            errors={
                "400": I18nString({
                    "en-US": "No files provided",
                    "zh-Hans": "未提供文件",
                    "ja-JP": "ファイルが提供されていません",
                }),
            },
        ),
    )
    def post(self, x_request_file_document: FileStorage, x_request_file_image: FileStorage):
        """
        Upload multiple files to the server.

        This endpoint accepts multiple file uploads and returns information about the uploaded files.
        The files are automatically injected into the method via the x_request_file_* parameters.
        """
        files_info = []

        # Process the document file
        if x_request_file_document:
            filename = secure_filename(x_request_file_document.filename)
            content_type = x_request_file_document.content_type

            # Read the file to get its size
            x_request_file_document.seek(0, 2)
            file_size = x_request_file_document.tell()
            x_request_file_document.seek(0)

            files_info.append({
                "filename": filename,
                "size": file_size,
                "content_type": content_type,
                "type": "document",
            })

        # Process the image file
        if x_request_file_image:
            filename = secure_filename(x_request_file_image.filename)
            content_type = x_request_file_image.content_type

            # Read the file to get its size
            x_request_file_image.seek(0, 2)
            file_size = x_request_file_image.tell()
            x_request_file_image.seek(0)

            files_info.append({
                "filename": filename,
                "size": file_size,
                "content_type": content_type,
                "type": "image",
            })

        if not files_info:
            return {"error": "No files provided"}, 400

        # Return information about the uploaded files
        return {"files": files_info}


# Register the resources with the API
api.add_resource(FileUploadResource, "/upload")
api.add_resource(MultipleFileUploadResource, "/upload-multiple")


if __name__ == "__main__":
    # Generate OpenAPI schema
    schema = api.generate_openapi_schema(
        title="File Upload API",
        version="1.0.0",
        description="API for uploading files",
        output_format="yaml",
    )

    # Save the schema to a file
    with open("openapi.yaml", "w") as f:
        f.write(schema)

    # Run the app
    app.run(debug=True)