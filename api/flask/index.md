# Flask Integration

This section provides documentation for the Flask-specific components of Flask-X-OpenAPI-Schema.

## Flask Module

Flask-specific implementations for OpenAPI schema generation.

#### `OpenAPIMethodViewMixin`

A mixin class for Flask.MethodView to collect OpenAPI metadata.

This mixin class adds OpenAPI schema generation capabilities to Flask's MethodView. It provides a method to register the view to a blueprint while collecting metadata for OpenAPI schema generation.

Examples:

```pycon
>>> from flask import Blueprint
>>> from flask.views import MethodView
>>> from flask_x_openapi_schema.x.flask import OpenAPIMethodViewMixin, openapi_metadata
>>> from pydantic import BaseModel, Field
>>>
>>> class ItemResponse(BaseModel):
...     id: str = Field(..., description="Item ID")
...     name: str = Field(..., description="Item name")
>>>
>>> class ItemView(OpenAPIMethodViewMixin, MethodView):
...     @openapi_metadata(summary="Get an item")
...     def get(self, item_id: str):
...         return {"id": item_id, "name": "Example Item"}
>>>
>>> bp = Blueprint("items", __name__)
>>> # Register the view to the blueprint
>>> _ = ItemView.register_to_blueprint(bp, "/items/<item_id>")

```

Source code in `src/flask_x_openapi_schema/x/flask/views.py`

```python
class OpenAPIMethodViewMixin:
    """A mixin class for Flask.MethodView to collect OpenAPI metadata.

    This mixin class adds OpenAPI schema generation capabilities to Flask's MethodView.
    It provides a method to register the view to a blueprint while collecting metadata
    for OpenAPI schema generation.

    Examples:
        >>> from flask import Blueprint
        >>> from flask.views import MethodView
        >>> from flask_x_openapi_schema.x.flask import OpenAPIMethodViewMixin, openapi_metadata
        >>> from pydantic import BaseModel, Field
        >>>
        >>> class ItemResponse(BaseModel):
        ...     id: str = Field(..., description="Item ID")
        ...     name: str = Field(..., description="Item name")
        >>>
        >>> class ItemView(OpenAPIMethodViewMixin, MethodView):
        ...     @openapi_metadata(summary="Get an item")
        ...     def get(self, item_id: str):
        ...         return {"id": item_id, "name": "Example Item"}
        >>>
        >>> bp = Blueprint("items", __name__)
        >>> # Register the view to the blueprint
        >>> _ = ItemView.register_to_blueprint(bp, "/items/<item_id>")

    """

    @classmethod
    def register_to_blueprint(cls, blueprint: Any, url: str, endpoint: str | None = None, **kwargs: Any) -> Any:
        """Register the MethodView to a blueprint and collect OpenAPI metadata.

        This method registers the view to a blueprint and stores metadata for
        OpenAPI schema generation.

        Args:
            blueprint: The Flask blueprint to register to
            url: The URL rule to register
            endpoint: The endpoint name (defaults to the class name)
            **kwargs: Additional arguments to pass to add_url_rule

        Returns:
            Any: The view function

        Examples:
            >>> from flask import Blueprint
            >>> from flask.views import MethodView
            >>> from flask_x_openapi_schema.x.flask import OpenAPIMethodViewMixin
            >>> class ItemView(OpenAPIMethodViewMixin, MethodView):
            ...     def get(self, item_id: str):
            ...         return {"id": item_id, "name": "Example Item"}
            >>> bp = Blueprint("items", __name__)
            >>> # Register the view to the blueprint
            >>> _ = ItemView.register_to_blueprint(bp, "/items/<item_id>")

        """
        view_func = cls.as_view(endpoint or cls.__name__.lower())
        blueprint.add_url_rule(url, view_func=view_func, **kwargs)

        if not hasattr(blueprint, "_methodview_openapi_resources"):
            blueprint._methodview_openapi_resources = []

        blueprint._methodview_openapi_resources.append((cls, url))

        return view_func

```

##### `register_to_blueprint(blueprint, url, endpoint=None, **kwargs)`

Register the MethodView to a blueprint and collect OpenAPI metadata.

This method registers the view to a blueprint and stores metadata for OpenAPI schema generation.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `blueprint` | `Any` | The Flask blueprint to register to | *required* | | `url` | `str` | The URL rule to register | *required* | | `endpoint` | `str | None` | The endpoint name (defaults to the class name) | `None` | | `**kwargs` | `Any` | Additional arguments to pass to add_url_rule | `{}` |

Returns:

| Name | Type | Description | | --- | --- | --- | | `Any` | `Any` | The view function |

Examples:

```pycon
>>> from flask import Blueprint
>>> from flask.views import MethodView
>>> from flask_x_openapi_schema.x.flask import OpenAPIMethodViewMixin
>>> class ItemView(OpenAPIMethodViewMixin, MethodView):
...     def get(self, item_id: str):
...         return {"id": item_id, "name": "Example Item"}
>>> bp = Blueprint("items", __name__)
>>> # Register the view to the blueprint
>>> _ = ItemView.register_to_blueprint(bp, "/items/<item_id>")

```

Source code in `src/flask_x_openapi_schema/x/flask/views.py`

```python
@classmethod
def register_to_blueprint(cls, blueprint: Any, url: str, endpoint: str | None = None, **kwargs: Any) -> Any:
    """Register the MethodView to a blueprint and collect OpenAPI metadata.

    This method registers the view to a blueprint and stores metadata for
    OpenAPI schema generation.

    Args:
        blueprint: The Flask blueprint to register to
        url: The URL rule to register
        endpoint: The endpoint name (defaults to the class name)
        **kwargs: Additional arguments to pass to add_url_rule

    Returns:
        Any: The view function

    Examples:
        >>> from flask import Blueprint
        >>> from flask.views import MethodView
        >>> from flask_x_openapi_schema.x.flask import OpenAPIMethodViewMixin
        >>> class ItemView(OpenAPIMethodViewMixin, MethodView):
        ...     def get(self, item_id: str):
        ...         return {"id": item_id, "name": "Example Item"}
        >>> bp = Blueprint("items", __name__)
        >>> # Register the view to the blueprint
        >>> _ = ItemView.register_to_blueprint(bp, "/items/<item_id>")

    """
    view_func = cls.as_view(endpoint or cls.__name__.lower())
    blueprint.add_url_rule(url, view_func=view_func, **kwargs)

    if not hasattr(blueprint, "_methodview_openapi_resources"):
        blueprint._methodview_openapi_resources = []

    blueprint._methodview_openapi_resources.append((cls, url))

    return view_func

```

#### `openapi_metadata(*, summary=None, description=None, tags=None, operation_id=None, responses=None, deprecated=False, security=None, external_docs=None, language=None, prefix_config=None, content_type=None, request_content_types=None, response_content_types=None, content_type_resolver=None)`

Decorator to add OpenAPI metadata to a Flask MethodView endpoint.

This decorator adds OpenAPI metadata to a Flask MethodView endpoint and handles parameter binding for request data. It automatically binds request body, query parameters, path parameters, and file uploads to function parameters based on their type annotations and parameter name prefixes.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `summary` | `str | I18nStr | None` | A short summary of what the operation does | `None` | | `description` | `str | I18nStr | None` | A verbose explanation of the operation behavior | `None` | | `tags` | `list[str] | None` | A list of tags for API documentation control | `None` | | `operation_id` | `str | None` | Unique string used to identify the operation | `None` | | `responses` | `OpenAPIMetaResponse | None` | The responses the API can return | `None` | | `deprecated` | `bool` | Declares this operation to be deprecated | `False` | | `security` | `list[dict[str, list[str]]] | None` | A declaration of which security mechanisms can be used for this operation | `None` | | `external_docs` | `dict[str, str] | None` | Additional external documentation | `None` | | `language` | `str | None` | Language code to use for I18nString values (default: current language) | `None` | | `prefix_config` | `ConventionalPrefixConfig | None` | Configuration object for parameter prefixes | `None` | | `content_type` | `str | None` | Custom content type for request body. If None, will be auto-detected. | `None` | | `request_content_types` | `RequestContentTypes | None` | Multiple content types for request body. | `None` | | `response_content_types` | `ResponseContentTypes | None` | Multiple content types for response body. | `None` | | `content_type_resolver` | `Callable[[Any], str] | None` | Function to determine content type based on request. | `None` |

