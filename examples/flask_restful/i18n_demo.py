"""
Flask-RESTful 国际化示例。

展示如何使用 flask-x-openapi-schema 的国际化功能。
"""

from flask import Flask, request, jsonify
from flask_restful import Resource

from flask_x_openapi_schema import OpenAPIIntegrationMixin
from flask_x_openapi_schema.x.flask_restful import openapi_metadata
from flask_x_openapi_schema.i18n import I18nStr, get_current_language, set_current_language

# 创建 Flask 应用
app = Flask(__name__)

# 创建支持 OpenAPI 的 API
class OpenAPIApi(OpenAPIIntegrationMixin, Api):
    pass

from flask_restful import Api
api = OpenAPIApi(app)

# 定义多语言消息
MESSAGES = {
    "welcome": I18nStr({
        "en-US": "Welcome to the API",
        "zh-Hans": "欢迎使用 API",
        "ja-JP": "API へようこそ"
    }),
    "item_created": I18nStr({
        "en-US": "Item created successfully",
        "zh-Hans": "项目创建成功",
        "ja-JP": "アイテムが正常に作成されました"
    }),
    "item_not_found": I18nStr({
        "en-US": "Item not found",
        "zh-Hans": "未找到项目",
        "ja-JP": "アイテムが見つかりません"
    })
}

# 创建资源类
class WelcomeResource(Resource):
    @openapi_metadata(
        summary=I18nStr({
            "en-US": "Get welcome message",
            "zh-Hans": "获取欢迎消息",
            "ja-JP": "ウェルカムメッセージを取得する"
        }),
        description=I18nStr({
            "en-US": "Returns a welcome message in the current language",
            "zh-Hans": "返回当前语言的欢迎消息",
            "ja-JP": "現在の言語でウェルカムメッセージを返します"
        }),
        tags=["I18n Demo"],
        operation_id="getWelcome"
    )
    def get(self):
        """获取欢迎消息。"""
        return {
            "message": str(MESSAGES["welcome"]),
            "language": get_current_language()
        }


class ItemsResource(Resource):
    @openapi_metadata(
        summary=I18nStr({
            "en-US": "Create an item",
            "zh-Hans": "创建项目",
            "ja-JP": "アイテムを作成する"
        }),
        description=I18nStr({
            "en-US": "Create a new item with the given data",
            "zh-Hans": "使用给定数据创建新项目",
            "ja-JP": "指定されたデータで新しいアイテムを作成します"
        }),
        tags=["I18n Demo"],
        operation_id="createItem"
    )
    def post(self):
        """创建项目。"""
        # 模拟创建项目
        return {
            "message": str(MESSAGES["item_created"]),
            "language": get_current_language(),
            "item_id": "123"
        }, 201


class ItemResource(Resource):
    @openapi_metadata(
        summary=I18nStr({
            "en-US": "Get an item",
            "zh-Hans": "获取项目",
            "ja-JP": "アイテムを取得する"
        }),
        description=I18nStr({
            "en-US": "Get an item by ID",
            "zh-Hans": "通过 ID 获取项目",
            "ja-JP": "ID でアイテムを取得します"
        }),
        tags=["I18n Demo"],
        operation_id="getItem"
    )
    def get(self, item_id: str):
        """获取项目。"""
        # 模拟获取项目
        if item_id == "404":
            return {
                "message": str(MESSAGES["item_not_found"]),
                "language": get_current_language()
            }, 404
        
        return {
            "id": item_id,
            "name": I18nStr({
                "en-US": "Test Item",
                "zh-Hans": "测试项目",
                "ja-JP": "テストアイテム"
            }),
            "language": get_current_language()
        }


