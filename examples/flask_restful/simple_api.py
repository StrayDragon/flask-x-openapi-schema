"""
Flask-RESTful 简单 API 示例。

展示如何使用 flask-x-openapi-schema 与 Flask-RESTful 集成。
"""

import os
from flask import Flask, jsonify
from flask_restful import Resource, Api

from flask_x_openapi_schema import OpenAPIIntegrationMixin
from flask_x_openapi_schema.x.flask_restful import openapi_metadata

# 导入共享模型
from examples.common.models import ItemRequest, ItemResponse, QueryParams

# 创建 Flask 应用
app = Flask(__name__)

# 创建支持 OpenAPI 的 API
class OpenAPIApi(OpenAPIIntegrationMixin, Api):
    pass

api = OpenAPIApi(app)

# 创建资源类
class ItemsResource(Resource):
    @openapi_metadata(
        summary="获取所有项目",
        description="获取项目列表，支持分页和排序",
        tags=["项目"],
        operation_id="getItems"
    )
    def get(self, x_request_query: QueryParams = None):
        """获取项目列表。"""
        # 在实际应用中，这里会从数据库获取数据
        items = [
            ItemResponse(
                id=f"item-{i}",
                name=f"测试项目 {i}",
                description=f"这是测试项目 {i} 的描述",
                price=10.99 + i,
                tags=["测试", f"标签{i}"]
            ) for i in range(1, x_request_query.limit + 1)
        ]
        
        # 应用排序
        reverse = x_request_query.order.lower() == "desc"
        items.sort(key=lambda x: getattr(x, x_request_query.sort_by), reverse=reverse)
        
        # 应用偏移
        items = items[x_request_query.offset:]
        
        return {"items": [item.model_dump() for item in items]}

    @openapi_metadata(
        summary="创建新项目",
        description="创建一个新的项目",
        tags=["项目"],
        operation_id="createItem"
    )
    def post(self, x_request_body: ItemRequest):
        """创建新项目。"""
        # 在实际应用中，这里会保存到数据库
        response = ItemResponse(
            id="new-item-1",
            name=x_request_body.name,
            description=x_request_body.description,
            price=x_request_body.price,
            tags=x_request_body.tags
        )
        return response, 201


class ItemResource(Resource):
    @openapi_metadata(
        summary="获取单个项目",
        description="通过ID获取项目",
        tags=["项目"],
        operation_id="getItem"
    )
    def get(self, item_id: str):
        """获取单个项目。"""
        # 在实际应用中，这里会从数据库获取数据
        response = ItemResponse(
            id=item_id,
            name="测试项目",
            description="这是一个测试项目",
            price=10.99,
            tags=["测试", "示例"]
        )
        return response

    @openapi_metadata(
        summary="更新项目",
        description="更新现有项目",
        tags=["项目"],
        operation_id="updateItem"
    )
    def put(self, item_id: str, x_request_body: ItemRequest):
        """更新项目。"""
        # 在实际应用中，这里会更新数据库
        response = ItemResponse(
            id=item_id,
            name=x_request_body.name,
            description=x_request_body.description,
            price=x_request_body.price,
            tags=x_request_body.tags
        )
        return response

    @openapi_metadata(
        summary="删除项目",
        description="删除现有项目",
        tags=["项目"],
        operation_id="deleteItem"
    )
    def delete(self, item_id: str):
        """删除项目。"""
        # 在实际应用中，这里会从数据库删除数据
        return {"message": f"项目 {item_id} 已删除"}, 200


# 注册资源
api.add_resource(ItemsResource, "/api/items")
api.add_resource(ItemResource, "/api/items/<string:item_id>")

# 添加获取 OpenAPI schema 的路由
@app.route("/openapi.yaml")
def get_openapi_yaml():
    """获取 OpenAPI schema (YAML 格式)。"""
    schema = api.generate_openapi_schema(
        title="项目 API",
        version="1.0.0",
        description="用于管理项目的 API",
    )
    return schema

@app.route("/openapi.json")
def get_openapi_json():
    """获取 OpenAPI schema (JSON 格式)。"""
    schema = api.generate_openapi_schema(
        title="项目 API",
        version="1.0.0",
        description="用于管理项目的 API",
        output_format="json"
    )
    return jsonify(schema)

# 添加 Swagger UI
@app.route("/")
def swagger_ui():
    """提供 Swagger UI 页面。"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Swagger UI</title>
        <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
        <script>
            window.onload = function() {
                window.ui = SwaggerUIBundle({
                    url: "/openapi.json",
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

# 保存 OpenAPI schema 到文件
def save_schema():
    """保存 OpenAPI schema 到文件。"""
    schema_dir = os.path.join(os.path.dirname(__file__), "schema")
    os.makedirs(schema_dir, exist_ok=True)
    
    # 保存 YAML 格式
    yaml_path = os.path.join(schema_dir, "openapi.yaml")
    with open(yaml_path, "w") as f:
        f.write(api.generate_openapi_schema(
            title="项目 API",
            version="1.0.0",
            description="用于管理项目的 API",
        ))
    
    # 保存 JSON 格式
    json_path = os.path.join(schema_dir, "openapi.json")
    with open(json_path, "w") as f:
        import json
        json.dump(
            api.generate_openapi_schema(
                title="项目 API",
                version="1.0.0",
                description="用于管理项目的 API",
                output_format="json"
            ),
            f,
            indent=2
        )
    
    print(f"Schema saved to {schema_dir}")

if __name__ == "__main__":
    # 保存 schema 到文件
    save_schema()
    
    # 启动应用
    app.run(debug=True, port=5000)