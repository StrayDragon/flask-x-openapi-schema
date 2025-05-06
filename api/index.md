# API Reference

This section provides detailed API documentation for the Flask-X-OpenAPI-Schema library. The documentation is generated directly from the source code, ensuring it always stays in sync with the latest code.

## Overview

Flask-X-OpenAPI-Schema is organized into several main components:

- **Core Modules**: The foundation of the library, including configuration, caching, and schema generation.
- **Flask Integration**: Components for integrating with Flask applications.
- **Flask-RESTful Integration**: Components for integrating with Flask-RESTful applications.
- **Models**: Pydantic models for requests, responses, and file uploads.
- **Internationalization**: Support for multiple languages in your API documentation.

## Common Usage Patterns

### Basic Setup

```python
from flask import Flask
from flask_x_openapi_schema.core.config import ConventionalPrefixConfig, configure_prefixes
from flask_x_openapi_schema.x.flask import openapi_metadata

# Configure global prefix settings
config = ConventionalPrefixConfig(
    request_body_prefix="body",
    request_query_prefix="query",
    request_path_prefix="path"
)
configure_prefixes(config)

app = Flask(__name__)

```

### Using with Flask MethodView

```python
from flask.views import MethodView
from flask_x_openapi_schema.x.flask import openapi_metadata
from pydantic import BaseModel

class UserRequest(BaseModel):
    name: str
    email: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str

class UserView(MethodView):
    @openapi_metadata(
        summary="Create a new user",
        description="Creates a new user with the provided information",
        tags=["users"]
    )
    def post(self, x_request_body_user: UserRequest) -> UserResponse:
        # The parameter will be automatically bound from request body
        user_data = x_request_body_user
        # Process the data...
        return UserResponse(id=1, name=user_data.name, email=user_data.email)

```

### Using with Flask-RESTful

```python
from flask_restful import Resource
from flask_x_openapi_schema.x.flask_restful import openapi_metadata
from pydantic import BaseModel

class UserRequest(BaseModel):
    name: str
    email: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str

class UserResource(Resource):
    @openapi_metadata(
        summary="Create a new user",
        description="Creates a new user with the provided information",
        tags=["users"]
    )
    def post(self, x_request_body_user: UserRequest) -> UserResponse:
        # The parameter will be automatically bound from request body
        user_data = x_request_body_user
        # Process the data...
        return UserResponse(id=1, name=user_data.name, email=user_data.email).model_dump()

```

## API Documentation

For detailed API documentation, please refer to the following sections:

- [Core Modules](core/)
- [Flask Integration](flask/)
- [Flask-RESTful Integration](flask_restful/)
- [Models](models/)
- [Internationalization Support](i18n/)