Returns:

| Type | Description | | --- | --- | | `Callable[[F], F]` | The decorated function with OpenAPI metadata attached |

Examples:

```pycon
>>> from flask.views import MethodView
>>> from flask_x_openapi_schema.x.flask import openapi_metadata
>>> from flask_x_openapi_schema import OpenAPIMetaResponse, OpenAPIMetaResponseItem
>>> from pydantic import BaseModel, Field
>>>
>>> class ItemRequest(BaseModel):
...     name: str = Field(..., description="Item name")
...     price: float = Field(..., description="Item price")
>>>
>>> class ItemResponse(BaseModel):
...     id: str = Field(..., description="Item ID")
...     name: str = Field(..., description="Item name")
...     price: float = Field(..., description="Item price")
>>>
>>> class ItemView(MethodView):
...     @openapi_metadata(
...         summary="Create a new item",
...         description="Create a new item with the provided information",
...         tags=["items"],
...         operation_id="createItem",
...         responses=OpenAPIMetaResponse(
...             responses={
...                 "201": OpenAPIMetaResponseItem(model=ItemResponse, description="Item created successfully"),
...                 "400": OpenAPIMetaResponseItem(description="Invalid request data"),
...             }
...         ),
...     )
...     def post(self, _x_body: ItemRequest):
...         item = {"id": "123", "name": _x_body.name, "price": _x_body.price}
...         return item, 201

```

Source code in `src/flask_x_openapi_schema/x/flask/decorators.py`

```python
def openapi_metadata(
    *,
    summary: str | I18nStr | None = None,
    description: str | I18nStr | None = None,
    tags: list[str] | None = None,
    operation_id: str | None = None,
    responses: OpenAPIMetaResponse | None = None,
    deprecated: bool = False,
    security: list[dict[str, list[str]]] | None = None,
    external_docs: dict[str, str] | None = None,
    language: str | None = None,
    prefix_config: ConventionalPrefixConfig | None = None,
    content_type: str | None = None,
    request_content_types: RequestContentTypes | None = None,
    response_content_types: ResponseContentTypes | None = None,
    content_type_resolver: Callable[[Any], str] | None = None,
) -> Callable[[F], F]:
    """Decorator to add OpenAPI metadata to a Flask MethodView endpoint.

    This decorator adds OpenAPI metadata to a Flask MethodView endpoint and handles
    parameter binding for request data. It automatically binds request body, query parameters,
    path parameters, and file uploads to function parameters based on their type annotations
    and parameter name prefixes.

    Args:
        summary: A short summary of what the operation does
        description: A verbose explanation of the operation behavior
        tags: A list of tags for API documentation control
        operation_id: Unique string used to identify the operation
        responses: The responses the API can return
        deprecated: Declares this operation to be deprecated
        security: A declaration of which security mechanisms can be used for this operation
        external_docs: Additional external documentation
        language: Language code to use for I18nString values (default: current language)
        prefix_config: Configuration object for parameter prefixes
        content_type: Custom content type for request body. If None, will be auto-detected.
        request_content_types: Multiple content types for request body.
        response_content_types: Multiple content types for response body.
        content_type_resolver: Function to determine content type based on request.


    Returns:
        The decorated function with OpenAPI metadata attached

    Examples:
        >>> from flask.views import MethodView
        >>> from flask_x_openapi_schema.x.flask import openapi_metadata
        >>> from flask_x_openapi_schema import OpenAPIMetaResponse, OpenAPIMetaResponseItem
        >>> from pydantic import BaseModel, Field
        >>>
        >>> class ItemRequest(BaseModel):
        ...     name: str = Field(..., description="Item name")
        ...     price: float = Field(..., description="Item price")
        >>>
        >>> class ItemResponse(BaseModel):
        ...     id: str = Field(..., description="Item ID")
        ...     name: str = Field(..., description="Item name")
        ...     price: float = Field(..., description="Item price")
        >>>
        >>> class ItemView(MethodView):
        ...     @openapi_metadata(
        ...         summary="Create a new item",
        ...         description="Create a new item with the provided information",
        ...         tags=["items"],
        ...         operation_id="createItem",
        ...         responses=OpenAPIMetaResponse(
        ...             responses={
        ...                 "201": OpenAPIMetaResponseItem(model=ItemResponse, description="Item created successfully"),
        ...                 "400": OpenAPIMetaResponseItem(description="Invalid request data"),
        ...             }
        ...         ),
        ...     )
        ...     def post(self, _x_body: ItemRequest):
        ...         item = {"id": "123", "name": _x_body.name, "price": _x_body.price}
        ...         return item, 201

    """
    return FlaskOpenAPIDecorator(
        summary=summary,
        description=description,
        tags=tags,
        operation_id=operation_id,
        responses=responses,
        deprecated=deprecated,
        security=security,
        external_docs=external_docs,
        language=language,
        prefix_config=prefix_config,
        content_type=content_type,
        request_content_types=request_content_types,
        response_content_types=response_content_types,
        content_type_resolver=content_type_resolver,
    )

```

## Decorators

Decorators for adding OpenAPI metadata to Flask MethodView endpoints.

This module provides decorators that can be used to add OpenAPI metadata to Flask MethodView endpoints. The decorators handle parameter binding for request data, including request body, query parameters, path parameters, and file uploads.

#### `FlaskOpenAPIDecorator`

Bases: `DecoratorBase`

OpenAPI metadata decorator for Flask MethodView.

This class implements a decorator that adds OpenAPI metadata to Flask MethodView endpoints and handles parameter binding for request data.

Source code in `src/flask_x_openapi_schema/x/flask/decorators.py`

