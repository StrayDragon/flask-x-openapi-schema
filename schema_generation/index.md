# OpenAPI Schema Generation in Flask-X-OpenAPI-Schema

This document explains how to generate OpenAPI schemas using Flask-X-OpenAPI-Schema, including customizing the schema, adding additional components, and serving the schema to clients.

## Overview

Flask-X-OpenAPI-Schema provides tools for generating OpenAPI 3.0.x schemas from your Flask and Flask-RESTful applications. The schema generation process is automatic and based on the metadata provided in your API endpoints.

## Basic Schema Generation

### With Flask.MethodView

```python
from flask import Flask, Blueprint
from flask_x_openapi_schema.x.flask.views import MethodViewOpenAPISchemaGenerator
import yaml

# Create a Flask app
app = Flask(__name__)
blueprint = Blueprint("api", __name__, url_prefix="/api")

# Register your views
# ...

# Register the blueprint
app.register_blueprint(blueprint)

# Generate OpenAPI schema
@app.route("/openapi.yaml")
def get_openapi_spec():
    generator = MethodViewOpenAPISchemaGenerator(
        title="My API",
        version="1.0.0",
        description="API for managing resources",
    )

    # Process MethodView resources
    generator.process_methodview_resources(blueprint)

    # Generate the schema
    schema = generator.generate_schema()

    # Convert to YAML
    yaml_content = yaml.dump(
        schema,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=True,
    )

    return yaml_content, 200, {"Content-Type": "text/yaml"}

```

### With Flask-RESTful

```python
from flask import Flask
from flask_restful import Api
from flask_x_openapi_schema.x.flask_restful import OpenAPIIntegrationMixin
import yaml

# Create a Flask app
app = Flask(__name__)

# Create an OpenAPI-enabled API
class OpenAPIApi(OpenAPIIntegrationMixin, Api):
    pass

api = OpenAPIApi(app)

# Register your resources
# ...

# Generate OpenAPI schema
@app.route("/openapi.yaml")
def get_openapi_spec():
    schema = api.generate_openapi_schema(
        title="My API",
        version="1.0.0",
        description="API for managing resources",
        output_format="json",
    )

    # Convert to YAML
    yaml_content = yaml.dump(
        schema,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=True,
    )

    return yaml_content, 200, {"Content-Type": "text/yaml"}

```

## Customizing the Schema

### Schema Information

You can customize the schema information by providing parameters to the schema generator:

```python
generator = MethodViewOpenAPISchemaGenerator(
    title="My API",
    version="1.0.0",
    description="API for managing resources",
    terms_of_service="https://example.com/terms/",
    contact={
        "name": "API Support",
        "url": "https://example.com/support/",
        "email": "support@example.com",
    },
    license={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

```

Or with Flask-RESTful:

```python
schema = api.generate_openapi_schema(
    title="My API",
    version="1.0.0",
    description="API for managing resources",
    terms_of_service="https://example.com/terms/",
    contact={
        "name": "API Support",
        "url": "https://example.com/support/",
        "email": "support@example.com",
    },
    license={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    output_format="json",
)

```

### Servers

You can specify the servers that the API is available on:

```python
generator = MethodViewOpenAPISchemaGenerator(
    # ...
    servers=[
        {
            "url": "https://api.example.com/v1",
            "description": "Production server",
        },
        {
            "url": "https://staging-api.example.com/v1",
            "description": "Staging server",
        },
        {
            "url": "https://dev-api.example.com/v1",
            "description": "Development server",
        },
    ],
)

```

Or with Flask-RESTful:

```python
schema = api.generate_openapi_schema(
    # ...
    servers=[
        {
            "url": "https://api.example.com/v1",
            "description": "Production server",
        },
        {
            "url": "https://staging-api.example.com/v1",
            "description": "Staging server",
        },
        {
            "url": "https://dev-api.example.com/v1",
            "description": "Development server",
        },
    ],
    output_format="json",
)

```

### Security Schemes

You can define security schemes for your API:

```python
generator = MethodViewOpenAPISchemaGenerator(
    # ...
    security_schemes={
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        },
        "apiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
        },
    },
)

```

Or with Flask-RESTful:

```python
schema = api.generate_openapi_schema(
    # ...
    security_schemes={
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        },
        "apiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
        },
    },
    output_format="json",
)

```

## Registering Additional Components

### Manually Registering Models

You can manually register additional models that might not be automatically detected:

```python
from flask_x_openapi_schema.x.flask.views import MethodViewOpenAPISchemaGenerator
from flask_x_openapi_schema.core.utils import pydantic_to_openapi_schema

# Create the schema generator
generator = MethodViewOpenAPISchemaGenerator(
    title="My API",
    version="1.0.0",
    description="API for managing resources",
)

# Manually register models
generator._register_model(UserResponse)
generator._register_model(ErrorResponse)
generator._register_model(ProductCategory)
generator._register_model(ProductStatus)

# Process MethodView resources
generator.process_methodview_resources(blueprint)

# Generate the schema
schema = generator.generate_schema()

```

Or with Flask-RESTful:

```python
# Generate the schema
schema = api.generate_openapi_schema(
    title="My API",
    version="1.0.0",
    description="API for managing resources",
    output_format="json",
)

# Manually register models
if "components" not in schema:
    schema["components"] = {}
if "schemas" not in schema["components"]:
    schema["components"]["schemas"] = {}

for model in [UserResponse, ErrorResponse, ProductCategory, ProductStatus]:
    model_schema = pydantic_to_openapi_schema(model)
    schema["components"]["schemas"][model.__name__] = model_schema

```

