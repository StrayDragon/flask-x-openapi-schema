# Models

This section provides documentation for the model classes in Flask-X-OpenAPI-Schema.

## Base Models

Base models for OpenAPI schema generation.

This module provides base models for generating OpenAPI schemas and handling API responses. It includes the BaseRespModel class which extends Pydantic's BaseModel to provide standardized methods for converting models to Flask-compatible responses.

#### `BaseErrorResponse`

Bases: `BaseRespModel`

Base model for API error responses.

This class extends BaseRespModel to provide a standard way to represent error responses. It includes fields for error code, message, and details.

All error responses in the application should inherit from this class to ensure consistent error handling.

Attributes:

| Name | Type | Description | | --- | --- | --- | | `error` | `str` | Error identifier or code. | | `message` | `str` | Human-readable error message. | | `details` | `dict[str, Any] | None` | Optional additional error details. |

Examples:

```pycon
>>> from flask_x_openapi_schema import BaseErrorResponse
>>> error = BaseErrorResponse(error="VALIDATION_ERROR", message="Invalid input data")
>>> response = error.to_response(400)
>>> response[1]
400
>>> response[0]["error"]
'VALIDATION_ERROR'

```

Source code in `src/flask_x_openapi_schema/models/base.py`

```python
class BaseErrorResponse(BaseRespModel):
    """Base model for API error responses.

    This class extends BaseRespModel to provide a standard way to represent
    error responses. It includes fields for error code, message, and details.

    All error responses in the application should inherit from this class
    to ensure consistent error handling.

    Attributes:
        error: Error identifier or code.
        message: Human-readable error message.
        details: Optional additional error details.

    Examples:
        >>> from flask_x_openapi_schema import BaseErrorResponse
        >>> error = BaseErrorResponse(error="VALIDATION_ERROR", message="Invalid input data")
        >>> response = error.to_response(400)
        >>> response[1]
        400
        >>> response[0]["error"]
        'VALIDATION_ERROR'

    """

    error: str = Field(..., description="Error identifier or code")
    message: str = Field(..., description="Human-readable error message")
    details: dict[str, Any] | None = Field(None, description="Additional error details")

```

#### `BaseRespModel`

Bases: `BaseModel`

Base model for API responses.

This class extends Pydantic's BaseModel to provide a standard way to convert response models to Flask-compatible responses. It includes methods for converting the model to dictionaries and Flask response objects.

Attributes:

| Name | Type | Description | | --- | --- | --- | | `model_config` | | Configuration for the Pydantic model. |

Examples:

```pycon
>>> from flask_x_openapi_schema import BaseRespModel
>>> from pydantic import Field
>>>
>>> class UserResponse(BaseRespModel):
...     id: str = Field(..., description="User ID")
...     name: str = Field(..., description="User name")
...     email: str = Field(..., description="User email")
>>> def get(self):
...     return UserResponse(id="123", name="John Doe", email="john@example.com")
>>> def post(self):
...     return UserResponse(id="123", name="John Doe", email="john@example.com"), 201
>>> def put(self):
...     user = UserResponse(id="123", name="John Doe", email="john@example.com")
...     return user.to_response(status_code=200)

```

Source code in `src/flask_x_openapi_schema/models/base.py`

```python
class BaseRespModel(BaseModel):
    """Base model for API responses.

    This class extends Pydantic's BaseModel to provide a standard way to convert
    response models to Flask-compatible responses. It includes methods for converting
    the model to dictionaries and Flask response objects.

    Attributes:
        model_config: Configuration for the Pydantic model.

    Examples:
        >>> from flask_x_openapi_schema import BaseRespModel
        >>> from pydantic import Field
        >>>
        >>> class UserResponse(BaseRespModel):
        ...     id: str = Field(..., description="User ID")
        ...     name: str = Field(..., description="User name")
        ...     email: str = Field(..., description="User email")
        >>> def get(self):
        ...     return UserResponse(id="123", name="John Doe", email="john@example.com")
        >>> def post(self):
        ...     return UserResponse(id="123", name="John Doe", email="john@example.com"), 201
        >>> def put(self):
        ...     user = UserResponse(id="123", name="John Doe", email="john@example.com")
        ...     return user.to_response(status_code=200)

    """

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        extra="ignore",
        arbitrary_types_allowed=True,
    )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create a model instance from a dictionary.

        Args:
            data: Dictionary containing model data.

        Returns:
            An instance of the model.

        Examples:
            >>> from flask_x_openapi_schema import BaseRespModel
            >>> from pydantic import Field
            >>> class UserResponse(BaseRespModel):
            ...     id: str = Field(..., description="User ID")
            ...     name: str = Field(..., description="User name")
            ...     email: str = Field(..., description="User email")
            >>> data = {"id": "123", "name": "John Doe", "email": "john@example.com"}
            >>> user = UserResponse.from_dict(data)
            >>> user.id
            '123'

        """
        return cls(**data)

    def to_dict(self) -> dict[str, Any]:
        """Convert the model to a dictionary.

        Returns:
            A dictionary representation of the model.

        Examples:
            >>> from flask_x_openapi_schema import BaseRespModel
            >>> from pydantic import Field
            >>> class UserResponse(BaseRespModel):
            ...     id: str = Field(..., description="User ID")
            ...     name: str = Field(..., description="User name")
            ...     email: str = Field(..., description="User email")
            >>> user = UserResponse(id="123", name="John Doe", email="john@example.com")
            >>> user_dict = user.to_dict()
            >>> user_dict
            {'id': '123', 'name': 'John Doe', 'email': 'john@example.com'}

        """
        return self.model_dump(exclude_none=True, mode="json")

    def to_response(self, status_code: int | None = None) -> dict[str, Any] | tuple[dict[str, Any], int]:
        """Convert the model to a Flask-compatible response.

        Args:
            status_code: Optional HTTP status code.

        Returns:
            A Flask-compatible response (dict or tuple with dict and status code).

        Examples:
            >>> from flask_x_openapi_schema import BaseRespModel
            >>> from pydantic import Field
            >>> class UserResponse(BaseRespModel):
            ...     id: str = Field(..., description="User ID")
            ...     name: str = Field(..., description="User name")
            ...     email: str = Field(..., description="User email")
            >>> user = UserResponse(id="123", name="John Doe", email="john@example.com")
            >>> response = user.to_response()
            >>> isinstance(response, dict)
            True
            >>> response = user.to_response(status_code=201)
            >>> isinstance(response, tuple) and response[1] == 201
            True

        """
        response_dict = self.to_dict()

        if status_code is not None:
            return response_dict, status_code

        return response_dict

```

