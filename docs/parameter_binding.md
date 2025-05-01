# Parameter Binding in Flask-X-OpenAPI-Schema

This document explains how parameter binding works in Flask-X-OpenAPI-Schema and how to customize it for your needs.

## Overview

Flask-X-OpenAPI-Schema uses a convention-based approach to bind request parameters to function arguments. By using special prefixes, the library can automatically:

1. Extract parameters from different parts of the request
2. Convert them to the appropriate types
3. Validate them against Pydantic models
4. Document them in the OpenAPI schema

## Default Parameter Prefixes

By default, Flask-X-OpenAPI-Schema uses the following prefixes:

| Prefix | Source | Example |
|--------|--------|---------|
| `_x_body` | Request body (JSON) | `_x_body: UserModel` |
| `_x_query` | Query parameters | `_x_query: FilterParams` |
| `_x_path_` | Path parameters | Path parameter binding is automatic |
| `_x_file` | File uploads | `_x_file: ImageUploadModel` |

## Request Body Binding

Use the `_x_body` prefix to bind the request body to a Pydantic model:

```python
from pydantic import BaseModel, Field

class UserCreateRequest(BaseModel):
    username: str = Field(..., description="User's username")
    email: str = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")
    full_name: str = Field(None, description="User's full name")

@openapi_metadata(
    summary="Create a new user",
    # ...
)
def post(self, _x_body: UserCreateRequest):
    # _x_body is automatically populated from the request JSON
    user = {
        "id": "123",
        "username": _x_body.username,
        "email": _x_body.email,
        "full_name": _x_body.full_name,
    }
    return user, 201
```

This will generate the following OpenAPI schema:

```yaml
paths:
  /users:
    post:
      summary: Create a new user
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
```

## Query Parameter Binding

Use the `_x_query` prefix to bind query parameters to a Pydantic model:

```python
from pydantic import BaseModel, Field

class UserFilterParams(BaseModel):
    username: str = Field(None, description="Filter by username")
    email: str = Field(None, description="Filter by email")
    role: str = Field(None, description="Filter by role")
    active: bool = Field(None, description="Filter by active status")
    limit: int = Field(10, description="Maximum number of results to return")
    offset: int = Field(0, description="Number of results to skip")

@openapi_metadata(
    summary="Get all users",
    # ...
)
def get(self, _x_query: UserFilterParams = None):
    # _x_query is automatically populated from the query parameters
    users = [...]

    if _x_query:
        if _x_query.username:
            users = [user for user in users if _x_query.username in user["username"]]

        if _x_query.email:
            users = [user for user in users if _x_query.email in user["email"]]

        if _x_query.role:
            users = [user for user in users if user["role"] == _x_query.role]

        if _x_query.active is not None:
            users = [user for user in users if user["active"] == _x_query.active]

        # Apply pagination
        users = users[_x_query.offset:_x_query.offset + _x_query.limit]

    return users, 200
```

This will generate the following OpenAPI schema:

```yaml
paths:
  /users:
    get:
      summary: Get all users
      parameters:
        - name: username
          in: query
          description: Filter by username
          schema:
            type: string
        - name: email
          in: query
          description: Filter by email
          schema:
            type: string
        - name: role
          in: query
          description: Filter by role
          schema:
            type: string
        - name: active
          in: query
          description: Filter by active status
          schema:
            type: boolean
        - name: limit
          in: query
          description: Maximum number of results to return
          schema:
            type: integer
            default: 10
        - name: offset
          in: query
          description: Number of results to skip
          schema:
            type: integer
            default: 0
      responses:
        '200':
          description: List of users retrieved successfully
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/UserResponse'
```

## Path Parameter Binding

Path parameters are automatically bound to function arguments with matching names:

```python
@openapi_metadata(
    summary="Get a user by ID",
    # ...
)
def get(self, user_id: str):
    # user_id is automatically populated from the path parameter
    if user_id not in ["123", "456"]:
        return {"error": "User not found"}, 404

    user = {
        "id": user_id,
        "username": f"user{user_id}",
        "email": f"user{user_id}@example.com",
        "full_name": f"User {user_id}",
    }
    return user, 200
```

This will generate the following OpenAPI schema:

```yaml
paths:
  /users/{user_id}:
    get:
      summary: Get a user by ID
      parameters:
        - name: user_id
          in: path
          required: true
          description: User ID
          schema:
            type: string
      responses:
        '200':
          description: User retrieved successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserResponse'
        '404':
          description: User not found
```

## File Upload Binding

Use the `_x_file` prefix to bind file uploads to a file upload model:

```python
from flask_x_openapi_schema import ImageUploadModel

@openapi_metadata(
    summary="Upload a user profile picture",
    # ...
)
def post(self, user_id: str, _x_file: ImageUploadModel):
    # _x_file.file is automatically populated from the uploaded file
    file = _x_file.file

    # Save the file
    file.save(f"uploads/{user_id}_profile.jpg")

    return {"message": "Profile picture uploaded successfully"}, 201
```

This will generate the following OpenAPI schema:

```yaml
paths:
  /users/{user_id}/profile-picture:
    post:
      summary: Upload a user profile picture
      parameters:
        - name: user_id
          in: path
          required: true
          description: User ID
          schema:
            type: string
      requestBody:
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                file:
                  type: string
                  format: binary
                  description: Profile picture to upload
      responses:
        '201':
          description: Profile picture uploaded successfully
```

## Custom Parameter Names

You can use custom parameter names with the appropriate prefixes:

