# Custom Error Handling Example

This example demonstrates how to create custom error types by extending the `APIError` abstract base class and implementing the `to_response` method.

## Features

- Custom error hierarchy with a base `CustomError` class
- Specialized error types for different error scenarios
- Complete freedom to define error structure and behavior
- Integration with Flask's error handling system
- Consistent error response format

## Running the Example

```bash
cd examples/custom_errors
python app.py
```

The application will start on http://localhost:5000.

## API Endpoints

### Get a User

```
GET /users/{user_id}
```

- Returns a user by ID
- Returns a 404 error if the user is not found

Example:
```bash
curl http://localhost:5000/users/1
curl http://localhost:5000/users/999  # Not found error
```

### Create a User

```
POST /users
```

- Creates a new user
- Validates the request body against the User model
- Returns validation errors if the data is invalid

Example:
```bash
curl -X POST http://localhost:5000/users \
  -H "Content-Type: application/json" \
  -d '{"username": "johndoe", "email": "john@example.com", "age": 25}'

# Validation error
curl -X POST http://localhost:5000/users \
  -H "Content-Type: application/json" \
  -d '{"username": "j", "email": "invalid-email", "age": 17}'
```

### Protected Resource

```
GET /protected
```

- Requires authentication via Bearer token
- Returns an authentication error if no token or invalid token is provided

Example:
```bash
curl http://localhost:5000/protected  # Authentication error

curl -H "Authorization: Bearer invalid-token" http://localhost:5000/protected  # Invalid token error

curl -H "Authorization: Bearer valid-token" http://localhost:5000/protected  # Success
```

## Custom Error Types

The example defines a custom error hierarchy:

```
APIError (abstract base class)
└── CustomError
    ├── ValidationError
    ├── NotFoundError
    └── AuthenticationError
```

### CustomError

Base class for all custom errors in the application:

```python
class CustomError(APIError):
    """Base class for all custom errors in this application."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()
        super().__init__(message)

    def to_response(self) -> Tuple[Dict[str, Any], int]:
        """Convert the error to a response tuple."""
        response_data = {
            "error": {
                "code": self.code,
                "message": self.message,
                "timestamp": self.timestamp,
            }
        }

        if self.details:
            response_data["error"]["details"] = self.details

        return response_data, self.status_code
```

### ValidationError

Error raised when request data fails validation:

```python
class ValidationError(CustomError):
    """Error raised when request data fails validation."""

    def __init__(
        self,
        field_errors: Dict[str, List[str]],
        message: str = "Validation failed",
    ):
        super().__init__(
            code="VALIDATION_ERROR",
            message=message,
            status_code=422,
            details={"fields": field_errors},
        )
```

## Error Response Format

All error responses follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "timestamp": "2023-05-05T12:00:00Z",
    "details": {
      "field1": "Error details for field1",
      "field2": "Error details for field2"
    }
  }
}
```

## Error Handling

The application registers error handlers for different types of exceptions:

```python
@app.errorhandler(APIError)
def handle_api_exception(error):
    """Handle API exceptions."""
    return handle_api_error(error)


@app.errorhandler(PydanticValidationError)
def handle_pydantic_validation_error(error):
    """Handle Pydantic validation errors."""
    field_errors = {}

    for err in error.errors():
        field = ".".join(str(loc) for loc in err["loc"])
        if field not in field_errors:
            field_errors[field] = []
        field_errors[field].append(err["msg"])

    return handle_api_error(ValidationError(field_errors))


@app.errorhandler(Exception)
def handle_exception(error):
    """Handle all other exceptions."""
    app.logger.exception("Unexpected error")
    return handle_api_error(
        CustomError(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred",
            status_code=500,
            details={"error": str(error)},
        ),
        include_traceback=app.debug,
    )
```