##### `from_dict(data)`

Create a model instance from a dictionary.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `data` | `dict[str, Any]` | Dictionary containing model data. | *required* |

Returns:

| Type | Description | | --- | --- | | `Self` | An instance of the model. |

Examples:

```pycon
>>> from flask_x_openapi_schema import BaseRespModel
>>> from pydantic import Field
>>> class UserResponse(BaseRespModel):
...     id: str = Field(..., description="User ID")
...     name: str = Field(..., description="User name")
...     email: str = Field(..., description="User email")
>>> data = {"id": "123", "name": "John Doe", "email": "john@example.com"}
>>> user = UserResponse.from_dict(data)
>>> user.id
'123'

```

Source code in `src/flask_x_openapi_schema/models/base.py`

```python
@classmethod
def from_dict(cls, data: dict[str, Any]) -> Self:
    """Create a model instance from a dictionary.

    Args:
        data: Dictionary containing model data.

    Returns:
        An instance of the model.

    Examples:
        >>> from flask_x_openapi_schema import BaseRespModel
        >>> from pydantic import Field
        >>> class UserResponse(BaseRespModel):
        ...     id: str = Field(..., description="User ID")
        ...     name: str = Field(..., description="User name")
        ...     email: str = Field(..., description="User email")
        >>> data = {"id": "123", "name": "John Doe", "email": "john@example.com"}
        >>> user = UserResponse.from_dict(data)
        >>> user.id
        '123'

    """
    return cls(**data)

```

##### `to_dict()`

Convert the model to a dictionary.

Returns:

| Type | Description | | --- | --- | | `dict[str, Any]` | A dictionary representation of the model. |

Examples:

```pycon
>>> from flask_x_openapi_schema import BaseRespModel
>>> from pydantic import Field
>>> class UserResponse(BaseRespModel):
...     id: str = Field(..., description="User ID")
...     name: str = Field(..., description="User name")
...     email: str = Field(..., description="User email")
>>> user = UserResponse(id="123", name="John Doe", email="john@example.com")
>>> user_dict = user.to_dict()
>>> user_dict
{'id': '123', 'name': 'John Doe', 'email': 'john@example.com'}

```

Source code in `src/flask_x_openapi_schema/models/base.py`

```python
def to_dict(self) -> dict[str, Any]:
    """Convert the model to a dictionary.

    Returns:
        A dictionary representation of the model.

    Examples:
        >>> from flask_x_openapi_schema import BaseRespModel
        >>> from pydantic import Field
        >>> class UserResponse(BaseRespModel):
        ...     id: str = Field(..., description="User ID")
        ...     name: str = Field(..., description="User name")
        ...     email: str = Field(..., description="User email")
        >>> user = UserResponse(id="123", name="John Doe", email="john@example.com")
        >>> user_dict = user.to_dict()
        >>> user_dict
        {'id': '123', 'name': 'John Doe', 'email': 'john@example.com'}

    """
    return self.model_dump(exclude_none=True, mode="json")

```

##### `to_response(status_code=None)`

Convert the model to a Flask-compatible response.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `status_code` | `int | None` | Optional HTTP status code. | `None` |

Returns:

| Type | Description | | --- | --- | | `dict[str, Any] | tuple[dict[str, Any], int]` | A Flask-compatible response (dict or tuple with dict and status code). |

Examples:

```pycon
>>> from flask_x_openapi_schema import BaseRespModel
>>> from pydantic import Field
>>> class UserResponse(BaseRespModel):
...     id: str = Field(..., description="User ID")
...     name: str = Field(..., description="User name")
...     email: str = Field(..., description="User email")
>>> user = UserResponse(id="123", name="John Doe", email="john@example.com")
>>> response = user.to_response()
>>> isinstance(response, dict)
True
>>> response = user.to_response(status_code=201)
>>> isinstance(response, tuple) and response[1] == 201
True

```

Source code in `src/flask_x_openapi_schema/models/base.py`

```python
def to_response(self, status_code: int | None = None) -> dict[str, Any] | tuple[dict[str, Any], int]:
    """Convert the model to a Flask-compatible response.

    Args:
        status_code: Optional HTTP status code.

    Returns:
        A Flask-compatible response (dict or tuple with dict and status code).

    Examples:
        >>> from flask_x_openapi_schema import BaseRespModel
        >>> from pydantic import Field
        >>> class UserResponse(BaseRespModel):
        ...     id: str = Field(..., description="User ID")
        ...     name: str = Field(..., description="User name")
        ...     email: str = Field(..., description="User email")
        >>> user = UserResponse(id="123", name="John Doe", email="john@example.com")
        >>> response = user.to_response()
        >>> isinstance(response, dict)
        True
        >>> response = user.to_response(status_code=201)
        >>> isinstance(response, tuple) and response[1] == 201
        True

    """
    response_dict = self.to_dict()

    if status_code is not None:
        return response_dict, status_code

    return response_dict

```

## File Upload Models

Pydantic models for file uploads in OpenAPI.

This module provides a structured way to handle file uploads with validation and type hints. The models are designed to work with OpenAPI 3.0.x specification and provide proper validation for different file types.

#### `AudioField`

Bases: `FileField`