```python
class FlaskOpenAPIDecorator(DecoratorBase):
    """OpenAPI metadata decorator for Flask MethodView.

    This class implements a decorator that adds OpenAPI metadata to Flask MethodView
    endpoints and handles parameter binding for request data.
    """

    def __init__(
        self,
        summary: str | I18nStr | None = None,
        description: str | I18nStr | None = None,
        tags: list[str] | None = None,
        operation_id: str | None = None,
        responses: OpenAPIMetaResponse | None = None,
        deprecated: bool = False,
        security: list[dict[str, list[str]]] | None = None,
        external_docs: dict[str, str] | None = None,
        language: str | None = None,
        prefix_config: ConventionalPrefixConfig | None = None,
        content_type: str | None = None,
        request_content_types: RequestContentTypes | None = None,
        response_content_types: ResponseContentTypes | None = None,
        content_type_resolver: Callable[[Any], str] | None = None,
    ) -> None:
        """Initialize the decorator with OpenAPI metadata parameters.

        Args:
            summary: A short summary of what the operation does
            description: A verbose explanation of the operation behavior
            tags: A list of tags for API documentation control
            operation_id: Unique string used to identify the operation
            responses: The responses the API can return
            deprecated: Declares this operation to be deprecated
            security: A declaration of which security mechanisms can be used for this operation
            external_docs: Additional external documentation
            language: Language code to use for I18nString values
            prefix_config: Configuration object for parameter prefixes
            content_type: Custom content type for request body. If None, will be auto-detected.
            request_content_types: Multiple content types for request body.
            response_content_types: Multiple content types for response body.
            content_type_resolver: Function to determine content type based on request.

        """
        super().__init__(
            summary=summary,
            description=description,
            tags=tags,
            operation_id=operation_id,
            responses=responses,
            deprecated=deprecated,
            security=security,
            external_docs=external_docs,
            language=language,
            prefix_config=prefix_config,
            content_type=content_type,
            request_content_types=request_content_types,
            response_content_types=response_content_types,
            content_type_resolver=content_type_resolver,
        )
        self.framework = "flask"
        self.base_decorator = None

    def __call__(self, func: Callable) -> Callable:
        """Apply the decorator to the function.

        Args:
            func: The function to decorate

        Returns:
            The decorated function

        """
        if self.base_decorator is None:
            self.base_decorator = OpenAPIDecoratorBase(
                summary=self.summary,
                description=self.description,
                tags=self.tags,
                operation_id=self.operation_id,
                responses=self.responses,
                deprecated=self.deprecated,
                security=self.security,
                external_docs=self.external_docs,
                language=self.language,
                prefix_config=self.prefix_config,
                framework=self.framework,
                content_type=self.content_type,
                request_content_types=self.request_content_types,
                response_content_types=self.response_content_types,
                content_type_resolver=self.content_type_resolver,
            )
        return self.base_decorator(func)

    def extract_parameters_from_models(
        self,
        query_model: type[BaseModel] | None,
        path_params: list[str] | None,
    ) -> list[dict[str, Any]]:
        """Extract OpenAPI parameters from models.

        Args:
            query_model: The query parameter model
            path_params: List of path parameter names

        Returns:
            List of OpenAPI parameter objects

        """
        parameters = [
            {
                "name": param,
                "in": "path",
                "required": True,
                "schema": {"type": "string"},
            }
            for param in path_params
        ]

        if query_model:
            schema = query_model.model_json_schema()
            properties = schema.get("properties", {})
            required = schema.get("required", [])

            for field_name, field_schema in properties.items():
                param = {
                    "name": field_name,
                    "in": "query",
                    "required": field_name in required,
                    "schema": field_schema,
                }

                if "description" in field_schema:
                    param["description"] = field_schema["description"]

                parameters.append(param)

        return parameters

    def process_request_body(self, param_name: str, model: type[BaseModel], kwargs: dict[str, Any]) -> dict[str, Any]:
        """Process request body parameters for Flask.

        Args:
            param_name: The parameter name to bind the model instance to
            model: The Pydantic model class to use for validation
            kwargs: The keyword arguments to update

        Returns:
            Updated kwargs dictionary with the model instance

        """
        from flask import request

        from flask_x_openapi_schema.models.file_models import FileField

        if hasattr(model, "model_fields") and hasattr(request, "files") and request.files:
            has_file_fields = False
            for field_info in model.model_fields.values():
                field_type = field_info.annotation

                if isinstance(field_type, type) and issubclass(field_type, FileField):
                    has_file_fields = True
                    break

                origin = getattr(field_type, "__origin__", None)
                if origin is list or origin is list:
                    args = getattr(field_type, "__args__", [])
                    if args and isinstance(args[0], type) and issubclass(args[0], FileField):
                        has_file_fields = True
                        break

            if has_file_fields:
                model_data = dict(request.form.items())
                for field_name in model.model_fields:
                    if field_name in request.files:
                        model_data[field_name] = request.files[field_name]

                if model_data:
                    try:
                        model_instance = model(**model_data)
                        kwargs[param_name] = model_instance
                    except Exception as e:
                        logger = get_logger(__name__)
                        logger.exception(
                            f"Failed to create model instance with mock files for {model.__name__}", exc_info=e
                        )
                    else:
                        return kwargs

        return super().process_request_body(param_name, model, kwargs)

    def process_query_params(self, param_name: str, model: type[BaseModel], kwargs: dict[str, Any]) -> dict[str, Any]:
        """Process query parameters for Flask.

        Args:
            param_name: The parameter name to bind the model instance to
            model: The Pydantic model class to use for validation
            kwargs: The keyword arguments to update

        Returns:
            Updated kwargs dictionary with the model instance

        """
        query_data = {}
        model_fields = model.model_fields

        for field_name in model_fields:
            if field_name in request.args:
                query_data[field_name] = request.args.get(field_name)

        model_instance = model(**query_data)

        kwargs[param_name] = model_instance

        return kwargs

    def process_additional_params(self, kwargs: dict[str, Any], param_names: list[str]) -> dict[str, Any]:
        """Process additional framework-specific parameters.

        Args:
            kwargs: The keyword arguments to update
            param_names: List of parameter names that have been processed

        Returns:
            Updated kwargs dictionary

        """
        logger = get_logger(__name__)
        logger.debug(f"Processing additional parameters with kwargs keys: {list(kwargs.keys())}")
        logger.debug(f"Processed parameter names: {param_names}")
        return kwargs

```

##### `__call__(func)`

Apply the decorator to the function.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `func` | `Callable` | The function to decorate | *required* |

Returns:

| Type | Description | | --- | --- | | `Callable` | The decorated function |

Source code in `src/flask_x_openapi_schema/x/flask/decorators.py`

```python
def __call__(self, func: Callable) -> Callable:
    """Apply the decorator to the function.

    Args:
        func: The function to decorate

    Returns:
        The decorated function

    """
    if self.base_decorator is None:
        self.base_decorator = OpenAPIDecoratorBase(
            summary=self.summary,
            description=self.description,
            tags=self.tags,
            operation_id=self.operation_id,
            responses=self.responses,
            deprecated=self.deprecated,
            security=self.security,
            external_docs=self.external_docs,
            language=self.language,
            prefix_config=self.prefix_config,
            framework=self.framework,
            content_type=self.content_type,
            request_content_types=self.request_content_types,
            response_content_types=self.response_content_types,
            content_type_resolver=self.content_type_resolver,
        )
    return self.base_decorator(func)

```

##### `__init__(summary=None, description=None, tags=None, operation_id=None, responses=None, deprecated=False, security=None, external_docs=None, language=None, prefix_config=None, content_type=None, request_content_types=None, response_content_types=None, content_type_resolver=None)`

Initialize the decorator with OpenAPI metadata parameters.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `summary` | `str | I18nStr | None` | A short summary of what the operation does | `None` | | `description` | `str | I18nStr | None` | A verbose explanation of the operation behavior | `None` | | `tags` | `list[str] | None` | A list of tags for API documentation control | `None` | | `operation_id` | `str | None` | Unique string used to identify the operation | `None` | | `responses` | `OpenAPIMetaResponse | None` | The responses the API can return | `None` | | `deprecated` | `bool` | Declares this operation to be deprecated | `False` | | `security` | `list[dict[str, list[str]]] | None` | A declaration of which security mechanisms can be used for this operation | `None` | | `external_docs` | `dict[str, str] | None` | Additional external documentation | `None` | | `language` | `str | None` | Language code to use for I18nString values | `None` | | `prefix_config` | `ConventionalPrefixConfig | None` | Configuration object for parameter prefixes | `None` | | `content_type` | `str | None` | Custom content type for request body. If None, will be auto-detected. | `None` | | `request_content_types` | `RequestContentTypes | None` | Multiple content types for request body. | `None` | | `response_content_types` | `ResponseContentTypes | None` | Multiple content types for response body. | `None` | | `content_type_resolver` | `Callable[[Any], str] | None` | Function to determine content type based on request. | `None` |

Source code in `src/flask_x_openapi_schema/x/flask/decorators.py`