```python
@openapi_metadata(
    summary="Upload multiple files",
    # ...
)
def post(
    self,
    user_id: str,
    _x_file_profile: ImageUploadModel,
    _x_file_cover: ImageUploadModel,
    _x_body: UserUpdateRequest,
):
    # Access each parameter
    profile_pic = _x_file_profile.file
    cover_pic = _x_file_cover.file
    update_data = _x_body

    # Process files and data
    # ...

    return {"message": "Files uploaded and user updated successfully"}, 200
```

## Customizing Parameter Prefixes

You can customize the parameter prefixes using the `ConventionalPrefixConfig` class:

```python
from flask_x_openapi_schema import ConventionalPrefixConfig, configure_prefixes

# Create a custom configuration
custom_config = ConventionalPrefixConfig(
    request_body_prefix="req_body",
    request_query_prefix="req_query",
    request_path_prefix="req_path",
    request_file_prefix="req_file"
)

# Configure globally
configure_prefixes(custom_config)
```

### Global Configuration

To configure the prefixes globally for all endpoints:

```python
from flask_x_openapi_schema import ConventionalPrefixConfig, configure_prefixes

# Create a custom configuration
custom_config = ConventionalPrefixConfig(
    request_body_prefix="req_body",
    request_query_prefix="req_query",
    request_path_prefix="req_path",
    request_file_prefix="req_file"
)

# Configure globally
configure_prefixes(custom_config)

# Now you can use the custom prefixes in your endpoints
@openapi_metadata(
    summary="Create a new user",
    # ...
)
def post(self, req_body: UserCreateRequest):
    # req_body is automatically populated from the request JSON
    user = {
        "id": "123",
        "username": req_body.username,
        "email": req_body.email,
        "full_name": req_body.full_name,
    }
    return user, 201
```

### Per-Function Configuration

To configure the prefixes for a specific endpoint:

```python
from flask_x_openapi_schema import ConventionalPrefixConfig

# Create a custom configuration
custom_config = ConventionalPrefixConfig(
    request_body_prefix="req_body",
    request_query_prefix="req_query",
    request_path_prefix="req_path",
    request_file_prefix="req_file"
)

@openapi_metadata(
    summary="Create a new user",
    prefix_config=custom_config,
    # ...
)
def post(self, req_body: UserCreateRequest):
    # req_body is automatically populated from the request JSON
    user = {
        "id": "123",
        "username": req_body.username,
        "email": req_body.email,
        "full_name": req_body.full_name,
    }
    return user, 201
```

## Advanced Parameter Binding

### Combining Parameter Types

You can combine different parameter types in a single endpoint:

```python
@openapi_metadata(
    summary="Search users",
    # ...
)
def get(
    self,
    _x_query: UserSearchParams = None,
    _x_body: UserAdvancedSearchRequest = None,
):
    # _x_query is populated from query parameters
    # _x_body is populated from the request body

    # Combine search criteria
    search_criteria = {}

    if _x_query:
        search_criteria.update(_x_query.model_dump(exclude_none=True))

    if _x_body:
        search_criteria.update(_x_body.model_dump(exclude_none=True))

    # Perform search
    # ...

    return results, 200
```

### Optional Parameters

Parameters can be made optional by providing a default value:

```python
@openapi_metadata(
    summary="Get all users",
    # ...
)
def get(self, _x_query: UserFilterParams = None):
    # _x_query is None if no query parameters are provided
    if _x_query is None:
        # Return all users
        return all_users, 200

    # Filter users based on query parameters
    # ...

    return filtered_users, 200
```

### Nested Models

You can use nested Pydantic models for complex parameter structures:

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class Address(BaseModel):
    street: str = Field(..., description="Street address")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State or province")
    postal_code: str = Field(..., description="Postal code")
    country: str = Field(..., description="Country")

class UserCreateRequest(BaseModel):
    username: str = Field(..., description="User's username")
    email: str = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")
    full_name: Optional[str] = Field(None, description="User's full name")
    addresses: List[Address] = Field([], description="User's addresses")
    metadata: Dict[str, str] = Field({}, description="Additional metadata")

@openapi_metadata(
    summary="Create a new user",
    # ...
)
def post(self, _x_body: UserCreateRequest):
    # _x_body is automatically populated from the request JSON
    # You can access nested fields like _x_body.addresses[0].city

    # Process the request
    # ...

    return user, 201
```

## Working Examples

For complete working examples of parameter binding, check out the example applications in the repository:

- [Flask MethodView Parameter Binding Example](https://github.com/StrayDragon/flask-x-openapi-schema/tree/main/examples/flask/app.py#L126-L146): Demonstrates binding path, query, and body parameters
- [Flask-RESTful Parameter Binding Example](https://github.com/StrayDragon/flask-x-openapi-schema/tree/main/examples/flask_restful/app.py#L126-L146): Demonstrates binding path, query, and body parameters
- [Custom Prefix Configuration Example](https://github.com/StrayDragon/flask-x-openapi-schema/tree/main/examples/flask/app.py#L35-L45): Demonstrates customizing parameter prefixes

These examples show how to:

- Bind request body parameters using `_x_body`
- Bind query parameters using `_x_query`
- Bind path parameters automatically
- Customize parameter prefixes
- Validate parameters using Pydantic models

You can run the examples using the provided justfile commands:

```bash
# Run the Flask MethodView example
just run-example-flask

# Run the Flask-RESTful example
just run-example-flask-restful
```

## Conclusion

Flask-X-OpenAPI-Schema's parameter binding system provides a powerful and flexible way to handle request parameters in your API endpoints. By using special prefixes and Pydantic models, you can automatically extract, convert, validate, and document parameters from different parts of the request. You can also customize the parameter prefixes to match your preferred naming convention.