Field for audio file uploads in OpenAPI schema.

Source code in `src/flask_x_openapi_schema/models/file_models.py`

```python
class AudioField(FileField):
    """Field for audio file uploads in OpenAPI schema."""

```

#### `DocumentUploadModel`

Bases: `FileUploadModel`

Model for document file uploads with validation.

This model extends FileUploadModel to provide specific validation for document files. It validates file extensions and optionally checks file size.

Attributes:

| Name | Type | Description | | --- | --- | --- | | `file` | `FileStorage` | The uploaded document file. | | `allowed_extensions` | `list[str]` | List of allowed file extensions. | | `max_size` | `int | None` | Maximum file size in bytes. |

Source code in `src/flask_x_openapi_schema/models/file_models.py`

```python
class DocumentUploadModel(FileUploadModel):
    """Model for document file uploads with validation.

    This model extends FileUploadModel to provide specific validation for document files.
    It validates file extensions and optionally checks file size.

    Attributes:
        file: The uploaded document file.
        allowed_extensions: List of allowed file extensions.
        max_size: Maximum file size in bytes.

    """

    file: FileStorage = Field(..., description="The uploaded document file")
    allowed_extensions: list[str] = Field(
        default=["pdf", "doc", "docx", "txt", "rtf", "md"],
        description="Allowed file extensions",
    )
    max_size: int | None = Field(default=None, description="Maximum file size in bytes")

    @field_validator("file")
    @classmethod
    def validate_document_file(cls, v: FileStorage, info: pydantic.ValidationInfo) -> FileStorage:
        """Validate that the file is a document with allowed extension and size.

        Args:
            v: The file to validate.
            info: Validation context information.

        Returns:
            FileStorage: The validated file.

        Raises:
            ValueError: If the file is invalid, has a disallowed extension, or exceeds the maximum size.

        """
        values = info.data

        if not v or not v.filename:
            msg = "No file provided"
            raise ValueError(msg)

        allowed_extensions = values.get("allowed_extensions", ["pdf", "doc", "docx", "txt", "rtf", "md"])
        if "." in v.filename:
            ext = v.filename.rsplit(".", 1)[1].lower()
            if ext not in allowed_extensions:
                msg = f"File extension '{ext}' not allowed. Allowed extensions: {', '.join(allowed_extensions)}"
                raise ValueError(
                    msg,
                )

        max_size = values.get("max_size")
        if max_size is not None:
            v.seek(0, 2)
            size = v.tell()
            v.seek(0)

            if size > max_size:
                msg = f"File size ({size} bytes) exceeds maximum allowed size ({max_size} bytes)"
                raise ValueError(msg)

        return v

```

##### `validate_document_file(v, info)`

Validate that the file is a document with allowed extension and size.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `v` | `FileStorage` | The file to validate. | *required* | | `info` | `ValidationInfo` | Validation context information. | *required* |

Returns:

| Name | Type | Description | | --- | --- | --- | | `FileStorage` | `FileStorage` | The validated file. |

Raises:

| Type | Description | | --- | --- | | `ValueError` | If the file is invalid, has a disallowed extension, or exceeds the maximum size. |

Source code in `src/flask_x_openapi_schema/models/file_models.py`

```python
@field_validator("file")
@classmethod
def validate_document_file(cls, v: FileStorage, info: pydantic.ValidationInfo) -> FileStorage:
    """Validate that the file is a document with allowed extension and size.

    Args:
        v: The file to validate.
        info: Validation context information.

    Returns:
        FileStorage: The validated file.

    Raises:
        ValueError: If the file is invalid, has a disallowed extension, or exceeds the maximum size.

    """
    values = info.data

    if not v or not v.filename:
        msg = "No file provided"
        raise ValueError(msg)

    allowed_extensions = values.get("allowed_extensions", ["pdf", "doc", "docx", "txt", "rtf", "md"])
    if "." in v.filename:
        ext = v.filename.rsplit(".", 1)[1].lower()
        if ext not in allowed_extensions:
            msg = f"File extension '{ext}' not allowed. Allowed extensions: {', '.join(allowed_extensions)}"
            raise ValueError(
                msg,
            )

    max_size = values.get("max_size")
    if max_size is not None:
        v.seek(0, 2)
        size = v.tell()
        v.seek(0)

        if size > max_size:
            msg = f"File size ({size} bytes) exceeds maximum allowed size ({max_size} bytes)"
            raise ValueError(msg)

    return v

```

#### `FileField`

Bases: `str`

Field for file uploads in OpenAPI schema.

This class is used as a type annotation for file upload fields in Pydantic models. It is a subclass of str, but with additional metadata for OpenAPI schema generation.

Source code in `src/flask_x_openapi_schema/models/file_models.py`

```python
class FileField(str):
    """Field for file uploads in OpenAPI schema.

    This class is used as a type annotation for file upload fields in Pydantic models.
    It is a subclass of str, but with additional metadata for OpenAPI schema generation.
    """

    __slots__ = ()

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: Any) -> core_schema.PlainValidatorFunctionSchema:
        """Define the Pydantic core schema for this type.

        This is the recommended way to define custom types in Pydantic v2.

        Args:
            _source_type: Source type information from Pydantic.
            _handler: Handler function from Pydantic.

        Returns:
            A Pydantic core schema for this type.

        """
        return core_schema.with_info_plain_validator_function(
            cls._validate,
            serialization=core_schema.str_schema(),
        )

    @classmethod
    def _validate(cls, v: _T, info: pydantic.ValidationInfo) -> _T:  # noqa: ARG003
        """Validate the value according to Pydantic v2 requirements.

        Args:
            v: The value to validate.
            info: Validation context information from Pydantic.

        Returns:
            The validated value.

        Raises:
            ValueError: If the value is None.

        """
        if v is None:
            msg = "File is required"
            raise ValueError(msg)
        return v

    @classmethod
    def __get_pydantic_json_schema__(cls, _schema_generator: Any, _field_schema: Any) -> dict[str, str]:
        """Define the JSON schema for OpenAPI.

        Args:
            _schema_generator: Schema generator from Pydantic.
            _field_schema: Field schema from Pydantic.

        Returns:
            dict: A dictionary representing the JSON schema for this field.

        """
        return {"type": "string", "format": "binary"}

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:  # noqa: ARG004
        """Create a new instance of the class.

        If a file object is provided, return it directly.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            The file object if provided, otherwise a new instance of the class.

        """
        file_obj = kwargs.get("file")
        if file_obj is not None:
            return file_obj
        return str.__new__(cls, "")

```

