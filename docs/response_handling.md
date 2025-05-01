# Response Handling in Flask-X-OpenAPI-Schema

This document explains how to handle API responses in Flask-X-OpenAPI-Schema, including defining response models, documenting responses in OpenAPI schemas, and returning responses from your API endpoints.

## Overview

Flask-X-OpenAPI-Schema provides a comprehensive system for handling API responses:

1. **Response Models**: Define response structures using Pydantic models
2. **Response Documentation**: Document responses in OpenAPI schemas using the `OpenAPIMetaResponse` class
3. **Response Generation**: Convert Pydantic models to Flask responses using the `BaseRespModel` class

## Response Models

### Basic Response Models

You can define response models using Pydantic's `BaseModel`:

```python
from pydantic import BaseModel, Field
from typing import List, Optional

class UserResponse(BaseModel):
    id: str = Field(..., description="User ID")
    username: str = Field(..., description="User's username")
    email: str = Field(..., description="User's email address")
    full_name: Optional[str] = Field(None, description="User's full name")
    created_at: str = Field(..., description="Creation timestamp")
```

### Using BaseRespModel

For more advanced response handling, you can use the `BaseRespModel` class, which provides additional functionality for converting models to Flask responses:

```python
from flask_x_openapi_schema import BaseRespModel
from pydantic import Field
from typing import Optional

class UserResponse(BaseRespModel):
    id: str = Field(..., description="User ID")
    username: str = Field(..., description="User's username")
    email: str = Field(..., description="User's email address")
    full_name: Optional[str] = Field(None, description="User's full name")
    created_at: str = Field(..., description="Creation timestamp")
```

The `BaseRespModel` class provides a `to_response` method that converts the model to a Flask response:

```python
@openapi_metadata(
    summary="Get a user by ID",
    # ...
)
def get(self, user_id: str):
    # Get user from database
    user = get_user_from_db(user_id)

    if not user:
        return {"error": "User not found"}, 404

    # Create response model
    response = UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        created_at=user.created_at.isoformat(),
    )

    # Convert to Flask response
    return response.to_response(200)
```

## Documenting Responses

### Using OpenAPIMetaResponse

The `OpenAPIMetaResponse` class provides a structured way to document responses in OpenAPI schemas:

```python
from flask_x_openapi_schema import OpenAPIMetaResponse, OpenAPIMetaResponseItem

@openapi_metadata(
    summary="Create a new user",
    description="Create a new user with the provided information",
    tags=["users"],
    operation_id="createUser",
    responses=OpenAPIMetaResponse(
        responses={
            "201": OpenAPIMetaResponseItem(
                model=UserResponse,
                description="User created successfully",
            ),
            "400": OpenAPIMetaResponseItem(
                model=ErrorResponse,
                description="Invalid request data",
            ),
            "409": OpenAPIMetaResponseItem(
                model=ErrorResponse,
                description="Username or email already exists",
            ),
            "500": OpenAPIMetaResponseItem(
                model=ErrorResponse,
                description="Internal server error",
            ),
        }
    ),
)
def post(self, _x_body: UserCreateRequest):
    # Implementation...
```

This will generate the following OpenAPI schema:

```yaml
paths:
  /users:
    post:
      summary: Create a new user
      description: Create a new user with the provided information
      tags:
        - users
      operationId: createUser
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UserCreateRequest'
      responses:
        '201':
          description: User created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserResponse'
        '400':
          description: Invalid request data
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '409':
          description: Username or email already exists
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '500':
          description: Internal server error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
```

### Response Without Model

You can also document responses without a model:

```python
@openapi_metadata(
    summary="Delete a user",
    description="Delete a user by ID",
    tags=["users"],
    operation_id="deleteUser",
    responses=OpenAPIMetaResponse(
        responses={
            "204": OpenAPIMetaResponseItem(
                description="User deleted successfully",
                msg="User deleted successfully",
            ),
            "404": OpenAPIMetaResponseItem(
                model=ErrorResponse,
                description="User not found",
            ),
            "500": OpenAPIMetaResponseItem(
                model=ErrorResponse,
                description="Internal server error",
            ),
        }
    ),
)
def delete(self, user_id: str):
    # Implementation...
```

## Returning Responses

### Basic Responses

You can return basic responses using Flask's standard response format:

```python
@openapi_metadata(
    summary="Get all users",
    # ...
)
def get(self):
    # Get users from database
    users = get_users_from_db()

    # Convert to response format
    response = [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "created_at": user.created_at.isoformat(),
        }
        for user in users
    ]

    return response, 200
```

### Using BaseRespModel

For more advanced response handling, you can use the `BaseRespModel` class:

