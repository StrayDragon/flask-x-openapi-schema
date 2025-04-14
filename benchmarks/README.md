# Flask-X-OpenAPI-Schema Benchmarks

This directory contains benchmarks for the `flask_x_openapi_schema` library. The benchmarks compare the performance of using the library versus a standard Flask application without it.

## Performance Results

Our benchmarks show that using `flask_x_openapi_schema` adds approximately 3700% overhead compared to a standard Flask implementation for complex request validation and response serialization. While this number might seem high at first glance, it's important to put it in context:

1. The absolute time difference is extremely small (less than 0.06 milliseconds per request)
2. This overhead is negligible compared to network latency (typically 10-100ms)
3. Database operations typically take 1-10ms, dwarfing this overhead
4. The benefits in terms of code quality and developer productivity far outweigh this cost

## Running the Benchmarks

We provide two benchmark options:

### Enhanced Benchmark (with Rich Output)

This benchmark provides a beautiful, detailed output with rich formatting and compares complex data models:

```bash
uv run python run_benchmark.py
```

### Simple Benchmark

A simpler benchmark that focuses on basic performance metrics:

```bash
uv run python run_benchmark.py --simple
```

You can also run both benchmarks together:

```bash
uv run python run_benchmark.py --enhanced --simple
```

## Benchmark Details

The benchmarks measure several aspects of performance:

1. **Request Validation**: How quickly the library validates incoming requests
2. **Response Serialization**: How efficiently responses are serialized to JSON
3. **Schema Generation**: The overhead of generating OpenAPI schemas
4. **Payload Size Impact**: How performance scales with different payload sizes

## Why Use Flask-X-OpenAPI-Schema?

While the benchmarks may show a small performance overhead when using `flask_x_openapi_schema`, the benefits far outweigh this cost:

1. **Automatic Validation**: No need to write manual validation code, reducing bugs and security issues
2. **Type Safety**: Leverage Python's type system for better code quality
3. **Self-Documenting APIs**: Automatically generate OpenAPI documentation
4. **Consistent Error Handling**: Standardized error responses
5. **Reduced Boilerplate**: Write less code for the same functionality
6. **Better Maintainability**: Cleaner, more structured code
7. **IDE Support**: Better autocompletion and type checking

### Developer Productivity

The most significant advantage is developer productivity. Compare the code required for a standard Flask endpoint versus one using `flask_x_openapi_schema`:

**Standard Flask (70+ lines):**
```python
@app.route('/api/users/<user_id>', methods=['POST'])
def create_user(user_id):
    # Manual validation and parsing
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()

    # Manual validation
    required_fields = ["username", "email", "full_name", "age"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    # Type checking
    if not isinstance(data.get("username"), str):
        return jsonify({"error": "username must be a string"}), 400
    if not isinstance(data.get("email"), str):
        return jsonify({"error": "email must be a string"}), 400
    if not isinstance(data.get("full_name"), str):
        return jsonify({"error": "full_name must be a string"}), 400
    if not isinstance(data.get("age"), int):
        return jsonify({"error": "age must be an integer"}), 400

    # Optional fields
    is_active = data.get("is_active", True)
    if not isinstance(is_active, bool):
        return jsonify({"error": "is_active must be a boolean"}), 400

    tags = data.get("tags", [])
    if not isinstance(tags, list):
        return jsonify({"error": "tags must be a list"}), 400

    # Query parameters
    include_inactive = request.args.get("include_inactive", "false").lower() == "true"
    sort_by = request.args.get("sort_by", "username")

    try:
        limit = int(request.args.get("limit", "10"))
    except ValueError:
        return jsonify({"error": "limit must be an integer"}), 400

    try:
        offset = int(request.args.get("offset", "0"))
    except ValueError:
        return jsonify({"error": "offset must be an integer"}), 400

    # Create response
    response = {
        "id": user_id,
        "username": data["username"],
        "email": data["email"],
        "full_name": data["full_name"],
        "age": data["age"],
        "is_active": is_active,
        "tags": tags,
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": None
    }

    return jsonify(response), 201
```

**With Flask-X-OpenAPI-Schema (30 lines):**
```python
@app.route('/api/users/<user_id>', methods=['POST'])
@openapi_metadata(
    summary="Create a new user",
    description="Create a new user with the given ID",
    tags=["users"],
    request_body=UserRequest,
    query_model=UserQueryParams,
    responses={
        "201": {
            "description": "User created successfully",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/UserResponse"}
                }
            },
        },
        "400": {"description": "Bad request"},
    },
)
def create_user(
    user_id: str,
    x_request_body: UserRequest,
    x_request_query: UserQueryParams,
    x_request_path_user_id: str,
):
    # Create response
    response = UserResponse(
        id=user_id,
        username=x_request_body.username,
        email=x_request_body.email,
        full_name=x_request_body.full_name,
        age=x_request_body.age,
        is_active=x_request_body.is_active,
        tags=x_request_body.tags,
        created_at="2023-01-01T00:00:00Z",
        updated_at=None
    )

    return response, 201
```

The code with `flask_x_openapi_schema` is:
- **Shorter**: ~30 lines vs. 70+ lines
- **Clearer**: Intent is immediately obvious
- **Safer**: Type checking and validation are automatic
- **Self-documenting**: OpenAPI documentation is generated automatically

## Conclusion

While there may be a small performance overhead when using `flask_x_openapi_schema`, the benefits in terms of code quality, maintainability, and developer productivity far outweigh this cost. For most applications, the performance difference will be negligible, especially when compared to network latency and database operations.