##### `__get_pydantic_core_schema__(_source_type, _handler)`

Define the Pydantic core schema for this type.

This is the recommended way to define custom types in Pydantic v2.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `_source_type` | `Any` | Source type information from Pydantic. | *required* | | `_handler` | `Any` | Handler function from Pydantic. | *required* |

Returns:

| Type | Description | | --- | --- | | `PlainValidatorFunctionSchema` | A Pydantic core schema for this type. |

Source code in `src/flask_x_openapi_schema/models/file_models.py`

```python
@classmethod
def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: Any) -> core_schema.PlainValidatorFunctionSchema:
    """Define the Pydantic core schema for this type.

    This is the recommended way to define custom types in Pydantic v2.

    Args:
        _source_type: Source type information from Pydantic.
        _handler: Handler function from Pydantic.

    Returns:
        A Pydantic core schema for this type.

    """
    return core_schema.with_info_plain_validator_function(
        cls._validate,
        serialization=core_schema.str_schema(),
    )

```

##### `__get_pydantic_json_schema__(_schema_generator, _field_schema)`

Define the JSON schema for OpenAPI.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `_schema_generator` | `Any` | Schema generator from Pydantic. | *required* | | `_field_schema` | `Any` | Field schema from Pydantic. | *required* |

Returns:

| Name | Type | Description | | --- | --- | --- | | `dict` | `dict[str, str]` | A dictionary representing the JSON schema for this field. |

Source code in `src/flask_x_openapi_schema/models/file_models.py`

```python
@classmethod
def __get_pydantic_json_schema__(cls, _schema_generator: Any, _field_schema: Any) -> dict[str, str]:
    """Define the JSON schema for OpenAPI.

    Args:
        _schema_generator: Schema generator from Pydantic.
        _field_schema: Field schema from Pydantic.

    Returns:
        dict: A dictionary representing the JSON schema for this field.

    """
    return {"type": "string", "format": "binary"}

```

##### `__new__(*args, **kwargs)`

Create a new instance of the class.

If a file object is provided, return it directly.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `*args` | `Any` | Variable length argument list. | `()` | | `**kwargs` | `Any` | Arbitrary keyword arguments. | `{}` |

Returns:

| Type | Description | | --- | --- | | `Any` | The file object if provided, otherwise a new instance of the class. |

Source code in `src/flask_x_openapi_schema/models/file_models.py`

```python
def __new__(cls, *args: Any, **kwargs: Any) -> Any:  # noqa: ARG004
    """Create a new instance of the class.

    If a file object is provided, return it directly.

    Args:
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.

    Returns:
        The file object if provided, otherwise a new instance of the class.

    """
    file_obj = kwargs.get("file")
    if file_obj is not None:
        return file_obj
    return str.__new__(cls, "")

```

#### `FileType`

Bases: `str`, `Enum`

Enumeration of file types for OpenAPI schema.

Source code in `src/flask_x_openapi_schema/models/file_models.py`

```python
class FileType(str, Enum):
    """Enumeration of file types for OpenAPI schema."""

    BINARY = "binary"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    PDF = "pdf"
    TEXT = "text"

```

#### `FileUploadModel`

Bases: `BaseModel`

Base model for file uploads.

This model provides a structured way to handle file uploads with validation. It automatically validates that the uploaded file is a valid FileStorage instance.

Attributes:

| Name | Type | Description | | --- | --- | --- | | `file` | `FileStorage` | The uploaded file. |

Examples:

```pycon
>>> from flask_x_openapi_schema.models.file_models import FileUploadModel
>>> # Example usage in a Flask route
>>> # @openapi_metadata(summary="Upload a file")
>>> # def post(self, _x_file: FileUploadModel):
>>> #     return {"filename": _x_file.file.filename}

```

Source code in `src/flask_x_openapi_schema/models/file_models.py`

```python
class FileUploadModel(BaseModel):
    """Base model for file uploads.

    This model provides a structured way to handle file uploads with validation.
    It automatically validates that the uploaded file is a valid FileStorage instance.

    Attributes:
        file: The uploaded file.

    Examples:
        >>> from flask_x_openapi_schema.models.file_models import FileUploadModel
        >>> # Example usage in a Flask route
        >>> # @openapi_metadata(summary="Upload a file")
        >>> # def post(self, _x_file: FileUploadModel):
        >>> #     return {"filename": _x_file.file.filename}

    """

    file: FileStorage = Field(..., description="The uploaded file")

    model_config = ConfigDict(arbitrary_types_allowed=True, json_schema_extra={"multipart/form-data": True})

    @field_validator("file")
    @classmethod
    def validate_file(cls, v: Any) -> FileStorage:
        """Validate that the file is a FileStorage instance.

        Args:
            v: The value to validate.

        Returns:
            FileStorage: The validated FileStorage instance.

        Raises:
            ValueError: If the value is not a FileStorage instance.

        """
        if not isinstance(v, FileStorage):
            msg = "Not a valid file upload"
            raise ValueError(msg)
        return v

```

##### `validate_file(v)`

Validate that the file is a FileStorage instance.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `v` | `Any` | The value to validate. | *required* |

Returns:

| Name | Type | Description | | --- | --- | --- | | `FileStorage` | `FileStorage` | The validated FileStorage instance. |