```python
def __init__(
    self,
    summary: str | I18nStr | None = None,
    description: str | I18nStr | None = None,
    tags: list[str] | None = None,
    operation_id: str | None = None,
    responses: OpenAPIMetaResponse | None = None,
    deprecated: bool = False,
    security: list[dict[str, list[str]]] | None = None,
    external_docs: dict[str, str] | None = None,
    language: str | None = None,
    prefix_config: ConventionalPrefixConfig | None = None,
    content_type: str | None = None,
    request_content_types: RequestContentTypes | None = None,
    response_content_types: ResponseContentTypes | None = None,
    content_type_resolver: Callable[[Any], str] | None = None,
) -> None:
    """Initialize the decorator with OpenAPI metadata parameters.

    Args:
        summary: A short summary of what the operation does
        description: A verbose explanation of the operation behavior
        tags: A list of tags for API documentation control
        operation_id: Unique string used to identify the operation
        responses: The responses the API can return
        deprecated: Declares this operation to be deprecated
        security: A declaration of which security mechanisms can be used for this operation
        external_docs: Additional external documentation
        language: Language code to use for I18nString values
        prefix_config: Configuration object for parameter prefixes
        content_type: Custom content type for request body. If None, will be auto-detected.
        request_content_types: Multiple content types for request body.
        response_content_types: Multiple content types for response body.
        content_type_resolver: Function to determine content type based on request.

    """
    super().__init__(
        summary=summary,
        description=description,
        tags=tags,
        operation_id=operation_id,
        responses=responses,
        deprecated=deprecated,
        security=security,
        external_docs=external_docs,
        language=language,
        prefix_config=prefix_config,
        content_type=content_type,
        request_content_types=request_content_types,
        response_content_types=response_content_types,
        content_type_resolver=content_type_resolver,
    )
    self.framework = "flask"
    self.base_decorator = None

```

##### `extract_parameters_from_models(query_model, path_params)`

Extract OpenAPI parameters from models.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `query_model` | `type[BaseModel] | None` | The query parameter model | *required* | | `path_params` | `list[str] | None` | List of path parameter names | *required* |

Returns:

| Type | Description | | --- | --- | | `list[dict[str, Any]]` | List of OpenAPI parameter objects |

Source code in `src/flask_x_openapi_schema/x/flask/decorators.py`

```python
def extract_parameters_from_models(
    self,
    query_model: type[BaseModel] | None,
    path_params: list[str] | None,
) -> list[dict[str, Any]]:
    """Extract OpenAPI parameters from models.

    Args:
        query_model: The query parameter model
        path_params: List of path parameter names

    Returns:
        List of OpenAPI parameter objects

    """
    parameters = [
        {
            "name": param,
            "in": "path",
            "required": True,
            "schema": {"type": "string"},
        }
        for param in path_params
    ]

    if query_model:
        schema = query_model.model_json_schema()
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        for field_name, field_schema in properties.items():
            param = {
                "name": field_name,
                "in": "query",
                "required": field_name in required,
                "schema": field_schema,
            }

            if "description" in field_schema:
                param["description"] = field_schema["description"]

            parameters.append(param)

    return parameters

```

##### `process_additional_params(kwargs, param_names)`

Process additional framework-specific parameters.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `kwargs` | `dict[str, Any]` | The keyword arguments to update | *required* | | `param_names` | `list[str]` | List of parameter names that have been processed | *required* |

Returns:

| Type | Description | | --- | --- | | `dict[str, Any]` | Updated kwargs dictionary |

Source code in `src/flask_x_openapi_schema/x/flask/decorators.py`

```python
def process_additional_params(self, kwargs: dict[str, Any], param_names: list[str]) -> dict[str, Any]:
    """Process additional framework-specific parameters.

    Args:
        kwargs: The keyword arguments to update
        param_names: List of parameter names that have been processed

    Returns:
        Updated kwargs dictionary

    """
    logger = get_logger(__name__)
    logger.debug(f"Processing additional parameters with kwargs keys: {list(kwargs.keys())}")
    logger.debug(f"Processed parameter names: {param_names}")
    return kwargs

```

##### `process_query_params(param_name, model, kwargs)`

Process query parameters for Flask.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `param_name` | `str` | The parameter name to bind the model instance to | *required* | | `model` | `type[BaseModel]` | The Pydantic model class to use for validation | *required* | | `kwargs` | `dict[str, Any]` | The keyword arguments to update | *required* |

Returns:

| Type | Description | | --- | --- | | `dict[str, Any]` | Updated kwargs dictionary with the model instance |

Source code in `src/flask_x_openapi_schema/x/flask/decorators.py`

```python
def process_query_params(self, param_name: str, model: type[BaseModel], kwargs: dict[str, Any]) -> dict[str, Any]:
    """Process query parameters for Flask.

    Args:
        param_name: The parameter name to bind the model instance to
        model: The Pydantic model class to use for validation
        kwargs: The keyword arguments to update

    Returns:
        Updated kwargs dictionary with the model instance

    """
    query_data = {}
    model_fields = model.model_fields

    for field_name in model_fields:
        if field_name in request.args:
            query_data[field_name] = request.args.get(field_name)

    model_instance = model(**query_data)

    kwargs[param_name] = model_instance

    return kwargs

```

##### `process_request_body(param_name, model, kwargs)`

Process request body parameters for Flask.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `param_name` | `str` | The parameter name to bind the model instance to | *required* | | `model` | `type[BaseModel]` | The Pydantic model class to use for validation | *required* | | `kwargs` | `dict[str, Any]` | The keyword arguments to update | *required* |

Returns:

| Type | Description | | --- | --- | | `dict[str, Any]` | Updated kwargs dictionary with the model instance |

Source code in `src/flask_x_openapi_schema/x/flask/decorators.py`

```python
def process_request_body(self, param_name: str, model: type[BaseModel], kwargs: dict[str, Any]) -> dict[str, Any]:
    """Process request body parameters for Flask.

    Args:
        param_name: The parameter name to bind the model instance to
        model: The Pydantic model class to use for validation
        kwargs: The keyword arguments to update

    Returns:
        Updated kwargs dictionary with the model instance

    """
    from flask import request

    from flask_x_openapi_schema.models.file_models import FileField

    if hasattr(model, "model_fields") and hasattr(request, "files") and request.files:
        has_file_fields = False
        for field_info in model.model_fields.values():
            field_type = field_info.annotation

            if isinstance(field_type, type) and issubclass(field_type, FileField):
                has_file_fields = True
                break

            origin = getattr(field_type, "__origin__", None)
            if origin is list or origin is list:
                args = getattr(field_type, "__args__", [])
                if args and isinstance(args[0], type) and issubclass(args[0], FileField):
                    has_file_fields = True
                    break

        if has_file_fields:
            model_data = dict(request.form.items())
            for field_name in model.model_fields:
                if field_name in request.files:
                    model_data[field_name] = request.files[field_name]

            if model_data:
                try:
                    model_instance = model(**model_data)
                    kwargs[param_name] = model_instance
                except Exception as e:
                    logger = get_logger(__name__)
                    logger.exception(
                        f"Failed to create model instance with mock files for {model.__name__}", exc_info=e
                    )
                else:
                    return kwargs

    return super().process_request_body(param_name, model, kwargs)

```

#### `openapi_metadata(*, summary=None, description=None, tags=None, operation_id=None, responses=None, deprecated=False, security=None, external_docs=None, language=None, prefix_config=None, content_type=None, request_content_types=None, response_content_types=None, content_type_resolver=None)`

Decorator to add OpenAPI metadata to a Flask MethodView endpoint.

This decorator adds OpenAPI metadata to a Flask MethodView endpoint and handles parameter binding for request data. It automatically binds request body, query parameters, path parameters, and file uploads to function parameters based on their type annotations and parameter name prefixes.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `summary` | `str | I18nStr | None` | A short summary of what the operation does | `None` | | `description` | `str | I18nStr | None` | A verbose explanation of the operation behavior | `None` | | `tags` | `list[str] | None` | A list of tags for API documentation control | `None` | | `operation_id` | `str | None` | Unique string used to identify the operation | `None` | | `responses` | `OpenAPIMetaResponse | None` | The responses the API can return | `None` | | `deprecated` | `bool` | Declares this operation to be deprecated | `False` | | `security` | `list[dict[str, list[str]]] | None` | A declaration of which security mechanisms can be used for this operation | `None` | | `external_docs` | `dict[str, str] | None` | Additional external documentation | `None` | | `language` | `str | None` | Language code to use for I18nString values (default: current language) | `None` | | `prefix_config` | `ConventionalPrefixConfig | None` | Configuration object for parameter prefixes | `None` | | `content_type` | `str | None` | Custom content type for request body. If None, will be auto-detected. | `None` | | `request_content_types` | `RequestContentTypes | None` | Multiple content types for request body. | `None` | | `response_content_types` | `ResponseContentTypes | None` | Multiple content types for response body. | `None` | | `content_type_resolver` | `Callable[[Any], str] | None` | Function to determine content type based on request. | `None` |