```python
@openapi_metadata(
    summary="Get a user by ID",
    # ...
)
def get(self, user_id: str):
    # Get user from database
    user = get_user_from_db(user_id)

    if not user:
        error = ErrorResponse(
            error_code="USER_NOT_FOUND",
            message=f"User with ID {user_id} not found",
        )
        return error.to_response(404)

    # Create response model
    response = UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        created_at=user.created_at.isoformat(),
    )

    # Convert to Flask response
    return response.to_response(200)
```

### List Responses

For list responses, you can use a list of response models:

```python
@openapi_metadata(
    summary="Get all users",
    # ...
)
def get(self):
    # Get users from database
    users = get_users_from_db()

    # Convert to response models
    response = [
        UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            created_at=user.created_at.isoformat(),
        )
        for user in users
    ]

    # Convert to Flask response
    return [r.model_dump() for r in response], 200
```

## Advanced Response Handling

### Pagination

For paginated responses, you can create a pagination wrapper model:

```python
from flask_x_openapi_schema import BaseRespModel
from pydantic import Field
from typing import List, Generic, TypeVar

T = TypeVar('T')

class PaginatedResponse(BaseRespModel, Generic[T]):
    items: List[T] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Number of items per page")
    pages: int = Field(..., description="Total number of pages")

@openapi_metadata(
    summary="Get all users",
    # ...
)
def get(self, _x_query: PaginationParams = None):
    # Get pagination parameters
    page = _x_query.page if _x_query else 1
    per_page = _x_query.per_page if _x_query else 10

    # Get users from database with pagination
    users, total = get_users_from_db_paginated(page, per_page)

    # Calculate total pages
    pages = (total + per_page - 1) // per_page

    # Convert to response models
    user_responses = [
        UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            created_at=user.created_at.isoformat(),
        )
        for user in users
    ]

    # Create paginated response
    response = PaginatedResponse(
        items=user_responses,
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )

    # Convert to Flask response
    return response.to_response(200)
```

### Error Responses

For error responses, you can create an error response model:

```python
from flask_x_openapi_schema import BaseRespModel
from pydantic import Field
from typing import Optional, Dict, Any

class ErrorResponse(BaseRespModel):
    error_code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

@openapi_metadata(
    summary="Create a new user",
    # ...
)
def post(self, _x_body: UserCreateRequest):
    # Check if username already exists
    if username_exists(_x_body.username):
        error = ErrorResponse(
            error_code="USERNAME_EXISTS",
            message="Username already exists",
            details={"username": _x_body.username},
        )
        return error.to_response(409)

    # Check if email already exists
    if email_exists(_x_body.email):
        error = ErrorResponse(
            error_code="EMAIL_EXISTS",
            message="Email already exists",
            details={"email": _x_body.email},
        )
        return error.to_response(409)

    # Create user
    # ...
```

### Custom Response Headers

You can add custom headers to your responses:

```python
@openapi_metadata(
    summary="Get a user by ID",
    # ...
)
def get(self, user_id: str):
    # Get user from database
    user = get_user_from_db(user_id)

    if not user:
        error = ErrorResponse(
            error_code="USER_NOT_FOUND",
            message=f"User with ID {user_id} not found",
        )
        return error.to_response(404)

    # Create response model
    response = UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        created_at=user.created_at.isoformat(),
    )

    # Convert to Flask response with custom headers
    return response.to_response(
        200,
        headers={
            "X-RateLimit-Limit": "100",
            "X-RateLimit-Remaining": "99",
            "X-RateLimit-Reset": "1619789983",
        },
    )
```

## Working Examples

For complete working examples of response handling, check out the example applications in the repository:

- [Flask MethodView Response Example](https://github.com/StrayDragon/flask-x-openapi-schema/tree/main/examples/flask/response_example.py): Demonstrates structured responses with OpenAPIMetaResponse
- [Flask-RESTful Response Example](https://github.com/StrayDragon/flask-x-openapi-schema/tree/main/examples/flask_restful/response_example.py): Demonstrates structured responses with OpenAPIMetaResponse
- [Error Response Example](https://github.com/StrayDragon/flask-x-openapi-schema/tree/main/examples/flask/app.py#L126-L146): Demonstrates error response handling

These examples show how to:

- Define response models using Pydantic
- Document responses using OpenAPIMetaResponse
- Return responses with appropriate status codes
- Handle error responses
- Use BaseRespModel for automatic response conversion

You can run the examples using the provided justfile commands:

```bash
# Run the Flask MethodView response example
just run-response-example-flask

# Run the Flask-RESTful response example
just run-response-example-flask-restful
```

## Conclusion

Flask-X-OpenAPI-Schema provides a comprehensive system for handling API responses. By using Pydantic models, the `OpenAPIMetaResponse` class, and the `BaseRespModel` class, you can define, document, and return responses from your API endpoints in a structured and consistent way.