Raises:

| Type | Description | | --- | --- | | `ValueError` | If the value is not a FileStorage instance. |

Source code in `src/flask_x_openapi_schema/models/file_models.py`

```python
@field_validator("file")
@classmethod
def validate_file(cls, v: Any) -> FileStorage:
    """Validate that the file is a FileStorage instance.

    Args:
        v: The value to validate.

    Returns:
        FileStorage: The validated FileStorage instance.

    Raises:
        ValueError: If the value is not a FileStorage instance.

    """
    if not isinstance(v, FileStorage):
        msg = "Not a valid file upload"
        raise ValueError(msg)
    return v

```

#### `ImageField`

Bases: `FileField`

Field for image file uploads in OpenAPI schema.

Source code in `src/flask_x_openapi_schema/models/file_models.py`

```python
class ImageField(FileField):
    """Field for image file uploads in OpenAPI schema."""

```

#### `ImageUploadModel`

Bases: `FileUploadModel`

Model for image file uploads with validation.

This model extends FileUploadModel to provide specific validation for image files. It validates file extensions and optionally checks file size.

Attributes:

| Name | Type | Description | | --- | --- | --- | | `file` | `FileStorage` | The uploaded image file. | | `allowed_extensions` | `list[str]` | List of allowed file extensions. | | `max_size` | `int | None` | Maximum file size in bytes. |

Examples:

```pycon
>>> from flask_x_openapi_schema.models.file_models import ImageUploadModel
>>> # Example usage in a Flask route
>>> # @openapi_metadata(summary="Upload an image")
>>> # def post(self, _x_file: ImageUploadModel):
>>> #     return {"filename": _x_file.file.filename}

```

Source code in `src/flask_x_openapi_schema/models/file_models.py`

```python
class ImageUploadModel(FileUploadModel):
    """Model for image file uploads with validation.

    This model extends FileUploadModel to provide specific validation for image files.
    It validates file extensions and optionally checks file size.

    Attributes:
        file: The uploaded image file.
        allowed_extensions: List of allowed file extensions.
        max_size: Maximum file size in bytes.

    Examples:
        >>> from flask_x_openapi_schema.models.file_models import ImageUploadModel
        >>> # Example usage in a Flask route
        >>> # @openapi_metadata(summary="Upload an image")
        >>> # def post(self, _x_file: ImageUploadModel):
        >>> #     return {"filename": _x_file.file.filename}

    """

    file: FileStorage = Field(..., description="The uploaded image file")
    allowed_extensions: list[str] = Field(
        default=["jpg", "jpeg", "png", "gif", "webp", "svg"],
        description="Allowed file extensions",
    )
    max_size: int | None = Field(default=None, description="Maximum file size in bytes")

    @field_validator("file")
    @classmethod
    def validate_image_file(cls, v: FileStorage, info: pydantic.ValidationInfo) -> FileStorage:
        """Validate that the file is an image with allowed extension and size.

        Args:
            v: The file to validate.
            info: Validation context information.

        Returns:
            FileStorage: The validated file.

        Raises:
            ValueError: If the file is invalid, has a disallowed extension, or exceeds the maximum size.

        """
        values = info.data

        if not v or not v.filename:
            msg = "No file provided"
            raise ValueError(msg)

        allowed_extensions = values.get("allowed_extensions", ["jpg", "jpeg", "png", "gif", "webp", "svg"])
        if "." in v.filename:
            ext = v.filename.rsplit(".", 1)[1].lower()
            if ext not in allowed_extensions:
                msg = f"File extension '{ext}' not allowed. Allowed extensions: {', '.join(allowed_extensions)}"
                raise ValueError(
                    msg,
                )

        max_size = values.get("max_size")
        if max_size is not None:
            v.seek(0, 2)
            size = v.tell()
            v.seek(0)

            if size > max_size:
                msg = f"File size ({size} bytes) exceeds maximum allowed size ({max_size} bytes)"
                raise ValueError(msg)

        return v

```

##### `validate_image_file(v, info)`

Validate that the file is an image with allowed extension and size.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `v` | `FileStorage` | The file to validate. | *required* | | `info` | `ValidationInfo` | Validation context information. | *required* |

Returns:

| Name | Type | Description | | --- | --- | --- | | `FileStorage` | `FileStorage` | The validated file. |

Raises:

| Type | Description | | --- | --- | | `ValueError` | If the file is invalid, has a disallowed extension, or exceeds the maximum size. |

Source code in `src/flask_x_openapi_schema/models/file_models.py`

```python
@field_validator("file")
@classmethod
def validate_image_file(cls, v: FileStorage, info: pydantic.ValidationInfo) -> FileStorage:
    """Validate that the file is an image with allowed extension and size.

    Args:
        v: The file to validate.
        info: Validation context information.

    Returns:
        FileStorage: The validated file.

    Raises:
        ValueError: If the file is invalid, has a disallowed extension, or exceeds the maximum size.

    """
    values = info.data

    if not v or not v.filename:
        msg = "No file provided"
        raise ValueError(msg)

    allowed_extensions = values.get("allowed_extensions", ["jpg", "jpeg", "png", "gif", "webp", "svg"])
    if "." in v.filename:
        ext = v.filename.rsplit(".", 1)[1].lower()
        if ext not in allowed_extensions:
            msg = f"File extension '{ext}' not allowed. Allowed extensions: {', '.join(allowed_extensions)}"
            raise ValueError(
                msg,
            )

    max_size = values.get("max_size")
    if max_size is not None:
        v.seek(0, 2)
        size = v.tell()
        v.seek(0)

        if size > max_size:
            msg = f"File size ({size} bytes) exceeds maximum allowed size ({max_size} bytes)"
            raise ValueError(msg)

    return v

```

#### `MultipleFileUploadModel`

Bases: `BaseModel`

Model for multiple file uploads.

This model allows uploading multiple files at once and validates that all files are valid FileStorage instances.