Returns:

| Type | Description | | --- | --- | | `Callable[[F], F]` | The decorated function with OpenAPI metadata attached |

Examples:

```pycon
>>> from flask.views import MethodView
>>> from flask_x_openapi_schema.x.flask import openapi_metadata
>>> from flask_x_openapi_schema import OpenAPIMetaResponse, OpenAPIMetaResponseItem
>>> from pydantic import BaseModel, Field
>>>
>>> class ItemRequest(BaseModel):
...     name: str = Field(..., description="Item name")
...     price: float = Field(..., description="Item price")
>>>
>>> class ItemResponse(BaseModel):
...     id: str = Field(..., description="Item ID")
...     name: str = Field(..., description="Item name")
...     price: float = Field(..., description="Item price")
>>>
>>> class ItemView(MethodView):
...     @openapi_metadata(
...         summary="Create a new item",
...         description="Create a new item with the provided information",
...         tags=["items"],
...         operation_id="createItem",
...         responses=OpenAPIMetaResponse(
...             responses={
...                 "201": OpenAPIMetaResponseItem(model=ItemResponse, description="Item created successfully"),
...                 "400": OpenAPIMetaResponseItem(description="Invalid request data"),
...             }
...         ),
...     )
...     def post(self, _x_body: ItemRequest):
...         item = {"id": "123", "name": _x_body.name, "price": _x_body.price}
...         return item, 201

```

Source code in `src/flask_x_openapi_schema/x/flask/decorators.py`

```python
def openapi_metadata(
    *,
    summary: str | I18nStr | None = None,
    description: str | I18nStr | None = None,
    tags: list[str] | None = None,
    operation_id: str | None = None,
    responses: OpenAPIMetaResponse | None = None,
    deprecated: bool = False,
    security: list[dict[str, list[str]]] | None = None,
    external_docs: dict[str, str] | None = None,
    language: str | None = None,
    prefix_config: ConventionalPrefixConfig | None = None,
    content_type: str | None = None,
    request_content_types: RequestContentTypes | None = None,
    response_content_types: ResponseContentTypes | None = None,
    content_type_resolver: Callable[[Any], str] | None = None,
) -> Callable[[F], F]:
    """Decorator to add OpenAPI metadata to a Flask MethodView endpoint.

    This decorator adds OpenAPI metadata to a Flask MethodView endpoint and handles
    parameter binding for request data. It automatically binds request body, query parameters,
    path parameters, and file uploads to function parameters based on their type annotations
    and parameter name prefixes.

    Args:
        summary: A short summary of what the operation does
        description: A verbose explanation of the operation behavior
        tags: A list of tags for API documentation control
        operation_id: Unique string used to identify the operation
        responses: The responses the API can return
        deprecated: Declares this operation to be deprecated
        security: A declaration of which security mechanisms can be used for this operation
        external_docs: Additional external documentation
        language: Language code to use for I18nString values (default: current language)
        prefix_config: Configuration object for parameter prefixes
        content_type: Custom content type for request body. If None, will be auto-detected.
        request_content_types: Multiple content types for request body.
        response_content_types: Multiple content types for response body.
        content_type_resolver: Function to determine content type based on request.


    Returns:
        The decorated function with OpenAPI metadata attached

    Examples:
        >>> from flask.views import MethodView
        >>> from flask_x_openapi_schema.x.flask import openapi_metadata
        >>> from flask_x_openapi_schema import OpenAPIMetaResponse, OpenAPIMetaResponseItem
        >>> from pydantic import BaseModel, Field
        >>>
        >>> class ItemRequest(BaseModel):
        ...     name: str = Field(..., description="Item name")
        ...     price: float = Field(..., description="Item price")
        >>>
        >>> class ItemResponse(BaseModel):
        ...     id: str = Field(..., description="Item ID")
        ...     name: str = Field(..., description="Item name")
        ...     price: float = Field(..., description="Item price")
        >>>
        >>> class ItemView(MethodView):
        ...     @openapi_metadata(
        ...         summary="Create a new item",
        ...         description="Create a new item with the provided information",
        ...         tags=["items"],
        ...         operation_id="createItem",
        ...         responses=OpenAPIMetaResponse(
        ...             responses={
        ...                 "201": OpenAPIMetaResponseItem(model=ItemResponse, description="Item created successfully"),
        ...                 "400": OpenAPIMetaResponseItem(description="Invalid request data"),
        ...             }
        ...         ),
        ...     )
        ...     def post(self, _x_body: ItemRequest):
        ...         item = {"id": "123", "name": _x_body.name, "price": _x_body.price}
        ...         return item, 201

    """
    return FlaskOpenAPIDecorator(
        summary=summary,
        description=description,
        tags=tags,
        operation_id=operation_id,
        responses=responses,
        deprecated=deprecated,
        security=security,
        external_docs=external_docs,
        language=language,
        prefix_config=prefix_config,
        content_type=content_type,
        request_content_types=request_content_types,
        response_content_types=response_content_types,
        content_type_resolver=content_type_resolver,
    )

```

## Views

Utilities for integrating Pydantic models with Flask.MethodView.

This module provides utilities for integrating Pydantic models with Flask.MethodView classes. It includes classes and functions for collecting OpenAPI metadata from MethodView classes and generating OpenAPI schema documentation.

Examples:

Basic usage with Flask blueprint and MethodView:

```pycon
>>> from flask import Blueprint
>>> from flask.views import MethodView
>>> from flask_x_openapi_schema.x.flask import OpenAPIMethodViewMixin, openapi_metadata
>>> from pydantic import BaseModel, Field
>>>
>>> class ItemResponse(BaseModel):
...     id: str = Field(..., description="Item ID")
...     name: str = Field(..., description="Item name")
>>>
>>> class ItemView(OpenAPIMethodViewMixin, MethodView):
...     @openapi_metadata(summary="Get an item")
...     def get(self, item_id: str):
...         return {"id": item_id, "name": "Example Item"}
>>>
>>> bp = Blueprint("items", __name__)
>>> # Register the view to the blueprint
>>> _ = ItemView.register_to_blueprint(bp, "/items/<item_id>")

```

#### `MethodViewOpenAPISchemaGenerator`

Bases: `OpenAPISchemaGenerator`

OpenAPI schema generator for Flask.MethodView classes.

This class extends the base OpenAPISchemaGenerator to provide specific functionality for generating OpenAPI schema from Flask.MethodView classes. It processes MethodView resources registered to blueprints and extracts metadata for OpenAPI schema generation.

Source code in `src/flask_x_openapi_schema/x/flask/views.py`

