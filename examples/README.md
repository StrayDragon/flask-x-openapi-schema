# Flask-X-OpenAPI-Schema 示例

本目录包含了 Flask-X-OpenAPI-Schema 库的示例应用程序，展示了如何使用该库的各种功能。

## 目录结构

- `common/` - 共享的 Pydantic 模型和工具
- `flask/` - Flask.MethodView 示例
  - `simple_api.py` - 基本的 API 示例，展示参数绑定和 schema 生成
  - `file_upload.py` - 文件上传示例
  - `i18n_demo.py` - 国际化示例
- `flask_restful/` - Flask-RESTful 示例
  - `simple_api.py` - 基本的 API 示例，展示参数绑定和 schema 生成
  - `file_upload.py` - 文件上传示例
  - `i18n_demo.py` - 国际化示例

## 运行示例

### 使用 justfile 运行示例

项目根目录的 justfile 包含了运行示例的命令：

```bash
# 运行 Flask 基本示例
just run-example-flask-simple

# 运行 Flask 文件上传示例
just run-example-flask-file

# 运行 Flask 国际化示例
just run-example-flask-i18n

# 运行 Flask-RESTful 基本示例
just run-example-restful-simple

# 运行 Flask-RESTful 文件上传示例
just run-example-restful-file

# 运行 Flask-RESTful 国际化示例
just run-example-restful-i18n
```

## 示例功能

### 基本 API 示例

- 展示如何使用 `openapi_metadata` 装饰器
- 演示参数绑定（请求体、查询参数、路径参数）
- 生成 OpenAPI schema（YAML 和 JSON 格式）
- 提供 Swagger UI 界面

### 文件上传示例

- 展示如何处理文件上传
- 使用自定义文件模型进行验证
- 提供简单的文件上传表单

### 国际化示例

- 展示如何使用 `I18nStr` 进行国际化
- 支持多语言切换
- 在 OpenAPI schema 中使用多语言

## 关键概念

### 参数绑定

库使用特殊前缀自动检测和绑定参数：

- `x_request_body`: 请求体（JSON）
- `x_request_query`: 查询参数
- `x_request_path_<param_name>`: 路径参数
- `x_request_file`: 文件上传

### Schema 生成

- 使用 `generate_openapi_schema` 方法生成 OpenAPI schema
- 支持 YAML 和 JSON 格式
- 自动从 Pydantic 模型生成 schema

### 文件处理

- 使用 `FileUploadModel`、`ImageUploadModel` 和 `DocumentUploadModel` 处理文件上传
- 支持文件类型和大小验证

### 国际化

- 使用 `I18nStr` 定义多语言字符串
- 使用 `set_current_language` 和 `get_current_language` 管理当前语言
- 支持线程安全的语言切换