Attributes:

| Name | Type | Description | | --- | --- | --- | | `files` | `list[FileStorage]` | List of uploaded files. |

Examples:

```pycon
>>> from flask_x_openapi_schema.models.file_models import MultipleFileUploadModel
>>> # Example usage in a Flask route
>>> # @openapi_metadata(summary="Upload multiple files")
>>> # def post(self, _x_file: MultipleFileUploadModel):
>>> #     return {"filenames": [f.filename for f in _x_file.files]}

```

Source code in `src/flask_x_openapi_schema/models/file_models.py`

```python
class MultipleFileUploadModel(BaseModel):
    """Model for multiple file uploads.

    This model allows uploading multiple files at once and validates that all files
    are valid FileStorage instances.

    Attributes:
        files: List of uploaded files.

    Examples:
        >>> from flask_x_openapi_schema.models.file_models import MultipleFileUploadModel
        >>> # Example usage in a Flask route
        >>> # @openapi_metadata(summary="Upload multiple files")
        >>> # def post(self, _x_file: MultipleFileUploadModel):
        >>> #     return {"filenames": [f.filename for f in _x_file.files]}

    """

    files: list[FileStorage] = Field(..., description="The uploaded files")

    model_config = {"arbitrary_types_allowed": True}

    @field_validator("files")
    @classmethod
    def validate_files(cls, v: list[Any]) -> list[FileStorage]:
        """Validate that all files are FileStorage instances.

        Args:
            v: List of values to validate.

        Returns:
            list[FileStorage]: The validated list of FileStorage instances.

        Raises:
            ValueError: If the list is empty or contains non-FileStorage objects.

        """
        if not v:
            msg = "No files provided"
            raise ValueError(msg)

        for file in v:
            if not isinstance(file, FileStorage):
                msg = "Not a valid file upload"
                raise ValueError(msg)

        return v

```

##### `validate_files(v)`

Validate that all files are FileStorage instances.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `v` | `list[Any]` | List of values to validate. | *required* |

Returns:

| Type | Description | | --- | --- | | `list[FileStorage]` | list\[FileStorage\]: The validated list of FileStorage instances. |

Raises:

| Type | Description | | --- | --- | | `ValueError` | If the list is empty or contains non-FileStorage objects. |

Source code in `src/flask_x_openapi_schema/models/file_models.py`

```python
@field_validator("files")
@classmethod
def validate_files(cls, v: list[Any]) -> list[FileStorage]:
    """Validate that all files are FileStorage instances.

    Args:
        v: List of values to validate.

    Returns:
        list[FileStorage]: The validated list of FileStorage instances.

    Raises:
        ValueError: If the list is empty or contains non-FileStorage objects.

    """
    if not v:
        msg = "No files provided"
        raise ValueError(msg)

    for file in v:
        if not isinstance(file, FileStorage):
            msg = "Not a valid file upload"
            raise ValueError(msg)

    return v

```

#### `PDFField`

Bases: `FileField`

Field for PDF file uploads in OpenAPI schema.

Source code in `src/flask_x_openapi_schema/models/file_models.py`

```python
class PDFField(FileField):
    """Field for PDF file uploads in OpenAPI schema."""

```

#### `TextField`

Bases: `FileField`

Field for text file uploads in OpenAPI schema.

Source code in `src/flask_x_openapi_schema/models/file_models.py`

```python
class TextField(FileField):
    """Field for text file uploads in OpenAPI schema."""

```

#### `VideoField`

Bases: `FileField`

Field for video file uploads in OpenAPI schema.

Source code in `src/flask_x_openapi_schema/models/file_models.py`

```python
class VideoField(FileField):
    """Field for video file uploads in OpenAPI schema."""

```

## Response Models

Response models for OpenAPI schema generation.

This module provides models for defining OpenAPI responses in a structured way. It includes classes and helper functions to create and manage response definitions for OpenAPI schema generation.

#### `OpenAPIMetaResponse`

Bases: `BaseModel`

Container for OpenAPI response definitions.

This class allows defining multiple responses for different status codes. It is used to define all possible responses for an API endpoint in the OpenAPI schema.

Attributes:

| Name | Type | Description | | --- | --- | --- | | `responses` | `dict[str, OpenAPIMetaResponseItem]` | Map of status codes to response definitions. | | `default_error_response` | `type[BaseErrorResponse]` | Default error response class for validation errors. Must be a subclass of BaseErrorResponse. |

Examples:

```pycon
>>> from flask_x_openapi_schema.models.responses import OpenAPIMetaResponse, OpenAPIMetaResponseItem
>>> from pydantic import BaseModel
>>>
>>> class UserResponse(BaseModel):
...     id: str
...     name: str
>>> class ErrorResponse(BaseModel):
...     error: str
...     code: int
>>> responses = OpenAPIMetaResponse(
...     responses={
...         "200": OpenAPIMetaResponseItem(
...             model=UserResponse, description="User details retrieved successfully"
...         ),
...         "404": OpenAPIMetaResponseItem(model=ErrorResponse, description="User not found"),
...     }
... )

```

Source code in `src/flask_x_openapi_schema/models/responses.py`