```python
class MethodViewOpenAPISchemaGenerator(OpenAPISchemaGenerator):
    """OpenAPI schema generator for Flask.MethodView classes.

    This class extends the base OpenAPISchemaGenerator to provide specific functionality
    for generating OpenAPI schema from Flask.MethodView classes. It processes MethodView
    resources registered to blueprints and extracts metadata for OpenAPI schema generation.
    """

    def process_methodview_resources(self, blueprint: Any) -> None:
        """Process MethodView resources registered to a blueprint.

        Extracts OpenAPI metadata from MethodView classes registered to a blueprint
        and adds them to the OpenAPI schema.

        Args:
            blueprint: The Flask blueprint with registered MethodView resources

        """
        if not hasattr(blueprint, "_methodview_openapi_resources"):
            return

        for view_class, url in blueprint._methodview_openapi_resources:
            self._process_methodview(view_class, url, blueprint.url_prefix or "")

    def _register_models_from_method(self, method: Any) -> None:
        """Register Pydantic models from method type hints.

        Extracts Pydantic models from method type hints and registers them
        in the OpenAPI schema components.

        Args:
            method: The method to extract models from

        """
        type_hints = get_type_hints(method)

        for param_name, param_type in type_hints.items():
            if param_name == "return":
                continue

            if isinstance(param_type, type) and issubclass(param_type, BaseModel):
                self._register_model(param_type)

        metadata = getattr(method, "_openapi_metadata", {})
        if "responses" in metadata and hasattr(metadata["responses"], "responses"):
            for response_item in metadata["responses"].responses.values():
                if response_item.model:
                    self._register_model(response_item.model)

    def _process_methodview(self, view_class: Any, url: str, url_prefix: str) -> None:
        """Process a MethodView class for OpenAPI schema generation.

        Extracts metadata from a MethodView class and adds it to the OpenAPI schema.
        Processes HTTP methods, path parameters, request bodies, and responses.

        Args:
            view_class: The MethodView class
            url: The URL rule
            url_prefix: The URL prefix from the blueprint

        """
        methods = [
            method.upper() for method in ["get", "post", "put", "delete", "patch"] if hasattr(view_class, method)
        ]

        if not methods:
            return

        full_url = (url_prefix + url).replace("//", "/")

        from flask_x_openapi_schema.core.cache import get_parameter_prefixes

        _, _, path_prefix, _ = get_parameter_prefixes()
        path_prefix_len = len(path_prefix) + 1

        path = full_url
        for segment in full_url.split("/"):
            if segment.startswith("<") and segment.endswith(">"):
                if ":" in segment[1:-1]:
                    _, name = segment[1:-1].split(":", 1)
                else:
                    name = segment[1:-1]

                actual_name = name
                if name.startswith(f"{path_prefix}_"):
                    actual_name = name[path_prefix_len:]

                path = path.replace(segment, "{" + actual_name + "}")

        for method in methods:
            method_func = getattr(view_class, method.lower())

            metadata = getattr(method_func, "_openapi_metadata", {})

            path_parameters = extract_openapi_parameters_from_methodview(view_class, method.lower(), url)

            if not metadata:
                metadata = {
                    "summary": method_func.__doc__.split("\n")[0] if method_func.__doc__ else f"{method} {path}",
                    "description": method_func.__doc__ if method_func.__doc__ else "",
                }

                if path_parameters:
                    metadata["parameters"] = path_parameters

            elif path_parameters:
                if "parameters" in metadata:
                    existing_path_param_names = [p["name"] for p in metadata["parameters"] if p.get("in") == "path"]
                    new_path_params = [p for p in path_parameters if p["name"] not in existing_path_param_names]
                    metadata["parameters"].extend(new_path_params)
                else:
                    metadata["parameters"] = path_parameters

            self._register_models_from_method(method_func)

            type_hints = get_type_hints(method_func)
            for param_name, param_type in type_hints.items():
                if param_name == "return":
                    continue

                if isinstance(param_type, type) and issubclass(param_type, BaseModel):
                    is_file_upload = False
                    has_binary_fields = False

                    if hasattr(param_type, "model_config"):
                        config = getattr(param_type, "model_config", {})
                        if isinstance(config, dict) and config.get("json_schema_extra", {}).get(
                            "multipart/form-data",
                            False,
                        ):
                            is_file_upload = True
                    elif hasattr(param_type, "Config") and hasattr(param_type.Config, "json_schema_extra"):
                        config_extra = getattr(param_type.Config, "json_schema_extra", {})
                        is_file_upload = config_extra.get("multipart/form-data", False)

                    if hasattr(param_type, "model_fields"):
                        for field_info in param_type.model_fields.values():
                            field_schema = getattr(field_info, "json_schema_extra", None)
                            if field_schema is not None and field_schema.get("format") == "binary":
                                has_binary_fields = True
                                break

                    if is_file_upload or has_binary_fields:
                        if "requestBody" in metadata and "content" in metadata["requestBody"]:
                            if "application/json" in metadata["requestBody"]["content"]:
                                schema = metadata["requestBody"]["content"]["application/json"]["schema"]
                                metadata["requestBody"]["content"] = {"multipart/form-data": {"schema": schema}}

                            elif not metadata["requestBody"]["content"]:
                                metadata["requestBody"]["content"] = {
                                    "multipart/form-data": {
                                        "schema": {"$ref": f"#/components/schemas/{param_type.__name__}"},
                                    },
                                }

                        elif "requestBody" not in metadata:
                            metadata["requestBody"] = {
                                "content": {
                                    "multipart/form-data": {
                                        "schema": {"$ref": f"#/components/schemas/{param_type.__name__}"},
                                    },
                                },
                                "required": True,
                            }

                        if "parameters" in metadata:
                            metadata["parameters"] = [p for p in metadata["parameters"] if p["in"] in ["path", "query"]]

            if "responses" in metadata and hasattr(metadata["responses"], "to_openapi_dict"):
                if hasattr(metadata["responses"], "responses"):
                    for response_item in metadata["responses"].responses.values():
                        if response_item.model:
                            self._register_model(response_item.model)

                            if hasattr(response_item.model, "model_fields"):
                                for field_info in response_item.model.model_fields.values():
                                    field_type = field_info.annotation

                                    if hasattr(field_type, "__origin__") and field_type.__origin__ is not None:
                                        args = getattr(field_type, "__args__", [])
                                        for arg in args:
                                            if hasattr(arg, "__members__"):
                                                self._register_model(arg)
                                    elif hasattr(field_type, "__members__"):
                                        self._register_model(field_type)

                metadata["responses"] = metadata["responses"].to_openapi_dict()

            if path not in self.paths:
                self.paths[path] = {}

            self.paths[path][method.lower()] = metadata

```

##### `process_methodview_resources(blueprint)`

Process MethodView resources registered to a blueprint.

Extracts OpenAPI metadata from MethodView classes registered to a blueprint and adds them to the OpenAPI schema.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `blueprint` | `Any` | The Flask blueprint with registered MethodView resources | *required* |

Source code in `src/flask_x_openapi_schema/x/flask/views.py`

```python
def process_methodview_resources(self, blueprint: Any) -> None:
    """Process MethodView resources registered to a blueprint.

    Extracts OpenAPI metadata from MethodView classes registered to a blueprint
    and adds them to the OpenAPI schema.

    Args:
        blueprint: The Flask blueprint with registered MethodView resources

    """
    if not hasattr(blueprint, "_methodview_openapi_resources"):
        return

    for view_class, url in blueprint._methodview_openapi_resources:
        self._process_methodview(view_class, url, blueprint.url_prefix or "")

```

#### `OpenAPIMethodViewMixin`

A mixin class for Flask.MethodView to collect OpenAPI metadata.

This mixin class adds OpenAPI schema generation capabilities to Flask's MethodView. It provides a method to register the view to a blueprint while collecting metadata for OpenAPI schema generation.

Examples:

```pycon
>>> from flask import Blueprint
>>> from flask.views import MethodView
>>> from flask_x_openapi_schema.x.flask import OpenAPIMethodViewMixin, openapi_metadata
>>> from pydantic import BaseModel, Field
>>>
>>> class ItemResponse(BaseModel):
...     id: str = Field(..., description="Item ID")
...     name: str = Field(..., description="Item name")
>>>
>>> class ItemView(OpenAPIMethodViewMixin, MethodView):
...     @openapi_metadata(summary="Get an item")
...     def get(self, item_id: str):
...         return {"id": item_id, "name": "Example Item"}
>>>
>>> bp = Blueprint("items", __name__)
>>> # Register the view to the blueprint
>>> _ = ItemView.register_to_blueprint(bp, "/items/<item_id>")

```