### Adding Tags

You can add tags to your OpenAPI schema to group operations:

```python
generator = MethodViewOpenAPISchemaGenerator(
    # ...
    tags=[
        {
            "name": "users",
            "description": "Operations related to users",
        },
        {
            "name": "products",
            "description": "Operations related to products",
        },
        {
            "name": "orders",
            "description": "Operations related to orders",
        },
    ],
)

```

Or with Flask-RESTful:

```python
schema = api.generate_openapi_schema(
    # ...
    tags=[
        {
            "name": "users",
            "description": "Operations related to users",
        },
        {
            "name": "products",
            "description": "Operations related to products",
        },
        {
            "name": "orders",
            "description": "Operations related to orders",
        },
    ],
    output_format="json",
)

```

## Serving the Schema

### Serving as YAML

```python
@app.route("/openapi.yaml")
def get_openapi_yaml():
    # Generate the schema
    # ...

    # Convert to YAML
    yaml_content = yaml.dump(
        schema,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=True,
    )

    return yaml_content, 200, {"Content-Type": "text/yaml"}

```

### Serving as JSON

```python
@app.route("/openapi.json")
def get_openapi_json():
    # Generate the schema
    # ...

    # Convert to JSON
    import json
    json_content = json.dumps(schema, ensure_ascii=False)

    return json_content, 200, {"Content-Type": "application/json"}

```

### Serving Swagger UI

```python
@app.route("/")
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>API Documentation</title>
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

```

### Serving ReDoc

```python
@app.route("/redoc")
def redoc():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>API Documentation</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
        <style>
            body {
                margin: 0;
                padding: 0;
            }
        </style>
    </head>
    <body>
        <redoc spec-url="/openapi.yaml"></redoc>
        <script src="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js"></script>
    </body>
    </html>
    """

```

## Advanced Schema Generation

### Internationalization

You can generate schemas in different languages using the internationalization support:

```python
from flask_x_openapi_schema import set_current_language

# Set the language for schema generation
set_current_language("zh-Hans")

# Generate the schema
# ...

```

### Customizing Schema Generation

You can customize the schema generation process by subclassing the schema generator:

```python
from flask_x_openapi_schema.x.flask.views import MethodViewOpenAPISchemaGenerator

class CustomSchemaGenerator(MethodViewOpenAPISchemaGenerator):
    def process_methodview_resources(self, blueprint):
        # Custom processing logic
        super().process_methodview_resources(blueprint)

    def generate_schema(self):
        # Custom schema generation logic
        schema = super().generate_schema()

        # Add custom components
        if "components" not in schema:
            schema["components"] = {}

        # Add custom security schemes
        if "securitySchemes" not in schema["components"]:
            schema["components"]["securitySchemes"] = {}

        schema["components"]["securitySchemes"]["customAuth"] = {
            "type": "apiKey",
            "in": "header",
            "name": "X-Custom-Auth",
        }

        return schema

# Use the custom generator
generator = CustomSchemaGenerator(
    title="My API",
    version="1.0.0",
    description="API for managing resources",
)

```

### Generating Multiple Schemas

You can generate multiple schemas for different parts of your API:

```python
# Generate schema for the main API
main_generator = MethodViewOpenAPISchemaGenerator(
    title="Main API",
    version="1.0.0",
    description="Main API for managing resources",
)
main_generator.process_methodview_resources(main_blueprint)
main_schema = main_generator.generate_schema()

# Generate schema for the admin API
admin_generator = MethodViewOpenAPISchemaGenerator(
    title="Admin API",
    version="1.0.0",
    description="Admin API for managing resources",
)
admin_generator.process_methodview_resources(admin_blueprint)
admin_schema = admin_generator.generate_schema()

# Serve the schemas
@app.route("/openapi.yaml")
def get_openapi_yaml():
    return yaml.dump(main_schema, sort_keys=False, default_flow_style=False), 200, {"Content-Type": "text/yaml"}

@app.route("/admin/openapi.yaml")
def get_admin_openapi_yaml():
    return yaml.dump(admin_schema, sort_keys=False, default_flow_style=False), 200, {"Content-Type": "text/yaml"}

```

## Working Examples

For complete working examples of schema generation, check out the example applications in the repository:

- [Flask MethodView Schema Generation](https://github.com/StrayDragon/flask-x-openapi-schema/tree/main/examples/flask/app.py#L972-L1000): Demonstrates generating OpenAPI schema from Flask.MethodView classes
- [Flask-RESTful Schema Generation](https://github.com/StrayDragon/flask-x-openapi-schema/tree/main/examples/flask_restful/app.py#L746-L774): Demonstrates generating OpenAPI schema from Flask-RESTful resources
- [Swagger UI Integration](https://github.com/StrayDragon/flask-x-openapi-schema/tree/main/examples/flask/app.py#L1003-L1030): Demonstrates integrating Swagger UI for API documentation

These examples show how to:

- Generate OpenAPI schema from Flask.MethodView classes and Flask-RESTful resources
- Customize schema information (title, version, description)
- Serve the schema as YAML or JSON
- Integrate Swagger UI for interactive API documentation

You can run the examples using the provided justfile commands:

```bash
# Run the Flask MethodView example
just run-example-flask

# Run the Flask-RESTful example
just run-example-flask-restful

```

## Conclusion

Flask-X-OpenAPI-Schema provides powerful tools for generating OpenAPI schemas from your Flask and Flask-RESTful applications. By using the schema generators and customizing the schema generation process, you can create comprehensive API documentation that accurately reflects your API's capabilities.