```python
class OpenAPIMetaResponse(BaseModel):
    """Container for OpenAPI response definitions.

    This class allows defining multiple responses for different status codes.
    It is used to define all possible responses for an API endpoint in the OpenAPI schema.

    Attributes:
        responses: Map of status codes to response definitions.
        default_error_response: Default error response class for validation errors.
            Must be a subclass of BaseErrorResponse.

    Examples:
        >>> from flask_x_openapi_schema.models.responses import OpenAPIMetaResponse, OpenAPIMetaResponseItem
        >>> from pydantic import BaseModel
        >>>
        >>> class UserResponse(BaseModel):
        ...     id: str
        ...     name: str
        >>> class ErrorResponse(BaseModel):
        ...     error: str
        ...     code: int
        >>> responses = OpenAPIMetaResponse(
        ...     responses={
        ...         "200": OpenAPIMetaResponseItem(
        ...             model=UserResponse, description="User details retrieved successfully"
        ...         ),
        ...         "404": OpenAPIMetaResponseItem(model=ErrorResponse, description="User not found"),
        ...     }
        ... )

    """

    default_error_response: type[BaseErrorResponse] = Field(
        default=BaseErrorResponse,
        description="Default error response class for validation errors",
    )

    responses: dict[str, OpenAPIMetaResponseItem] = Field(
        ...,
        description="Map of status codes to response definitions",
    )

    def to_openapi_dict(self) -> dict[str, Any]:
        """Convert the response container to an OpenAPI responses object.

        Returns:
            dict: An OpenAPI responses object dictionary.

        """
        result = {}
        for status_code, response_item in self.responses.items():
            result[status_code] = response_item.to_openapi_dict()
        return result

```

##### `to_openapi_dict()`

Convert the response container to an OpenAPI responses object.

Returns:

| Name | Type | Description | | --- | --- | --- | | `dict` | `dict[str, Any]` | An OpenAPI responses object dictionary. |

Source code in `src/flask_x_openapi_schema/models/responses.py`

```python
def to_openapi_dict(self) -> dict[str, Any]:
    """Convert the response container to an OpenAPI responses object.

    Returns:
        dict: An OpenAPI responses object dictionary.

    """
    result = {}
    for status_code, response_item in self.responses.items():
        result[status_code] = response_item.to_openapi_dict()
    return result

```

#### `OpenAPIMetaResponseItem`

Bases: `BaseModel`

Represents a single response item in an OpenAPI specification.

This class allows defining a response with either a Pydantic model or a simple message. It is used to define the response for a specific status code in the OpenAPI schema.

Attributes:

| Name | Type | Description | | --- | --- | --- | | `model` | `type[BaseModel] | None` | Pydantic model for the response. | | `description` | `str` | Response description. | | `content_type` | `str` | Response content type. | | `headers` | `dict[str, Any] | None` | Response headers. | | `examples` | `dict[str, Any] | None` | Response examples. | | `msg` | `str | None` | Simple message for responses without a model. |

Examples:

```pycon
>>> from flask_x_openapi_schema.models.responses import OpenAPIMetaResponseItem
>>> from pydantic import BaseModel
>>>
>>> class UserResponse(BaseModel):
...     id: str
...     name: str
>>> response_item = OpenAPIMetaResponseItem(
...     model=UserResponse, description="User details", content_type="application/json"
... )

```

Source code in `src/flask_x_openapi_schema/models/responses.py`

```python
class OpenAPIMetaResponseItem(BaseModel):
    """Represents a single response item in an OpenAPI specification.

    This class allows defining a response with either a Pydantic model or a simple message.
    It is used to define the response for a specific status code in the OpenAPI schema.

    Attributes:
        model: Pydantic model for the response.
        description: Response description.
        content_type: Response content type.
        headers: Response headers.
        examples: Response examples.
        msg: Simple message for responses without a model.

    Examples:
        >>> from flask_x_openapi_schema.models.responses import OpenAPIMetaResponseItem
        >>> from pydantic import BaseModel
        >>>
        >>> class UserResponse(BaseModel):
        ...     id: str
        ...     name: str
        >>> response_item = OpenAPIMetaResponseItem(
        ...     model=UserResponse, description="User details", content_type="application/json"
        ... )

    """

    model: type[BaseModel] | None = Field(None, description="Pydantic model for the response")
    description: str = Field("Successful response", description="Response description")
    content_type: str = Field("application/json", description="Response content type")
    headers: dict[str, Any] | None = Field(None, description="Response headers")
    examples: dict[str, Any] | None = Field(None, description="Response examples")
    msg: str | None = Field(None, description="Simple message for responses without a model")

    def to_openapi_dict(self) -> dict[str, Any]:
        """Convert the response item to an OpenAPI response object.

        Returns:
            dict: An OpenAPI response object dictionary.

        """
        response = {"description": self.description}

        if self.model:
            response["content"] = {
                self.content_type: {"schema": {"$ref": f"#/components/schemas/{self.model.__name__}"}},
            }

            if self.examples:
                response["content"][self.content_type]["examples"] = self.examples

        if self.headers:
            response["headers"] = self.headers

        return response

```

##### `to_openapi_dict()`

Convert the response item to an OpenAPI response object.

Returns:

| Name | Type | Description | | --- | --- | --- | | `dict` | `dict[str, Any]` | An OpenAPI response object dictionary. |

Source code in `src/flask_x_openapi_schema/models/responses.py`

```python
def to_openapi_dict(self) -> dict[str, Any]:
    """Convert the response item to an OpenAPI response object.

    Returns:
        dict: An OpenAPI response object dictionary.

    """
    response = {"description": self.description}

    if self.model:
        response["content"] = {
            self.content_type: {"schema": {"$ref": f"#/components/schemas/{self.model.__name__}"}},
        }

        if self.examples:
            response["content"][self.content_type]["examples"] = self.examples

    if self.headers:
        response["headers"] = self.headers

    return response

```

#### `create_response(model=None, description='Successful response', status_code=200, content_type='application/json', headers=None, examples=None, msg=None)`

Create a response definition for use with OpenAPIMetaResponse.

This is a helper function to create a response definition for a specific status code. It returns a dictionary that can be used to build an OpenAPIMetaResponse object.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `model` | `type[BaseModel] | None` | Pydantic model for the response. | `None` | | `description` | `str` | Response description. | `'Successful response'` | | `status_code` | `int | str` | HTTP status code. | `200` | | `content_type` | `str` | Response content type. | `'application/json'` | | `headers` | `dict[str, Any] | None` | Response headers. | `None` | | `examples` | `dict[str, Any] | None` | Response examples. | `None` | | `msg` | `str | None` | Simple message for responses without a model. | `None` |