Source code in `src/flask_x_openapi_schema/x/flask/views.py`

```python
class OpenAPIMethodViewMixin:
    """A mixin class for Flask.MethodView to collect OpenAPI metadata.

    This mixin class adds OpenAPI schema generation capabilities to Flask's MethodView.
    It provides a method to register the view to a blueprint while collecting metadata
    for OpenAPI schema generation.

    Examples:
        >>> from flask import Blueprint
        >>> from flask.views import MethodView
        >>> from flask_x_openapi_schema.x.flask import OpenAPIMethodViewMixin, openapi_metadata
        >>> from pydantic import BaseModel, Field
        >>>
        >>> class ItemResponse(BaseModel):
        ...     id: str = Field(..., description="Item ID")
        ...     name: str = Field(..., description="Item name")
        >>>
        >>> class ItemView(OpenAPIMethodViewMixin, MethodView):
        ...     @openapi_metadata(summary="Get an item")
        ...     def get(self, item_id: str):
        ...         return {"id": item_id, "name": "Example Item"}
        >>>
        >>> bp = Blueprint("items", __name__)
        >>> # Register the view to the blueprint
        >>> _ = ItemView.register_to_blueprint(bp, "/items/<item_id>")

    """

    @classmethod
    def register_to_blueprint(cls, blueprint: Any, url: str, endpoint: str | None = None, **kwargs: Any) -> Any:
        """Register the MethodView to a blueprint and collect OpenAPI metadata.

        This method registers the view to a blueprint and stores metadata for
        OpenAPI schema generation.

        Args:
            blueprint: The Flask blueprint to register to
            url: The URL rule to register
            endpoint: The endpoint name (defaults to the class name)
            **kwargs: Additional arguments to pass to add_url_rule

        Returns:
            Any: The view function

        Examples:
            >>> from flask import Blueprint
            >>> from flask.views import MethodView
            >>> from flask_x_openapi_schema.x.flask import OpenAPIMethodViewMixin
            >>> class ItemView(OpenAPIMethodViewMixin, MethodView):
            ...     def get(self, item_id: str):
            ...         return {"id": item_id, "name": "Example Item"}
            >>> bp = Blueprint("items", __name__)
            >>> # Register the view to the blueprint
            >>> _ = ItemView.register_to_blueprint(bp, "/items/<item_id>")

        """
        view_func = cls.as_view(endpoint or cls.__name__.lower())
        blueprint.add_url_rule(url, view_func=view_func, **kwargs)

        if not hasattr(blueprint, "_methodview_openapi_resources"):
            blueprint._methodview_openapi_resources = []

        blueprint._methodview_openapi_resources.append((cls, url))

        return view_func

```

##### `register_to_blueprint(blueprint, url, endpoint=None, **kwargs)`

Register the MethodView to a blueprint and collect OpenAPI metadata.

This method registers the view to a blueprint and stores metadata for OpenAPI schema generation.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `blueprint` | `Any` | The Flask blueprint to register to | *required* | | `url` | `str` | The URL rule to register | *required* | | `endpoint` | `str | None` | The endpoint name (defaults to the class name) | `None` | | `**kwargs` | `Any` | Additional arguments to pass to add_url_rule | `{}` |

Returns:

| Name | Type | Description | | --- | --- | --- | | `Any` | `Any` | The view function |

Examples:

```pycon
>>> from flask import Blueprint
>>> from flask.views import MethodView
>>> from flask_x_openapi_schema.x.flask import OpenAPIMethodViewMixin
>>> class ItemView(OpenAPIMethodViewMixin, MethodView):
...     def get(self, item_id: str):
...         return {"id": item_id, "name": "Example Item"}
>>> bp = Blueprint("items", __name__)
>>> # Register the view to the blueprint
>>> _ = ItemView.register_to_blueprint(bp, "/items/<item_id>")

```

Source code in `src/flask_x_openapi_schema/x/flask/views.py`

```python
@classmethod
def register_to_blueprint(cls, blueprint: Any, url: str, endpoint: str | None = None, **kwargs: Any) -> Any:
    """Register the MethodView to a blueprint and collect OpenAPI metadata.

    This method registers the view to a blueprint and stores metadata for
    OpenAPI schema generation.

    Args:
        blueprint: The Flask blueprint to register to
        url: The URL rule to register
        endpoint: The endpoint name (defaults to the class name)
        **kwargs: Additional arguments to pass to add_url_rule

    Returns:
        Any: The view function

    Examples:
        >>> from flask import Blueprint
        >>> from flask.views import MethodView
        >>> from flask_x_openapi_schema.x.flask import OpenAPIMethodViewMixin
        >>> class ItemView(OpenAPIMethodViewMixin, MethodView):
        ...     def get(self, item_id: str):
        ...         return {"id": item_id, "name": "Example Item"}
        >>> bp = Blueprint("items", __name__)
        >>> # Register the view to the blueprint
        >>> _ = ItemView.register_to_blueprint(bp, "/items/<item_id>")

    """
    view_func = cls.as_view(endpoint or cls.__name__.lower())
    blueprint.add_url_rule(url, view_func=view_func, **kwargs)

    if not hasattr(blueprint, "_methodview_openapi_resources"):
        blueprint._methodview_openapi_resources = []

    blueprint._methodview_openapi_resources.append((cls, url))

    return view_func

```

#### `extract_openapi_parameters_from_methodview(view_class, method, url)`

Extract OpenAPI parameters from a MethodView class method.

Analyzes a MethodView class method to extract path parameters and their types for OpenAPI schema generation.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `view_class` | `type[MethodView]` | The MethodView class | *required* | | `method` | `str` | The HTTP method (get, post, etc.) | *required* | | `url` | `str` | The URL rule | *required* |

Returns:

| Type | Description | | --- | --- | | `list[dict[str, Any]]` | list\[dict[str, Any]\]: List of OpenAPI parameter objects |

Source code in `src/flask_x_openapi_schema/x/flask/views.py`

```python
def extract_openapi_parameters_from_methodview(
    view_class: type[MethodView],
    method: str,
    url: str,
) -> list[dict[str, Any]]:
    """Extract OpenAPI parameters from a MethodView class method.

    Analyzes a MethodView class method to extract path parameters and their types
    for OpenAPI schema generation.

    Args:
        view_class: The MethodView class
        method: The HTTP method (get, post, etc.)
        url: The URL rule

    Returns:
        list[dict[str, Any]]: List of OpenAPI parameter objects

    """
    from flask_x_openapi_schema.core.cache import get_parameter_prefixes

    parameters = []

    method_func = getattr(view_class, method.lower(), None)
    if not method_func:
        return parameters

    type_hints = get_type_hints(method_func)

    _, _, path_prefix, _ = get_parameter_prefixes()
    path_prefix_len = len(path_prefix) + 1

    path_params = []
    for segment in url.split("/"):
        if segment.startswith("<") and segment.endswith(">"):
            if ":" in segment[1:-1]:
                _, name = segment[1:-1].split(":", 1)
            else:
                name = segment[1:-1]
            path_params.append(name)

    for param_name in path_params:
        actual_param_name = param_name
        if param_name.startswith(f"{path_prefix}_"):
            actual_param_name = param_name[path_prefix_len:]

        param_type = type_hints.get(param_name, str)
        param_schema = {"type": "string"}

        if param_type is int:
            param_schema = {"type": "integer"}
        elif param_type is float:
            param_schema = {"type": "number"}
        elif param_type is bool:
            param_schema = {"type": "boolean"}

        parameters.append(
            {
                "name": actual_param_name,
                "in": "path",
                "required": True,
                "schema": param_schema,
            },
        )

    for param_name, param_type in type_hints.items():
        if param_name in path_params or param_name == "return":
            continue

        if isinstance(param_type, type) and issubclass(param_type, BaseModel):
            pass

    return parameters

```

