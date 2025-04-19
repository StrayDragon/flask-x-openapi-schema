"""
Flask-RESTful 文件上传示例。

展示如何使用 flask-x-openapi-schema 处理文件上传。
"""

import os
from flask import Flask, send_from_directory
from flask_restful import Resource

from flask_x_openapi_schema import OpenAPIIntegrationMixin
from flask_x_openapi_schema.x.flask_restful import openapi_metadata

# 导入共享模型
from examples.common.models import CustomImageUploadModel, CustomDocumentUploadModel

# 创建 Flask 应用
app = Flask(__name__)

# 创建上传目录
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, "images"), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, "documents"), exist_ok=True)

# 创建支持 OpenAPI 的 API
class OpenAPIApi(OpenAPIIntegrationMixin, Api):
    pass

from flask_restful import Api
api = OpenAPIApi(app)

# 创建文件上传资源
class ImageUploadResource(Resource):
    @openapi_metadata(
        summary="上传图片",
        description="上传图片文件（支持 jpg, jpeg, png）",
        tags=["文件上传"],
        operation_id="uploadImage"
    )
    def post(self, x_request_file: CustomImageUploadModel):
        """上传图片文件。"""
        # 保存上传的文件
        filename = x_request_file.file.filename
        file_path = os.path.join(UPLOAD_FOLDER, "images", filename)
        x_request_file.file.save(file_path)
        
        return {
            "message": "图片上传成功",
            "filename": filename,
            "size": os.path.getsize(file_path),
            "url": f"/api/images/{filename}"
        }


class DocumentUploadResource(Resource):
    @openapi_metadata(
        summary="上传文档",
        description="上传文档文件（支持 pdf, doc, docx）",
        tags=["文件上传"],
        operation_id="uploadDocument"
    )
    def post(self, x_request_file: CustomDocumentUploadModel):
        """上传文档文件。"""
        # 保存上传的文件
        filename = x_request_file.file.filename
        file_path = os.path.join(UPLOAD_FOLDER, "documents", filename)
        x_request_file.file.save(file_path)
        
        return {
            "message": "文档上传成功",
            "filename": filename,
            "size": os.path.getsize(file_path),
            "url": f"/api/documents/{filename}"
        }


# 创建文件下载路由
@app.route("/api/images/<filename>")
def get_image(filename):
    """获取上传的图片。"""
    return send_from_directory(os.path.join(UPLOAD_FOLDER, "images"), filename)


@app.route("/api/documents/<filename>")
def get_document(filename):
    """获取上传的文档。"""
    return send_from_directory(os.path.join(UPLOAD_FOLDER, "documents"), filename)


# 注册资源
api.add_resource(ImageUploadResource, "/api/upload/image")
api.add_resource(DocumentUploadResource, "/api/upload/document")

# 添加获取 OpenAPI schema 的路由
@app.route("/openapi.yaml")
def get_openapi_yaml():
    """获取 OpenAPI schema (YAML 格式)。"""
    schema = api.generate_openapi_schema(
        title="文件上传 API",
        version="1.0.0",
        description="用于文件上传的 API",
    )
    return schema

# 添加 Swagger UI
@app.route("/")
def swagger_ui():
    """提供 Swagger UI 页面。"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>文件上传 API</title>
        <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
        <script>
            window.onload = function() {
                window.ui = SwaggerUIBundle({
                    url: "/openapi.yaml",
                    dom_id: '#swagger-ui',
                    deepLinking: true,
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIBundle.SwaggerUIStandalonePreset
                    ],
                    layout: "BaseLayout"
                });
            };
        </script>
    </body>
    </html>
    """

# 添加简单的文件上传表单
@app.route("/upload-form")
def upload_form():
    """提供简单的文件上传表单。"""
    return """
    <!DOCTYPE html>
    <html lang="zh">
    <head>
        <meta charset="UTF-8">
        <title>文件上传表单</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .form-container { margin-bottom: 30px; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
            h2 { color: #333; }
            label { display: block; margin-bottom: 10px; }
            input[type="file"] { margin-bottom: 15px; }
            button { background-color: #4CAF50; color: white; padding: 10px 15px; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background-color: #45a049; }
            .response { margin-top: 20px; padding: 10px; background-color: #f8f8f8; border-radius: 4px; white-space: pre-wrap; }
        </style>
    </head>
    <body>
        <h1>文件上传示例</h1>
        
        <div class="form-container">
            <h2>上传图片</h2>
            <form id="imageForm" enctype="multipart/form-data">
                <label for="imageFile">选择图片文件 (jpg, jpeg, png):</label>
                <input type="file" id="imageFile" name="file" accept=".jpg,.jpeg,.png">
                <button type="button" onclick="uploadFile('imageForm', '/api/upload/image')">上传图片</button>
            </form>
            <div id="imageResponse" class="response"></div>
        </div>
        
        <div class="form-container">
            <h2>上传文档</h2>
            <form id="documentForm" enctype="multipart/form-data">
                <label for="documentFile">选择文档文件 (pdf, doc, docx):</label>
                <input type="file" id="documentFile" name="file" accept=".pdf,.doc,.docx">
                <button type="button" onclick="uploadFile('documentForm', '/api/upload/document')">上传文档</button>
            </form>
            <div id="documentResponse" class="response"></div>
        </div>

        <script>
            function uploadFile(formId, url) {
                const form = document.getElementById(formId);
                const formData = new FormData(form);
                const responseDiv = form.nextElementSibling;
                
                responseDiv.textContent = '上传中...';
                
                fetch(url, {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    responseDiv.textContent = JSON.stringify(data, null, 2);
                    if (data.url) {
                        const link = document.createElement('a');
                        link.href = data.url;
                        link.textContent = '查看上传的文件';
                        link.target = '_blank';
                        responseDiv.appendChild(document.createElement('br'));
                        responseDiv.appendChild(link);
                    }
                })
                .catch(error => {
                    responseDiv.textContent = '上传失败: ' + error;
                });
            }
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(debug=True, port=5001)