Returns:

| Name | Type | Description | | --- | --- | --- | | `dict` | `dict[str, OpenAPIMetaResponseItem]` | A dictionary with the status code as key and response item as value. |

Examples:

```pycon
>>> from flask_x_openapi_schema.models.responses import create_response, OpenAPIMetaResponse
>>> from pydantic import BaseModel
>>>
>>> class UserResponse(BaseModel):
...     id: str
...     name: str
>>>
>>> user_response = create_response(model=UserResponse, description="User details", status_code=200)
>>>
>>> not_found_response = create_response(msg="User not found", description="User not found", status_code=404)
>>>
>>> responses = OpenAPIMetaResponse(responses={**user_response, **not_found_response})

```

Source code in `src/flask_x_openapi_schema/models/responses.py`

```python
def create_response(
    model: type[BaseModel] | None = None,
    description: str = "Successful response",
    status_code: int | str = 200,
    content_type: str = "application/json",
    headers: dict[str, Any] | None = None,
    examples: dict[str, Any] | None = None,
    msg: str | None = None,
) -> dict[str, OpenAPIMetaResponseItem]:
    """Create a response definition for use with OpenAPIMetaResponse.

    This is a helper function to create a response definition for a specific status code.
    It returns a dictionary that can be used to build an OpenAPIMetaResponse object.

    Args:
        model: Pydantic model for the response.
        description: Response description.
        status_code: HTTP status code.
        content_type: Response content type.
        headers: Response headers.
        examples: Response examples.
        msg: Simple message for responses without a model.

    Returns:
        dict: A dictionary with the status code as key and response item as value.

    Examples:
        >>> from flask_x_openapi_schema.models.responses import create_response, OpenAPIMetaResponse
        >>> from pydantic import BaseModel
        >>>
        >>> class UserResponse(BaseModel):
        ...     id: str
        ...     name: str
        >>>
        >>> user_response = create_response(model=UserResponse, description="User details", status_code=200)
        >>>
        >>> not_found_response = create_response(msg="User not found", description="User not found", status_code=404)
        >>>
        >>> responses = OpenAPIMetaResponse(responses={**user_response, **not_found_response})

    """
    return {
        str(status_code): OpenAPIMetaResponseItem(
            model=model,
            description=description,
            content_type=content_type,
            headers=headers,
            examples=examples,
            msg=msg,
        ),
    }

```

#### `error_response(description, status_code=400, model=None, content_type='application/json', headers=None, examples=None, msg=None)`

Create an error response definition for use with OpenAPIMetaResponse.

This is a convenience function to create an error response with a description.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `description` | `str` | Response description. | *required* | | `status_code` | `int | str` | HTTP status code. | `400` | | `model` | `type[BaseModel] | None` | Optional Pydantic model for the response. | `None` | | `content_type` | `str` | Response content type. | `'application/json'` | | `headers` | `dict[str, Any] | None` | Response headers. | `None` | | `examples` | `dict[str, Any] | None` | Response examples. | `None` | | `msg` | `str | None` | Simple message for responses without a model. | `None` |

Returns:

| Name | Type | Description | | --- | --- | --- | | `dict` | `dict[str, OpenAPIMetaResponseItem]` | A dictionary with the status code as key and response item as value. |

Source code in `src/flask_x_openapi_schema/models/responses.py`

```python
def error_response(
    description: str,
    status_code: int | str = 400,
    model: type[BaseModel] | None = None,
    content_type: str = "application/json",
    headers: dict[str, Any] | None = None,
    examples: dict[str, Any] | None = None,
    msg: str | None = None,
) -> dict[str, OpenAPIMetaResponseItem]:
    """Create an error response definition for use with OpenAPIMetaResponse.

    This is a convenience function to create an error response with a description.

    Args:
        description: Response description.
        status_code: HTTP status code.
        model: Optional Pydantic model for the response.
        content_type: Response content type.
        headers: Response headers.
        examples: Response examples.
        msg: Simple message for responses without a model.

    Returns:
        dict: A dictionary with the status code as key and response item as value.

    """
    return create_response(
        model=model,
        description=description,
        status_code=status_code,
        content_type=content_type,
        headers=headers,
        examples=examples,
        msg=msg,
    )

```

#### `success_response(model, description='Successful response', status_code=200, content_type='application/json', headers=None, examples=None)`

Create a success response definition for use with OpenAPIMetaResponse.

This is a convenience function to create a success response with a model.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `model` | `type[BaseModel]` | Pydantic model for the response. | *required* | | `description` | `str` | Response description. | `'Successful response'` | | `status_code` | `int | str` | HTTP status code. | `200` | | `content_type` | `str` | Response content type. | `'application/json'` | | `headers` | `dict[str, Any] | None` | Response headers. | `None` | | `examples` | `dict[str, Any] | None` | Response examples. | `None` |

Returns:

| Name | Type | Description | | --- | --- | --- | | `dict` | `dict[str, OpenAPIMetaResponseItem]` | A dictionary with the status code as key and response item as value. |

Source code in `src/flask_x_openapi_schema/models/responses.py`

```python
def success_response(
    model: type[BaseModel],
    description: str = "Successful response",
    status_code: int | str = 200,
    content_type: str = "application/json",
    headers: dict[str, Any] | None = None,
    examples: dict[str, Any] | None = None,
) -> dict[str, OpenAPIMetaResponseItem]:
    """Create a success response definition for use with OpenAPIMetaResponse.

    This is a convenience function to create a success response with a model.

    Args:
        model: Pydantic model for the response.
        description: Response description.
        status_code: HTTP status code.
        content_type: Response content type.
        headers: Response headers.
        examples: Response examples.

    Returns:
        dict: A dictionary with the status code as key and response item as value.

    """
    return create_response(
        model=model,
        description=description,
        status_code=status_code,
        content_type=content_type,
        headers=headers,
        examples=examples,
    )

```