## Utilities

Utility functions for Flask integration.

This module provides utility functions for integrating Flask with OpenAPI schema generation. It includes functions for generating OpenAPI schemas from Flask blueprints, registering Pydantic models with schema generators, and extracting data from requests based on Pydantic models.

#### `extract_pydantic_data(model_class)`

Extract data from the request based on a Pydantic model.

This function extracts data from the current Flask request and validates it against the provided Pydantic model. It handles JSON data, form data, and query parameters.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `model_class` | `type[BaseModel]` | The Pydantic model class to use for validation. | *required* |

Returns:

| Name | Type | Description | | --- | --- | --- | | `BaseModel` | `BaseModel` | A validated instance of the provided Pydantic model. |

Raises:

| Type | Description | | --- | --- | | `ValidationError` | If the request data doesn't match the model's schema. |

Examples:

```pycon
>>> from flask import Flask, request
>>> from pydantic import BaseModel, Field
>>> app = Flask(__name__)
>>> class UserCreate(BaseModel):
...     username: str
...     email: str
...     age: int = Field(gt=0)
>>> @app.route("/users", methods=["POST"])
... def create_user():
...     # In a real request context:
...     user_data = extract_pydantic_data(UserCreate)
...     # user_data is now a validated UserCreate instance
...     return {"id": 1, "username": user_data.username}

```

Note

This function combines data from request.json, request.form, and request.args.

Source code in `src/flask_x_openapi_schema/x/flask/utils.py`

```python
def extract_pydantic_data(model_class: type[BaseModel]) -> BaseModel:
    """Extract data from the request based on a Pydantic model.

    This function extracts data from the current Flask request and validates it
    against the provided Pydantic model. It handles JSON data, form data, and
    query parameters.

    Args:
        model_class: The Pydantic model class to use for validation.

    Returns:
        BaseModel: A validated instance of the provided Pydantic model.

    Raises:
        ValidationError: If the request data doesn't match the model's schema.

    Examples:
        >>> from flask import Flask, request
        >>> from pydantic import BaseModel, Field
        >>> app = Flask(__name__)
        >>> class UserCreate(BaseModel):
        ...     username: str
        ...     email: str
        ...     age: int = Field(gt=0)
        >>> @app.route("/users", methods=["POST"])
        ... def create_user():
        ...     # In a real request context:
        ...     user_data = extract_pydantic_data(UserCreate)
        ...     # user_data is now a validated UserCreate instance
        ...     return {"id": 1, "username": user_data.username}

    Note:
        This function combines data from request.json, request.form, and request.args.

    """
    if request.is_json:
        data = request.get_json(silent=True) or {}
    elif request.form:
        data = request.form.to_dict()
    else:
        data = {}

    if request.args:
        for key, value in request.args.items():
            if key not in data:
                data[key] = value

    return model_class(**data)

```

#### `generate_openapi_schema(blueprint, title, version, description='', output_format='yaml', language=None)`

Generate an OpenAPI schema from a Flask blueprint with MethodView classes.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `blueprint` | `Blueprint` | The Flask blueprint with registered MethodView classes. | *required* | | `title` | `str | I18nStr` | The title of the API. Can be a string or I18nStr for internationalization. | *required* | | `version` | `str` | The version of the API. | *required* | | `description` | `str | I18nStr` | The description of the API. Can be a string or I18nStr for internationalization. | `''` | | `output_format` | `str` | The output format. Options are "yaml" or "json". Defaults to "yaml". | `'yaml'` | | `language` | `str | None` | The language to use for internationalized strings. If None, uses the current language. | `None` |

Returns:

| Type | Description | | --- | --- | | `dict[str, Any] | str` | dict or str: The OpenAPI schema as a dictionary (if output_format is "json") or as a YAML string (if output_format is "yaml"). |

Examples:

```pycon
>>> from flask import Blueprint
>>> bp = Blueprint("api", __name__)
>>> schema = generate_openapi_schema(
...     blueprint=bp, title="My API", version="1.0.0", description="My API Description", output_format="yaml"
... )
>>> isinstance(schema, str)
True
>>> "title: My API" in schema
True

```

Source code in `src/flask_x_openapi_schema/x/flask/utils.py`

```python
def generate_openapi_schema(
    blueprint: Blueprint,
    title: str | I18nStr,
    version: str,
    description: str | I18nStr = "",
    output_format: str = "yaml",
    language: str | None = None,
) -> dict[str, Any] | str:
    """Generate an OpenAPI schema from a Flask blueprint with MethodView classes.

    Args:
        blueprint: The Flask blueprint with registered MethodView classes.
        title: The title of the API. Can be a string or I18nStr for internationalization.
        version: The version of the API.
        description: The description of the API. Can be a string or I18nStr for internationalization.
        output_format: The output format. Options are "yaml" or "json". Defaults to "yaml".
        language: The language to use for internationalized strings. If None, uses the current language.

    Returns:
        dict or str: The OpenAPI schema as a dictionary (if output_format is "json")
            or as a YAML string (if output_format is "yaml").

    Examples:
        >>> from flask import Blueprint
        >>> bp = Blueprint("api", __name__)
        >>> schema = generate_openapi_schema(
        ...     blueprint=bp, title="My API", version="1.0.0", description="My API Description", output_format="yaml"
        ... )
        >>> isinstance(schema, str)
        True
        >>> "title: My API" in schema
        True

    """
    current_lang = language or get_current_language()

    generator = MethodViewOpenAPISchemaGenerator(
        title=title,
        version=version,
        description=description,
        language=current_lang,
    )

    generator.process_methodview_resources(blueprint=blueprint)

    schema = generator.generate_schema()

    if output_format == "yaml":
        import yaml

        return yaml.dump(schema, sort_keys=False, default_flow_style=False, allow_unicode=True)
    return schema

```

#### `register_model_schema(generator, model)`

Register a Pydantic model schema with an OpenAPI schema generator.

This function registers a Pydantic model with the OpenAPI schema generator, making it available in the components/schemas section of the generated OpenAPI schema.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `generator` | `OpenAPISchemaGenerator` | The OpenAPI schema generator instance. | *required* | | `model` | `type[BaseModel]` | The Pydantic model class to register. | *required* |

Examples:

```pycon
>>> from pydantic import BaseModel, Field
>>> from flask_x_openapi_schema.x.flask.views import MethodViewOpenAPISchemaGenerator
>>> class User(BaseModel):
...     id: int = Field(..., description="User ID")
...     name: str = Field(..., description="User name")
>>> generator = MethodViewOpenAPISchemaGenerator(title="My API", version="1.0.0")
>>> register_model_schema(generator, User)
>>> schema = generator.generate_schema()
>>> "User" in schema["components"]["schemas"]
True

```

Note

This function uses the internal \_register_model method of the generator.

Source code in `src/flask_x_openapi_schema/x/flask/utils.py`

```python
def register_model_schema(generator: OpenAPISchemaGenerator, model: type[BaseModel]) -> None:
    """Register a Pydantic model schema with an OpenAPI schema generator.

    This function registers a Pydantic model with the OpenAPI schema generator,
    making it available in the components/schemas section of the generated OpenAPI schema.

    Args:
        generator: The OpenAPI schema generator instance.
        model: The Pydantic model class to register.

    Examples:
        >>> from pydantic import BaseModel, Field
        >>> from flask_x_openapi_schema.x.flask.views import MethodViewOpenAPISchemaGenerator
        >>> class User(BaseModel):
        ...     id: int = Field(..., description="User ID")
        ...     name: str = Field(..., description="User name")
        >>> generator = MethodViewOpenAPISchemaGenerator(title="My API", version="1.0.0")
        >>> register_model_schema(generator, User)
        >>> schema = generator.generate_schema()
        >>> "User" in schema["components"]["schemas"]
        True

    Note:
        This function uses the internal _register_model method of the generator.

    """
    generator._register_model(model)

```