# 语言切换中间件
@app.before_request
def set_language_from_header():
    """从请求头或查询参数设置语言。"""
    # 从查询参数获取语言
    lang = request.args.get("lang")
    
    # 如果查询参数中没有语言，则从请求头获取
    if not lang:
        accept_language = request.headers.get("Accept-Language", "")
        if accept_language:
            # 简单解析 Accept-Language 头
            langs = [l.split(";")[0].strip() for l in accept_language.split(",")]
            if langs:
                lang = langs[0]
    
    # 设置语言（如果提供了有效的语言）
    if lang in ["en-US", "zh-Hans", "ja-JP"]:
        set_current_language(lang)
    else:
        # 默认使用英语
        set_current_language("en-US")


# 注册资源
api.add_resource(WelcomeResource, "/api/welcome")
api.add_resource(ItemsResource, "/api/items")
api.add_resource(ItemResource, "/api/items/<string:item_id>")

# 添加获取 OpenAPI schema 的路由
@app.route("/openapi.yaml")
def get_openapi_yaml():
    """获取 OpenAPI schema (YAML 格式)。"""
    # 使用请求中的语言
    lang = request.args.get("lang", "en-US")
    if lang in ["en-US", "zh-Hans", "ja-JP"]:
        set_current_language(lang)
    
    schema = api.generate_openapi_schema(
        title=I18nStr({
            "en-US": "I18n Demo API",
            "zh-Hans": "国际化演示 API",
            "ja-JP": "国際化デモ API"
        }),
        version="1.0.0",
        description=I18nStr({
            "en-US": "API demonstrating internationalization features",
            "zh-Hans": "演示国际化功能的 API",
            "ja-JP": "国際化機能を示す API"
        })
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
        <title>I18n Demo API</title>
        <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
        <style>
            .language-selector {
                padding: 10px;
                background-color: #f0f0f0;
                margin-bottom: 10px;
                border-radius: 4px;
            }
            .language-selector button {
                margin-right: 10px;
                padding: 5px 10px;
                cursor: pointer;
            }
            .language-selector button.active {
                background-color: #4990e2;
                color: white;
                border: none;
            }
        </style>
    </head>
    <body>
        <div class="language-selector">
            <strong>选择语言 / Select Language / 言語を選択:</strong>
            <button onclick="changeLanguage('en-US')" id="lang-en">English</button>
            <button onclick="changeLanguage('zh-Hans')" id="lang-zh">中文</button>
            <button onclick="changeLanguage('ja-JP')" id="lang-ja">日本語</button>
        </div>
        <div id="swagger-ui"></div>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
        <script>
            // 获取当前语言或使用默认语言
            let currentLang = localStorage.getItem('preferredLanguage') || 'en-US';
            
            // 更新按钮状态
            function updateButtons() {
                document.querySelectorAll('.language-selector button').forEach(btn => {
                    btn.classList.remove('active');
                });
                document.getElementById('lang-' + currentLang.split('-')[0]).classList.add('active');
            }
            
            // 切换语言
            function changeLanguage(lang) {
                currentLang = lang;
                localStorage.setItem('preferredLanguage', lang);
                updateButtons();
                
                // 重新加载 Swagger UI
                window.ui.specActions.download('/openapi.yaml?lang=' + lang);
            }
            
            // 初始化 Swagger UI
            window.onload = function() {
                updateButtons();
                
                window.ui = SwaggerUIBundle({
                    url: "/openapi.yaml?lang=" + currentLang,
                    dom_id: '#swagger-ui',
                    deepLinking: true,
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIBundle.SwaggerUIStandalonePreset
                    ],
                    layout: "BaseLayout",
                    requestInterceptor: (req) => {
                        // 添加 Accept-Language 头
                        req.headers = req.headers || {};
                        req.headers['Accept-Language'] = currentLang;
                        return req;
                    }
                });
            };
        </script>
    </body>
    </html>
    """

# 添加语言切换 API
@app.route("/api/languages")
def get_languages():
    """获取支持的语言列表。"""
    return jsonify({
        "current": get_current_language(),
        "supported": ["en-US", "zh-Hans", "ja-JP"]
    })

if __name__ == "__main__":
    app.run(debug=True, port=5002)