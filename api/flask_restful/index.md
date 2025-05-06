# Flask-RESTful Integration

This section provides documentation for the Flask-RESTful specific components of Flask-X-OpenAPI-Schema.

## Flask-RESTful Module

Flask-RESTful specific implementations for OpenAPI schema generation.

#### `OpenAPIBlueprintMixin`

A mixin class for Flask Blueprint to collect OpenAPI metadata from MethodView classes.

This mixin extends Flask's Blueprint class to add OpenAPI schema generation capabilities for MethodView classes. It tracks MethodView classes registered to the blueprint and provides methods to generate OpenAPI schemas.

Examples:

```pycon
>>> from flask import Blueprint, Flask
>>> from flask.views import MethodView
>>> from flask_x_openapi_schema.x.flask_restful import OpenAPIBlueprintMixin
>>> from flask_x_openapi_schema.x.flask import openapi_metadata, OpenAPIMethodViewMixin
>>>
>>> app = Flask(__name__)
>>>
>>> class OpenAPIBlueprint(OpenAPIBlueprintMixin, Blueprint):
...     pass
>>>
>>> bp = OpenAPIBlueprint("api", __name__, url_prefix="/api")
>>>
>>> class ItemView(OpenAPIMethodViewMixin, MethodView):
...     @openapi_metadata(summary="Get an item")
...     def get(self, item_id):
...         return {"id": item_id, "name": "Example Item"}
>>>
>>> # Register the view to the blueprint (returns a view function)
>>> view_func = ItemView.register_to_blueprint(bp, "/items/<item_id>")
>>>
>>> app.register_blueprint(bp)
>>>
>>> # Generate OpenAPI schema
>>> schema = bp.generate_openapi_schema(title="My API", version="1.0.0", description="API for managing items")

```

Source code in `src/flask_x_openapi_schema/x/flask_restful/resources.py`

```python
class OpenAPIBlueprintMixin:
    """A mixin class for Flask Blueprint to collect OpenAPI metadata from MethodView classes.

    This mixin extends Flask's Blueprint class to add OpenAPI schema generation capabilities
    for MethodView classes. It tracks MethodView classes registered to the blueprint and
    provides methods to generate OpenAPI schemas.

    Examples:
        >>> from flask import Blueprint, Flask
        >>> from flask.views import MethodView
        >>> from flask_x_openapi_schema.x.flask_restful import OpenAPIBlueprintMixin
        >>> from flask_x_openapi_schema.x.flask import openapi_metadata, OpenAPIMethodViewMixin
        >>>
        >>> app = Flask(__name__)
        >>>
        >>> class OpenAPIBlueprint(OpenAPIBlueprintMixin, Blueprint):
        ...     pass
        >>>
        >>> bp = OpenAPIBlueprint("api", __name__, url_prefix="/api")
        >>>
        >>> class ItemView(OpenAPIMethodViewMixin, MethodView):
        ...     @openapi_metadata(summary="Get an item")
        ...     def get(self, item_id):
        ...         return {"id": item_id, "name": "Example Item"}
        >>>
        >>> # Register the view to the blueprint (returns a view function)
        >>> view_func = ItemView.register_to_blueprint(bp, "/items/<item_id>")
        >>>
        >>> app.register_blueprint(bp)
        >>>
        >>> # Generate OpenAPI schema
        >>> schema = bp.generate_openapi_schema(title="My API", version="1.0.0", description="API for managing items")

    """

    def configure_openapi(self, *, prefix_config: ConventionalPrefixConfig = None, **kwargs: Any) -> None:
        """Configure OpenAPI settings for this Blueprint instance.

        Args:
            prefix_config: Configuration object with parameter prefixes
            **kwargs: For backward compatibility - will be used to create a config object if prefix_config is None

        """
        if prefix_config is not None:
            configure_prefixes(prefix_config)
        elif kwargs:
            new_config = ConventionalPrefixConfig(
                request_body_prefix=kwargs.get(
                    "request_body_prefix",
                    GLOBAL_CONFIG_HOLDER.get().request_body_prefix,
                ),
                request_query_prefix=kwargs.get(
                    "request_query_prefix",
                    GLOBAL_CONFIG_HOLDER.get().request_query_prefix,
                ),
                request_path_prefix=kwargs.get(
                    "request_path_prefix",
                    GLOBAL_CONFIG_HOLDER.get().request_path_prefix,
                ),
                request_file_prefix=kwargs.get(
                    "request_file_prefix",
                    GLOBAL_CONFIG_HOLDER.get().request_file_prefix,
                ),
            )
            configure_prefixes(new_config)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the mixin.

        Args:
            *args: Arguments to pass to the parent class.
            **kwargs: Keyword arguments to pass to the parent class.

        """
        super().__init__(*args, **kwargs)

        self._methodview_openapi_resources = []

    def generate_openapi_schema(
        self,
        title: str | I18nStr,
        version: str,
        description: str | I18nStr = "",
        output_format: Literal["json", "yaml"] = "yaml",
        language: str | None = None,
    ) -> Any:
        """Generate an OpenAPI schema for the API.

        Args:
            title: The title of the API (can be an I18nString).
            version: The version of the API.
            description: The description of the API (can be an I18nString).
            output_format: The output format (json or yaml).
            language: The language to use for internationalized strings (default: current language).

        Returns:
            The OpenAPI schema as a dictionary (if json) or string (if yaml).

        """
        current_lang = language or get_current_language()

        generator = MethodViewOpenAPISchemaGenerator(title, version, description, language=current_lang)

        generator.process_methodview_resources(self)

        schema = generator.generate_schema()

        if output_format == "yaml":
            return yaml.dump(schema, sort_keys=False, default_flow_style=False, allow_unicode=True)
        return schema

```

##### `__init__(*args, **kwargs)`

Initialize the mixin.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `*args` | `Any` | Arguments to pass to the parent class. | `()` | | `**kwargs` | `Any` | Keyword arguments to pass to the parent class. | `{}` |

Source code in `src/flask_x_openapi_schema/x/flask_restful/resources.py`

```python
def __init__(self, *args: Any, **kwargs: Any) -> None:
    """Initialize the mixin.

    Args:
        *args: Arguments to pass to the parent class.
        **kwargs: Keyword arguments to pass to the parent class.

    """
    super().__init__(*args, **kwargs)

    self._methodview_openapi_resources = []

```

##### `configure_openapi(*, prefix_config=None, **kwargs)`

Configure OpenAPI settings for this Blueprint instance.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `prefix_config` | `ConventionalPrefixConfig` | Configuration object with parameter prefixes | `None` | | `**kwargs` | `Any` | For backward compatibility - will be used to create a config object if prefix_config is None | `{}` |

Source code in `src/flask_x_openapi_schema/x/flask_restful/resources.py`

```python
def configure_openapi(self, *, prefix_config: ConventionalPrefixConfig = None, **kwargs: Any) -> None:
    """Configure OpenAPI settings for this Blueprint instance.

    Args:
        prefix_config: Configuration object with parameter prefixes
        **kwargs: For backward compatibility - will be used to create a config object if prefix_config is None

    """
    if prefix_config is not None:
        configure_prefixes(prefix_config)
    elif kwargs:
        new_config = ConventionalPrefixConfig(
            request_body_prefix=kwargs.get(
                "request_body_prefix",
                GLOBAL_CONFIG_HOLDER.get().request_body_prefix,
            ),
            request_query_prefix=kwargs.get(
                "request_query_prefix",
                GLOBAL_CONFIG_HOLDER.get().request_query_prefix,
            ),
            request_path_prefix=kwargs.get(
                "request_path_prefix",
                GLOBAL_CONFIG_HOLDER.get().request_path_prefix,
            ),
            request_file_prefix=kwargs.get(
                "request_file_prefix",
                GLOBAL_CONFIG_HOLDER.get().request_file_prefix,
            ),
        )
        configure_prefixes(new_config)

```

##### `generate_openapi_schema(title, version, description='', output_format='yaml', language=None)`

Generate an OpenAPI schema for the API.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `title` | `str | I18nStr` | The title of the API (can be an I18nString). | *required* | | `version` | `str` | The version of the API. | *required* | | `description` | `str | I18nStr` | The description of the API (can be an I18nString). | `''` | | `output_format` | `Literal['json', 'yaml']` | The output format (json or yaml). | `'yaml'` | | `language` | `str | None` | The language to use for internationalized strings (default: current language). | `None` |

Returns:

| Type | Description | | --- | --- | | `Any` | The OpenAPI schema as a dictionary (if json) or string (if yaml). |

Source code in `src/flask_x_openapi_schema/x/flask_restful/resources.py`

```python
def generate_openapi_schema(
    self,
    title: str | I18nStr,
    version: str,
    description: str | I18nStr = "",
    output_format: Literal["json", "yaml"] = "yaml",
    language: str | None = None,
) -> Any:
    """Generate an OpenAPI schema for the API.

    Args:
        title: The title of the API (can be an I18nString).
        version: The version of the API.
        description: The description of the API (can be an I18nString).
        output_format: The output format (json or yaml).
        language: The language to use for internationalized strings (default: current language).

    Returns:
        The OpenAPI schema as a dictionary (if json) or string (if yaml).

    """
    current_lang = language or get_current_language()

    generator = MethodViewOpenAPISchemaGenerator(title, version, description, language=current_lang)

    generator.process_methodview_resources(self)

    schema = generator.generate_schema()

    if output_format == "yaml":
        return yaml.dump(schema, sort_keys=False, default_flow_style=False, allow_unicode=True)
    return schema

```

#### `OpenAPIIntegrationMixin`

Bases: `Api`

A mixin class for the flask-restful Api to collect OpenAPI metadata.

This mixin extends Flask-RESTful's Api class to add OpenAPI schema generation capabilities. It tracks resources added to the API and provides methods to generate OpenAPI schemas.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `*args` | `Any` | Arguments to pass to the parent class. | `()` | | `**kwargs` | `Any` | Keyword arguments to pass to the parent class. | `{}` |

Examples:

```pycon
>>> from flask import Flask
>>> from flask_restful import Resource
>>> from flask_x_openapi_schema.x.flask_restful import OpenAPIIntegrationMixin, openapi_metadata
>>> from pydantic import BaseModel, Field
>>>
>>> app = Flask(__name__)
>>>
>>> class OpenAPIApi(OpenAPIIntegrationMixin):
...     pass
>>>
>>> api = OpenAPIApi(app)
>>>
>>> class ItemResource(Resource):
...     @openapi_metadata(summary="Get an item")
...     def get(self, item_id):
...         return {"id": item_id, "name": "Example Item"}
>>>
>>> api.add_resource(ItemResource, "/items/<item_id>")
>>>
>>> # Generate OpenAPI schema
>>> schema = api.generate_openapi_schema(title="My API", version="1.0.0", description="API for managing items")

```

Source code in `src/flask_x_openapi_schema/x/flask_restful/resources.py`

```python
class OpenAPIIntegrationMixin(Api):
    """A mixin class for the flask-restful Api to collect OpenAPI metadata.

    This mixin extends Flask-RESTful's Api class to add OpenAPI schema generation capabilities.
    It tracks resources added to the API and provides methods to generate OpenAPI schemas.

    Args:
        *args: Arguments to pass to the parent class.
        **kwargs: Keyword arguments to pass to the parent class.

    Examples:
        >>> from flask import Flask
        >>> from flask_restful import Resource
        >>> from flask_x_openapi_schema.x.flask_restful import OpenAPIIntegrationMixin, openapi_metadata
        >>> from pydantic import BaseModel, Field
        >>>
        >>> app = Flask(__name__)
        >>>
        >>> class OpenAPIApi(OpenAPIIntegrationMixin):
        ...     pass
        >>>
        >>> api = OpenAPIApi(app)
        >>>
        >>> class ItemResource(Resource):
        ...     @openapi_metadata(summary="Get an item")
        ...     def get(self, item_id):
        ...         return {"id": item_id, "name": "Example Item"}
        >>>
        >>> api.add_resource(ItemResource, "/items/<item_id>")
        >>>
        >>> # Generate OpenAPI schema
        >>> schema = api.generate_openapi_schema(title="My API", version="1.0.0", description="API for managing items")

    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the mixin.

        Args:
            *args: Arguments to pass to the parent class.
            **kwargs: Keyword arguments to pass to the parent class.

        """
        super().__init__(*args, **kwargs)

        if not hasattr(self, "resources"):
            self.resources = []

    def add_resource(self, resource: Any, *urls: str, **kwargs: Any) -> Any:
        """Add a resource to the API and register it for OpenAPI schema generation.

        Args:
            resource: The resource class.
            *urls: The URLs to register the resource with.
            **kwargs: Additional arguments to pass to the parent method.

        Returns:
            The result of the parent method.

        """
        result = super().add_resource(resource, *urls, **kwargs)

        if not hasattr(self, "resources"):
            self.resources = []

        for existing_resource, existing_urls, _ in self.resources:
            if existing_resource == resource and set(existing_urls) == set(urls):
                return result

        if "endpoint" not in kwargs and kwargs is not None:
            kwargs["endpoint"] = resource.__name__.lower()
        elif kwargs is None:
            kwargs = {"endpoint": resource.__name__.lower()}

        self.resources.append((resource, urls, kwargs))

        return result

    def configure_openapi(self, *, prefix_config: ConventionalPrefixConfig = None, **kwargs: Any) -> None:
        """Configure OpenAPI settings for this API instance.

        Args:
            prefix_config: Configuration object with parameter prefixes
            **kwargs: For backward compatibility - will be used to create a config object if prefix_config is None

        """
        if prefix_config is not None:
            configure_prefixes(prefix_config)
        elif kwargs:
            new_config = ConventionalPrefixConfig(
                request_body_prefix=kwargs.get(
                    "request_body_prefix",
                    GLOBAL_CONFIG_HOLDER.get().request_body_prefix,
                ),
                request_query_prefix=kwargs.get(
                    "request_query_prefix",
                    GLOBAL_CONFIG_HOLDER.get().request_query_prefix,
                ),
                request_path_prefix=kwargs.get(
                    "request_path_prefix",
                    GLOBAL_CONFIG_HOLDER.get().request_path_prefix,
                ),
                request_file_prefix=kwargs.get(
                    "request_file_prefix",
                    GLOBAL_CONFIG_HOLDER.get().request_file_prefix,
                ),
            )
            configure_prefixes(new_config)

    def generate_openapi_schema(
        self,
        title: str | I18nStr,
        version: str,
        description: str | I18nStr = "",
        output_format: Literal["json", "yaml"] = "yaml",
        language: str | None = None,
    ) -> Any:
        """Generate an OpenAPI schema for the API.

        This method generates an OpenAPI schema for all resources registered with the API.
        It supports internationalization through I18nStr objects and can output the schema
        in either JSON or YAML format.

        Args:
            title: The title of the API (can be an I18nString).
            version: The version of the API.
            description: The description of the API (can be an I18nString).
            output_format: The output format (json or yaml).
            language: The language to use for internationalized strings (default: current language).

        Returns:
            The OpenAPI schema as a dictionary (if json) or string (if yaml).

        Examples:
            >>> from flask import Flask
            >>> from flask_restful import Resource
            >>> from flask_x_openapi_schema.x.flask_restful import OpenAPIIntegrationMixin, openapi_metadata
            >>> app = Flask(__name__)
            >>> class OpenAPIApi(OpenAPIIntegrationMixin):
            ...     pass
            >>> api = OpenAPIApi(app)
            >>> yaml_schema = api.generate_openapi_schema(
            ...     title="My API", version="1.0.0", description="API for managing items"
            ... )
            >>>
            >>> json_schema = api.generate_openapi_schema(
            ...     title="My API", version="1.0.0", description="API for managing items", output_format="json"
            ... )
            >>>
            >>> from flask_x_openapi_schema import I18nStr
            >>> i18n_schema = api.generate_openapi_schema(
            ...     title=I18nStr({"en-US": "My API", "zh-Hans": "我的API"}),
            ...     version="1.0.0",
            ...     description=I18nStr({"en-US": "API for managing items", "zh-Hans": "用于管理项目的API"}),
            ...     language="zh-Hans",
            ... )

        """
        current_lang = language or get_current_language()

        generator = OpenAPISchemaGenerator(title, version, description, language=current_lang)

        url_prefix = None
        if hasattr(self, "blueprint") and hasattr(self.blueprint, "url_prefix"):
            url_prefix = self.blueprint.url_prefix

        for resource, urls, _ in self.resources:
            generator._process_resource(resource, urls, url_prefix)

        schema = generator.generate_schema()

        if output_format == "yaml":
            return yaml.dump(schema, sort_keys=False, default_flow_style=False, allow_unicode=True)
        return schema

```

##### `__init__(*args, **kwargs)`

Initialize the mixin.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `*args` | `Any` | Arguments to pass to the parent class. | `()` | | `**kwargs` | `Any` | Keyword arguments to pass to the parent class. | `{}` |

Source code in `src/flask_x_openapi_schema/x/flask_restful/resources.py`

```python
def __init__(self, *args: Any, **kwargs: Any) -> None:
    """Initialize the mixin.

    Args:
        *args: Arguments to pass to the parent class.
        **kwargs: Keyword arguments to pass to the parent class.

    """
    super().__init__(*args, **kwargs)

    if not hasattr(self, "resources"):
        self.resources = []

```

##### `add_resource(resource, *urls, **kwargs)`

Add a resource to the API and register it for OpenAPI schema generation.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `resource` | `Any` | The resource class. | *required* | | `*urls` | `str` | The URLs to register the resource with. | `()` | | `**kwargs` | `Any` | Additional arguments to pass to the parent method. | `{}` |

Returns:

| Type | Description | | --- | --- | | `Any` | The result of the parent method. |

Source code in `src/flask_x_openapi_schema/x/flask_restful/resources.py`

```python
def add_resource(self, resource: Any, *urls: str, **kwargs: Any) -> Any:
    """Add a resource to the API and register it for OpenAPI schema generation.

    Args:
        resource: The resource class.
        *urls: The URLs to register the resource with.
        **kwargs: Additional arguments to pass to the parent method.

    Returns:
        The result of the parent method.

    """
    result = super().add_resource(resource, *urls, **kwargs)

    if not hasattr(self, "resources"):
        self.resources = []

    for existing_resource, existing_urls, _ in self.resources:
        if existing_resource == resource and set(existing_urls) == set(urls):
            return result

    if "endpoint" not in kwargs and kwargs is not None:
        kwargs["endpoint"] = resource.__name__.lower()
    elif kwargs is None:
        kwargs = {"endpoint": resource.__name__.lower()}

    self.resources.append((resource, urls, kwargs))

    return result

```

##### `configure_openapi(*, prefix_config=None, **kwargs)`

Configure OpenAPI settings for this API instance.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `prefix_config` | `ConventionalPrefixConfig` | Configuration object with parameter prefixes | `None` | | `**kwargs` | `Any` | For backward compatibility - will be used to create a config object if prefix_config is None | `{}` |

Source code in `src/flask_x_openapi_schema/x/flask_restful/resources.py`

```python
def configure_openapi(self, *, prefix_config: ConventionalPrefixConfig = None, **kwargs: Any) -> None:
    """Configure OpenAPI settings for this API instance.

    Args:
        prefix_config: Configuration object with parameter prefixes
        **kwargs: For backward compatibility - will be used to create a config object if prefix_config is None

    """
    if prefix_config is not None:
        configure_prefixes(prefix_config)
    elif kwargs:
        new_config = ConventionalPrefixConfig(
            request_body_prefix=kwargs.get(
                "request_body_prefix",
                GLOBAL_CONFIG_HOLDER.get().request_body_prefix,
            ),
            request_query_prefix=kwargs.get(
                "request_query_prefix",
                GLOBAL_CONFIG_HOLDER.get().request_query_prefix,
            ),
            request_path_prefix=kwargs.get(
                "request_path_prefix",
                GLOBAL_CONFIG_HOLDER.get().request_path_prefix,
            ),
            request_file_prefix=kwargs.get(
                "request_file_prefix",
                GLOBAL_CONFIG_HOLDER.get().request_file_prefix,
            ),
        )
        configure_prefixes(new_config)

```

##### `generate_openapi_schema(title, version, description='', output_format='yaml', language=None)`

Generate an OpenAPI schema for the API.

This method generates an OpenAPI schema for all resources registered with the API. It supports internationalization through I18nStr objects and can output the schema in either JSON or YAML format.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `title` | `str | I18nStr` | The title of the API (can be an I18nString). | *required* | | `version` | `str` | The version of the API. | *required* | | `description` | `str | I18nStr` | The description of the API (can be an I18nString). | `''` | | `output_format` | `Literal['json', 'yaml']` | The output format (json or yaml). | `'yaml'` | | `language` | `str | None` | The language to use for internationalized strings (default: current language). | `None` |

Returns:

| Type | Description | | --- | --- | | `Any` | The OpenAPI schema as a dictionary (if json) or string (if yaml). |

Examples:

```pycon
>>> from flask import Flask
>>> from flask_restful import Resource
>>> from flask_x_openapi_schema.x.flask_restful import OpenAPIIntegrationMixin, openapi_metadata
>>> app = Flask(__name__)
>>> class OpenAPIApi(OpenAPIIntegrationMixin):
...     pass
>>> api = OpenAPIApi(app)
>>> yaml_schema = api.generate_openapi_schema(
...     title="My API", version="1.0.0", description="API for managing items"
... )
>>>
>>> json_schema = api.generate_openapi_schema(
...     title="My API", version="1.0.0", description="API for managing items", output_format="json"
... )
>>>
>>> from flask_x_openapi_schema import I18nStr
>>> i18n_schema = api.generate_openapi_schema(
...     title=I18nStr({"en-US": "My API", "zh-Hans": "我的API"}),
...     version="1.0.0",
...     description=I18nStr({"en-US": "API for managing items", "zh-Hans": "用于管理项目的API"}),
...     language="zh-Hans",
... )

```

Source code in `src/flask_x_openapi_schema/x/flask_restful/resources.py`

```python
def generate_openapi_schema(
    self,
    title: str | I18nStr,
    version: str,
    description: str | I18nStr = "",
    output_format: Literal["json", "yaml"] = "yaml",
    language: str | None = None,
) -> Any:
    """Generate an OpenAPI schema for the API.

    This method generates an OpenAPI schema for all resources registered with the API.
    It supports internationalization through I18nStr objects and can output the schema
    in either JSON or YAML format.

    Args:
        title: The title of the API (can be an I18nString).
        version: The version of the API.
        description: The description of the API (can be an I18nString).
        output_format: The output format (json or yaml).
        language: The language to use for internationalized strings (default: current language).

    Returns:
        The OpenAPI schema as a dictionary (if json) or string (if yaml).

    Examples:
        >>> from flask import Flask
        >>> from flask_restful import Resource
        >>> from flask_x_openapi_schema.x.flask_restful import OpenAPIIntegrationMixin, openapi_metadata
        >>> app = Flask(__name__)
        >>> class OpenAPIApi(OpenAPIIntegrationMixin):
        ...     pass
        >>> api = OpenAPIApi(app)
        >>> yaml_schema = api.generate_openapi_schema(
        ...     title="My API", version="1.0.0", description="API for managing items"
        ... )
        >>>
        >>> json_schema = api.generate_openapi_schema(
        ...     title="My API", version="1.0.0", description="API for managing items", output_format="json"
        ... )
        >>>
        >>> from flask_x_openapi_schema import I18nStr
        >>> i18n_schema = api.generate_openapi_schema(
        ...     title=I18nStr({"en-US": "My API", "zh-Hans": "我的API"}),
        ...     version="1.0.0",
        ...     description=I18nStr({"en-US": "API for managing items", "zh-Hans": "用于管理项目的API"}),
        ...     language="zh-Hans",
        ... )

    """
    current_lang = language or get_current_language()

    generator = OpenAPISchemaGenerator(title, version, description, language=current_lang)

    url_prefix = None
    if hasattr(self, "blueprint") and hasattr(self.blueprint, "url_prefix"):
        url_prefix = self.blueprint.url_prefix

    for resource, urls, _ in self.resources:
        generator._process_resource(resource, urls, url_prefix)

    schema = generator.generate_schema()

    if output_format == "yaml":
        return yaml.dump(schema, sort_keys=False, default_flow_style=False, allow_unicode=True)
    return schema

```

#### `openapi_metadata(*, summary=None, description=None, tags=None, operation_id=None, deprecated=False, responses=None, security=None, external_docs=None, language=None, prefix_config=None, content_type=None, request_content_types=None, response_content_types=None, content_type_resolver=None)`

Decorator to add OpenAPI metadata to a Flask-RESTful Resource endpoint.

This decorator adds OpenAPI metadata to a Flask-RESTful Resource endpoint and handles parameter binding for request data. It automatically binds request body, query parameters, path parameters, and file uploads to function parameters based on their type annotations and parameter name prefixes.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `summary` | `str | I18nStr | None` | A short summary of what the operation does. | `None` | | `description` | `str | I18nStr | None` | A verbose explanation of the operation behavior. | `None` | | `tags` | `list[str] | None` | A list of tags for API documentation control. | `None` | | `operation_id` | `str | None` | Unique string used to identify the operation. | `None` | | `deprecated` | `bool` | Declares this operation to be deprecated. | `False` | | `responses` | `OpenAPIMetaResponse | None` | The responses the API can return. | `None` | | `security` | `list[dict[str, list[str]]] | None` | A declaration of which security mechanisms can be used for this operation. | `None` | | `external_docs` | `dict[str, str] | None` | Additional external documentation. | `None` | | `language` | `str | None` | Language code to use for I18nString values (default: current language). | `None` | | `prefix_config` | `ConventionalPrefixConfig | None` | Configuration object for parameter prefixes. | `None` | | `content_type` | `str | None` | Custom content type for request body. If None, will be auto-detected. | `None` | | `request_content_types` | `RequestContentTypes | None` | Multiple content types for request body. | `None` | | `response_content_types` | `ResponseContentTypes | None` | Multiple content types for response body. | `None` | | `content_type_resolver` | `Callable[[Any], str] | None` | Function to determine content type based on request. | `None` |

Returns:

| Type | Description | | --- | --- | | `Callable[[F], F] | F` | The decorated function with OpenAPI metadata attached. |

Examples:

```pycon
>>> from flask_restful import Resource
>>> from flask_x_openapi_schema.x.flask_restful import openapi_metadata
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
>>> class ItemResource(Resource):
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

Source code in `src/flask_x_openapi_schema/x/flask_restful/decorators.py`

```python
def openapi_metadata(
    *,
    summary: str | I18nStr | None = None,
    description: str | I18nStr | None = None,
    tags: list[str] | None = None,
    operation_id: str | None = None,
    deprecated: bool = False,
    responses: OpenAPIMetaResponse | None = None,
    security: list[dict[str, list[str]]] | None = None,
    external_docs: dict[str, str] | None = None,
    language: str | None = None,
    prefix_config: ConventionalPrefixConfig | None = None,
    content_type: str | None = None,
    request_content_types: RequestContentTypes | None = None,
    response_content_types: ResponseContentTypes | None = None,
    content_type_resolver: Callable[[Any], str] | None = None,
) -> Callable[[F], F] | F:
    """Decorator to add OpenAPI metadata to a Flask-RESTful Resource endpoint.

    This decorator adds OpenAPI metadata to a Flask-RESTful Resource endpoint and handles
    parameter binding for request data. It automatically binds request body, query parameters,
    path parameters, and file uploads to function parameters based on their type annotations
    and parameter name prefixes.

    Args:
        summary: A short summary of what the operation does.
        description: A verbose explanation of the operation behavior.
        tags: A list of tags for API documentation control.
        operation_id: Unique string used to identify the operation.
        deprecated: Declares this operation to be deprecated.
        responses: The responses the API can return.
        security: A declaration of which security mechanisms can be used for this operation.
        external_docs: Additional external documentation.
        language: Language code to use for I18nString values (default: current language).
        prefix_config: Configuration object for parameter prefixes.
        content_type: Custom content type for request body. If None, will be auto-detected.
        request_content_types: Multiple content types for request body.
        response_content_types: Multiple content types for response body.
        content_type_resolver: Function to determine content type based on request.


    Returns:
        The decorated function with OpenAPI metadata attached.

    Examples:
        >>> from flask_restful import Resource
        >>> from flask_x_openapi_schema.x.flask_restful import openapi_metadata
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
        >>> class ItemResource(Resource):
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
    return FlaskRestfulOpenAPIDecorator(
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

Decorators for adding OpenAPI metadata to Flask-RESTful Resource endpoints.

This module provides decorators and utilities for adding OpenAPI metadata to Flask-RESTful Resource class methods. It enables automatic parameter binding, request validation, and OpenAPI schema generation for Flask-RESTful APIs.

The main decorator `openapi_metadata` can be applied to Resource methods to add OpenAPI metadata and enable automatic parameter binding based on type annotations.

Examples:

Basic usage with Flask-RESTful Resource:

```pycon
>>> from flask_restful import Resource
>>> from flask_x_openapi_schema.x.flask_restful import openapi_metadata
>>> from pydantic import BaseModel, Field
>>>
>>> class UserModel(BaseModel):
...     name: str = Field(..., description="User name")
...     age: int = Field(..., description="User age")
>>>
>>> class UserResource(Resource):
...     @openapi_metadata(summary="Create user", tags=["users"])
...     def post(self, _x_body: UserModel):
...         return {"name": _x_body.name, "age": _x_body.age}, 201

```

#### `FlaskRestfulOpenAPIDecorator`

Bases: `DecoratorBase`

OpenAPI metadata decorator for Flask-RESTful Resource.

This class implements the decorator functionality for adding OpenAPI metadata to Flask-RESTful Resource methods. It handles parameter binding, request processing, and OpenAPI schema generation.

Attributes:

| Name | Type | Description | | --- | --- | --- | | `summary` | `str | I18nStr | None` | A short summary of what the operation does. | | `description` | `str | I18nStr | None` | A verbose explanation of the operation behavior. | | `tags` | `list[str] | None` | A list of tags for API documentation control. | | `operation_id` | `str | None` | Unique string used to identify the operation. | | `responses` | `OpenAPIMetaResponse | None` | The responses the API can return. | | `deprecated` | `bool` | Declares this operation to be deprecated. | | `security` | `list[dict[str, list[str]]] | None` | Security mechanisms for this operation. | | `external_docs` | `dict[str, str] | None` | Additional external documentation. | | `language` | `str | None` | Language code to use for I18nString values. | | `prefix_config` | `ConventionalPrefixConfig | None` | Configuration for parameter prefixes. | | `framework` | `str` | The framework being used ('flask_restful'). | | `base_decorator` | `OpenAPIDecoratorBase | None` | The base decorator instance. | | `parsed_args` | `Any | None` | Parsed arguments from request parser. |

Source code in `src/flask_x_openapi_schema/x/flask_restful/decorators.py`

```python
class FlaskRestfulOpenAPIDecorator(DecoratorBase):
    """OpenAPI metadata decorator for Flask-RESTful Resource.

    This class implements the decorator functionality for adding OpenAPI metadata
    to Flask-RESTful Resource methods. It handles parameter binding, request processing,
    and OpenAPI schema generation.

    Attributes:
        summary (str | I18nStr | None): A short summary of what the operation does.
        description (str | I18nStr | None): A verbose explanation of the operation behavior.
        tags (list[str] | None): A list of tags for API documentation control.
        operation_id (str | None): Unique string used to identify the operation.
        responses (OpenAPIMetaResponse | None): The responses the API can return.
        deprecated (bool): Declares this operation to be deprecated.
        security (list[dict[str, list[str]]] | None): Security mechanisms for this operation.
        external_docs (dict[str, str] | None): Additional external documentation.
        language (str | None): Language code to use for I18nString values.
        prefix_config (ConventionalPrefixConfig | None): Configuration for parameter prefixes.
        framework (str): The framework being used ('flask_restful').
        base_decorator (OpenAPIDecoratorBase | None): The base decorator instance.
        parsed_args (Any | None): Parsed arguments from request parser.

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
            summary: A short summary of what the operation does.
            description: A verbose explanation of the operation behavior.
            tags: A list of tags for API documentation control.
            operation_id: Unique string used to identify the operation.
            responses: The responses the API can return.
            deprecated: Declares this operation to be deprecated.
            security: A declaration of which security mechanisms can be used for this operation.
            external_docs: Additional external documentation.
            language: Language code to use for I18nString values.
            prefix_config: Configuration object for parameter prefixes.
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
        self.framework = "flask_restful"
        self.base_decorator = None
        self.parsed_args = None

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """Apply the decorator to the function.

        Args:
            func: The function to decorate.

        Returns:
            The decorated function.

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

        Converts Pydantic models and path parameters into OpenAPI parameter objects.

        Args:
            query_model: Pydantic model for query parameters.
            path_params: List of path parameter names.

        Returns:
            List of OpenAPI parameter objects.

        """
        parameters = []

        if path_params:
            parameters.extend(
                [
                    {
                        "name": param,
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                    }
                    for param in path_params
                ],
            )

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
        """Process request body parameters for Flask-RESTful.

        Args:
            param_name: The parameter name to bind the model instance to
            model: The Pydantic model class to use for validation
            kwargs: The keyword arguments to update

        Returns:
            Updated kwargs dictionary with the model instance

        """
        logger = get_logger(__name__)
        logger.debug(f"Processing request body for {param_name} with model {model.__name__}")

        is_multipart = False
        if hasattr(model, "model_config"):
            config = getattr(model, "model_config", {})
            if isinstance(config, dict) and config.get("json_schema_extra", {}).get("multipart/form-data", False):
                is_multipart = True
        elif hasattr(model, "Config") and hasattr(model.Config, "json_schema_extra"):
            config_extra = getattr(model.Config, "json_schema_extra", {})
            is_multipart = config_extra.get("multipart/form-data", False)

        has_file_fields = self._check_for_file_fields(model)

        if (has_file_fields or is_multipart) and (request.files or request.form):
            result = self._process_file_upload_model(model)

            if isinstance(result, BaseErrorResponse):
                response_dict, status_code = result.to_response(400)
                return make_response(response_dict, status_code)

            if result is not None:
                kwargs[param_name] = result
                return kwargs

        processed_kwargs = super().process_request_body(param_name, model, kwargs.copy())
        if param_name in processed_kwargs:
            return processed_kwargs

        json_model_instance = request_processor.process_request_data(request, model, param_name)
        if json_model_instance:
            logger.debug(f"Successfully created model instance from request data for {param_name}")
            kwargs[param_name] = json_model_instance
            return kwargs

        effective_content_type = self.content_type or request.content_type or ""
        if "form" in effective_content_type or "multipart" in effective_content_type:
            parser_location = "form"
        elif "json" in effective_content_type:
            parser_location = "json"
        elif any(
            binary_type in effective_content_type
            for binary_type in ["image/", "audio/", "video/", "application/octet-stream"]
        ):
            parser_location = "binary"
        elif "text/event-stream" in effective_content_type:
            parser_location = "json"
        else:
            parser_location = "form" if is_multipart else "json"

        logger.debug(f"Using parser location: {parser_location}")

        parser = self._get_or_create_parser(model, location=parser_location)
        self.parsed_args = parser.parse_args()

        if self.parsed_args:
            try:
                processed_data = preprocess_request_data(self.parsed_args, model)
                model_instance = safe_operation(
                    lambda: ModelFactory.create_from_data(model, processed_data), fallback=None
                )
                if model_instance:
                    logger.debug(f"Successfully created model instance from reqparse for {param_name}")
                    kwargs[param_name] = model_instance
                    return kwargs
            except Exception:
                logger.exception("Error processing reqparse data")

        logger.warning(f"No valid request data found for {param_name}, creating default instance")
        try:
            model_instance = safe_operation(lambda: model(), fallback=None)
            if model_instance:
                logger.debug(f"Created empty model instance for {param_name}")
                kwargs[param_name] = model_instance
        except Exception:
            logger.exception("Failed to create default model instance")

        return kwargs

    def _check_for_file_fields(self, model: type[BaseModel]) -> bool:
        """Check if a model contains file upload fields.

        Args:
            model: The model to check

        Returns:
            True if the model has file fields, False otherwise

        """
        if not hasattr(model, "model_fields"):
            return False

        for field_info in model.model_fields.values():
            field_type = field_info.annotation

            if inspect.isclass(field_type) and issubclass(field_type, FileField):
                return True

            origin = getattr(field_type, "__origin__", None)
            if origin is list or origin is list:
                args = getattr(field_type, "__args__", [])
                if args and isinstance(args[0], type) and issubclass(args[0], FileField):
                    return True

        return False

    def _process_file_upload_model(self, model: type[BaseModel]) -> BaseModel:
        """Process a file upload model with form data and files.

        Args:
            model: The model class to instantiate

        Returns:
            An instance of the model with file data

        """
        logger = get_logger(__name__)
        logger.debug(f"Processing file upload model for {model.__name__}")

        model_data = dict(request.form.items())
        logger.debug(f"Form data: {model_data}")

        has_file_fields = False
        file_field_names = []

        for field_name, field_info in model.model_fields.items():
            field_type = field_info.annotation

            if inspect.isclass(field_type) and issubclass(field_type, FileField):
                has_file_fields = True
                file_field_names.append(field_name)
                continue

            origin = getattr(field_type, "__origin__", None)
            if origin is list or origin is list:
                args = getattr(field_type, "__args__", [])
                if args and isinstance(args[0], type) and issubclass(args[0], FileField):
                    has_file_fields = True
                    file_field_names.append(field_name)

        files_found = False

        for field_name, field_info in model.model_fields.items():
            field_type = field_info.annotation

            if inspect.isclass(field_type) and issubclass(field_type, FileField):
                if field_name in request.files:
                    model_data[field_name] = request.files[field_name]
                    files_found = True
                    logger.debug(f"Found file for field {field_name}: {request.files[field_name].filename}")
                elif "file" in request.files and field_name == "file":
                    model_data[field_name] = request.files["file"]
                    files_found = True
                    logger.debug(f"Using default file for field {field_name}: {request.files['file'].filename}")
                elif "avatar" in request.files and field_name == "avatar":
                    model_data[field_name] = request.files["avatar"]
                    files_found = True
                    logger.debug(f"Using avatar file for field {field_name}: {request.files['avatar'].filename}")
                elif len(request.files) == 1:
                    file_key = next(iter(request.files))
                    model_data[field_name] = request.files[file_key]
                    files_found = True
                    logger.debug(f"Using single file for field {field_name}: {request.files[file_key].filename}")

            else:
                origin = getattr(field_type, "__origin__", None)
                if origin is list or origin is list:
                    args = getattr(field_type, "__args__", [])
                    if args and isinstance(args[0], type) and issubclass(args[0], FileField):
                        if field_name in request.files:
                            if hasattr(request.files, "getlist"):
                                files_list = request.files.getlist(field_name)
                                if files_list:
                                    model_data[field_name] = files_list
                                    files_found = True
                                    logger.debug(
                                        f"Found multiple files for field {field_name}: {len(files_list)} files"
                                    )
                        else:
                            all_files = []
                            for file_key in request.files:
                                if hasattr(request.files, "getlist"):
                                    all_files.extend(request.files.getlist(file_key))
                                else:
                                    all_files.append(request.files[file_key])

                            if all_files:
                                model_data[field_name] = all_files
                                files_found = True
                                logger.debug(f"Collected all files for field {field_name}: {len(all_files)} files")

        if has_file_fields and not files_found:
            logger.warning(f"No files found for file fields: {file_field_names}")
            error_message = f"No files found for required fields: {', '.join(file_field_names)}"
            return self.default_error_response(error="FILE_REQUIRED", message=error_message)

        processed_data = preprocess_request_data(model_data, model)
        logger.debug(f"Processed data: {processed_data}")

        try:
            return ModelFactory.create_from_data(model, processed_data)
        except Exception:
            logger.exception("Error creating model instance")

            return model(**model_data)

    def _get_or_create_parser(self, model: type[BaseModel], location: str = "json") -> Any:
        """Create a parser for the model.

        Args:
            model: The model to create a parser for
            location: The location to look for arguments (json, form, binary, args, etc.)

        Returns:
            A RequestParser instance for the model

        """
        if location == "binary":
            logger = get_logger(__name__)
            logger.debug("Using binary parser, will handle raw data separately")

            return reqparse.RequestParser(bundle_errors=True)

        return create_reqparse_from_pydantic(model=model, location=location)

    def _create_model_from_args(self, model: type[BaseModel], args: dict[str, Any]) -> BaseModel:
        """Create a model instance from parsed arguments.

        Args:
            model: The model class to instantiate
            args: The parsed arguments

        Returns:
            An instance of the model

        """
        logger = get_logger(__name__)
        logger.debug(f"Creating model instance for {model.__name__} from args")

        processed_data = preprocess_request_data(args, model)
        logger.debug("Processed data", extra={"processed_data": processed_data})

        model_instance = safe_operation(lambda: ModelFactory.create_from_data(model, processed_data), fallback=None)

        if model_instance:
            logger.debug("Successfully created model instance")
            return model_instance

        logger.warning("Failed to create model instance from args, creating empty instance")

        try:
            model_instance = model()
            logger.debug("Created empty model instance")
        except Exception as empty_err:
            logger.exception("Failed to create empty model instance")

            if hasattr(model, "model_json_schema"):
                schema = model.model_json_schema()
                required_fields = schema.get("required", [])
                default_data = {}

                for field in required_fields:
                    if field in model.model_fields:
                        field_info = model.model_fields[field]
                        if field_info.annotation is str:
                            default_data[field] = ""
                        elif field_info.annotation is int:
                            default_data[field] = 0
                        elif field_info.annotation is float:
                            default_data[field] = 0.0
                        elif field_info.annotation is bool:
                            default_data[field] = False
                        else:
                            default_data[field] = None

                try:
                    model_instance = model.model_validate(default_data)
                    logger.debug("Created model instance with default values")
                except Exception:
                    logger.exception("Failed to create model instance with default values")
                else:
                    return model_instance

            error_msg = f"Failed to create instance of {model.__name__}"
            raise ValueError(error_msg) from empty_err
        else:
            return model_instance

    def process_query_params(self, param_name: str, model: type[BaseModel], kwargs: dict[str, Any]) -> dict[str, Any]:
        """Process query parameters for Flask-RESTful.

        Args:
            param_name: The parameter name to bind the model instance to.
            model: The Pydantic model class to use for validation.
            kwargs: The keyword arguments to update.

        Returns:
            Updated kwargs dictionary with the model instance.

        """
        logger = get_logger(__name__)

        if self.parsed_args:
            model_instance = self._create_model_from_args(model, self.parsed_args)
            kwargs[param_name] = model_instance
            return kwargs

        parser = self._get_or_create_query_parser(model)

        self.parsed_args = parser.parse_args()

        try:
            model_instance = self._create_model_from_args(model, self.parsed_args)
            kwargs[param_name] = model_instance
        except Exception:
            logger.exception(f"Failed to create model instance for {param_name}")

            try:
                model_instance = model()
                logger.debug(f"Created empty model instance for {param_name}")
                kwargs[param_name] = model_instance
            except Exception:
                logger.exception(f"Failed to create empty model instance for {param_name}")

        return kwargs

    def _get_or_create_query_parser(self, model: type[BaseModel]) -> Any:
        """Create a query parser for the model.

        Args:
            model: The model to create a parser for

        Returns:
            A RequestParser instance for the model

        """
        return create_reqparse_from_pydantic(model=model, location="args")

    def process_additional_params(self, kwargs: dict[str, Any], param_names: list[str]) -> dict[str, Any]:
        """Process additional framework-specific parameters.

        Args:
            kwargs: The keyword arguments to update.
            param_names: List of parameter names that have been processed.

        Returns:
            Updated kwargs dictionary.

        """
        if self.parsed_args:
            for arg_name, arg_value in self.parsed_args.items():
                if arg_name not in kwargs and arg_name not in param_names:
                    kwargs[arg_name] = arg_value
        return kwargs

```

##### `__call__(func)`

Apply the decorator to the function.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `func` | `Callable[..., Any]` | The function to decorate. | *required* |

Returns:

| Type | Description | | --- | --- | | `Callable[..., Any]` | The decorated function. |

Source code in `src/flask_x_openapi_schema/x/flask_restful/decorators.py`

```python
def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
    """Apply the decorator to the function.

    Args:
        func: The function to decorate.

    Returns:
        The decorated function.

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

| Name | Type | Description | Default | | --- | --- | --- | --- | | `summary` | `str | I18nStr | None` | A short summary of what the operation does. | `None` | | `description` | `str | I18nStr | None` | A verbose explanation of the operation behavior. | `None` | | `tags` | `list[str] | None` | A list of tags for API documentation control. | `None` | | `operation_id` | `str | None` | Unique string used to identify the operation. | `None` | | `responses` | `OpenAPIMetaResponse | None` | The responses the API can return. | `None` | | `deprecated` | `bool` | Declares this operation to be deprecated. | `False` | | `security` | `list[dict[str, list[str]]] | None` | A declaration of which security mechanisms can be used for this operation. | `None` | | `external_docs` | `dict[str, str] | None` | Additional external documentation. | `None` | | `language` | `str | None` | Language code to use for I18nString values. | `None` | | `prefix_config` | `ConventionalPrefixConfig | None` | Configuration object for parameter prefixes. | `None` | | `content_type` | `str | None` | Custom content type for request body. If None, will be auto-detected. | `None` | | `request_content_types` | `RequestContentTypes | None` | Multiple content types for request body. | `None` | | `response_content_types` | `ResponseContentTypes | None` | Multiple content types for response body. | `None` | | `content_type_resolver` | `Callable[[Any], str] | None` | Function to determine content type based on request. | `None` |

Source code in `src/flask_x_openapi_schema/x/flask_restful/decorators.py`

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
        summary: A short summary of what the operation does.
        description: A verbose explanation of the operation behavior.
        tags: A list of tags for API documentation control.
        operation_id: Unique string used to identify the operation.
        responses: The responses the API can return.
        deprecated: Declares this operation to be deprecated.
        security: A declaration of which security mechanisms can be used for this operation.
        external_docs: Additional external documentation.
        language: Language code to use for I18nString values.
        prefix_config: Configuration object for parameter prefixes.
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
    self.framework = "flask_restful"
    self.base_decorator = None
    self.parsed_args = None

```

##### `extract_parameters_from_models(query_model, path_params)`

Extract OpenAPI parameters from models.

Converts Pydantic models and path parameters into OpenAPI parameter objects.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `query_model` | `type[BaseModel] | None` | Pydantic model for query parameters. | *required* | | `path_params` | `list[str] | None` | List of path parameter names. | *required* |

Returns:

| Type | Description | | --- | --- | | `list[dict[str, Any]]` | List of OpenAPI parameter objects. |

Source code in `src/flask_x_openapi_schema/x/flask_restful/decorators.py`

```python
def extract_parameters_from_models(
    self,
    query_model: type[BaseModel] | None,
    path_params: list[str] | None,
) -> list[dict[str, Any]]:
    """Extract OpenAPI parameters from models.

    Converts Pydantic models and path parameters into OpenAPI parameter objects.

    Args:
        query_model: Pydantic model for query parameters.
        path_params: List of path parameter names.

    Returns:
        List of OpenAPI parameter objects.

    """
    parameters = []

    if path_params:
        parameters.extend(
            [
                {
                    "name": param,
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"},
                }
                for param in path_params
            ],
        )

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

| Name | Type | Description | Default | | --- | --- | --- | --- | | `kwargs` | `dict[str, Any]` | The keyword arguments to update. | *required* | | `param_names` | `list[str]` | List of parameter names that have been processed. | *required* |

Returns:

| Type | Description | | --- | --- | | `dict[str, Any]` | Updated kwargs dictionary. |

Source code in `src/flask_x_openapi_schema/x/flask_restful/decorators.py`

```python
def process_additional_params(self, kwargs: dict[str, Any], param_names: list[str]) -> dict[str, Any]:
    """Process additional framework-specific parameters.

    Args:
        kwargs: The keyword arguments to update.
        param_names: List of parameter names that have been processed.

    Returns:
        Updated kwargs dictionary.

    """
    if self.parsed_args:
        for arg_name, arg_value in self.parsed_args.items():
            if arg_name not in kwargs and arg_name not in param_names:
                kwargs[arg_name] = arg_value
    return kwargs

```

##### `process_query_params(param_name, model, kwargs)`

Process query parameters for Flask-RESTful.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `param_name` | `str` | The parameter name to bind the model instance to. | *required* | | `model` | `type[BaseModel]` | The Pydantic model class to use for validation. | *required* | | `kwargs` | `dict[str, Any]` | The keyword arguments to update. | *required* |

Returns:

| Type | Description | | --- | --- | | `dict[str, Any]` | Updated kwargs dictionary with the model instance. |

Source code in `src/flask_x_openapi_schema/x/flask_restful/decorators.py`

```python
def process_query_params(self, param_name: str, model: type[BaseModel], kwargs: dict[str, Any]) -> dict[str, Any]:
    """Process query parameters for Flask-RESTful.

    Args:
        param_name: The parameter name to bind the model instance to.
        model: The Pydantic model class to use for validation.
        kwargs: The keyword arguments to update.

    Returns:
        Updated kwargs dictionary with the model instance.

    """
    logger = get_logger(__name__)

    if self.parsed_args:
        model_instance = self._create_model_from_args(model, self.parsed_args)
        kwargs[param_name] = model_instance
        return kwargs

    parser = self._get_or_create_query_parser(model)

    self.parsed_args = parser.parse_args()

    try:
        model_instance = self._create_model_from_args(model, self.parsed_args)
        kwargs[param_name] = model_instance
    except Exception:
        logger.exception(f"Failed to create model instance for {param_name}")

        try:
            model_instance = model()
            logger.debug(f"Created empty model instance for {param_name}")
            kwargs[param_name] = model_instance
        except Exception:
            logger.exception(f"Failed to create empty model instance for {param_name}")

    return kwargs

```

##### `process_request_body(param_name, model, kwargs)`

Process request body parameters for Flask-RESTful.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `param_name` | `str` | The parameter name to bind the model instance to | *required* | | `model` | `type[BaseModel]` | The Pydantic model class to use for validation | *required* | | `kwargs` | `dict[str, Any]` | The keyword arguments to update | *required* |

Returns:

| Type | Description | | --- | --- | | `dict[str, Any]` | Updated kwargs dictionary with the model instance |

Source code in `src/flask_x_openapi_schema/x/flask_restful/decorators.py`

```python
def process_request_body(self, param_name: str, model: type[BaseModel], kwargs: dict[str, Any]) -> dict[str, Any]:
    """Process request body parameters for Flask-RESTful.

    Args:
        param_name: The parameter name to bind the model instance to
        model: The Pydantic model class to use for validation
        kwargs: The keyword arguments to update

    Returns:
        Updated kwargs dictionary with the model instance

    """
    logger = get_logger(__name__)
    logger.debug(f"Processing request body for {param_name} with model {model.__name__}")

    is_multipart = False
    if hasattr(model, "model_config"):
        config = getattr(model, "model_config", {})
        if isinstance(config, dict) and config.get("json_schema_extra", {}).get("multipart/form-data", False):
            is_multipart = True
    elif hasattr(model, "Config") and hasattr(model.Config, "json_schema_extra"):
        config_extra = getattr(model.Config, "json_schema_extra", {})
        is_multipart = config_extra.get("multipart/form-data", False)

    has_file_fields = self._check_for_file_fields(model)

    if (has_file_fields or is_multipart) and (request.files or request.form):
        result = self._process_file_upload_model(model)

        if isinstance(result, BaseErrorResponse):
            response_dict, status_code = result.to_response(400)
            return make_response(response_dict, status_code)

        if result is not None:
            kwargs[param_name] = result
            return kwargs

    processed_kwargs = super().process_request_body(param_name, model, kwargs.copy())
    if param_name in processed_kwargs:
        return processed_kwargs

    json_model_instance = request_processor.process_request_data(request, model, param_name)
    if json_model_instance:
        logger.debug(f"Successfully created model instance from request data for {param_name}")
        kwargs[param_name] = json_model_instance
        return kwargs

    effective_content_type = self.content_type or request.content_type or ""
    if "form" in effective_content_type or "multipart" in effective_content_type:
        parser_location = "form"
    elif "json" in effective_content_type:
        parser_location = "json"
    elif any(
        binary_type in effective_content_type
        for binary_type in ["image/", "audio/", "video/", "application/octet-stream"]
    ):
        parser_location = "binary"
    elif "text/event-stream" in effective_content_type:
        parser_location = "json"
    else:
        parser_location = "form" if is_multipart else "json"

    logger.debug(f"Using parser location: {parser_location}")

    parser = self._get_or_create_parser(model, location=parser_location)
    self.parsed_args = parser.parse_args()

    if self.parsed_args:
        try:
            processed_data = preprocess_request_data(self.parsed_args, model)
            model_instance = safe_operation(
                lambda: ModelFactory.create_from_data(model, processed_data), fallback=None
            )
            if model_instance:
                logger.debug(f"Successfully created model instance from reqparse for {param_name}")
                kwargs[param_name] = model_instance
                return kwargs
        except Exception:
            logger.exception("Error processing reqparse data")

    logger.warning(f"No valid request data found for {param_name}, creating default instance")
    try:
        model_instance = safe_operation(lambda: model(), fallback=None)
        if model_instance:
            logger.debug(f"Created empty model instance for {param_name}")
            kwargs[param_name] = model_instance
    except Exception:
        logger.exception("Failed to create default model instance")

    return kwargs

```

#### `openapi_metadata(*, summary=None, description=None, tags=None, operation_id=None, deprecated=False, responses=None, security=None, external_docs=None, language=None, prefix_config=None, content_type=None, request_content_types=None, response_content_types=None, content_type_resolver=None)`

Decorator to add OpenAPI metadata to a Flask-RESTful Resource endpoint.

This decorator adds OpenAPI metadata to a Flask-RESTful Resource endpoint and handles parameter binding for request data. It automatically binds request body, query parameters, path parameters, and file uploads to function parameters based on their type annotations and parameter name prefixes.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `summary` | `str | I18nStr | None` | A short summary of what the operation does. | `None` | | `description` | `str | I18nStr | None` | A verbose explanation of the operation behavior. | `None` | | `tags` | `list[str] | None` | A list of tags for API documentation control. | `None` | | `operation_id` | `str | None` | Unique string used to identify the operation. | `None` | | `deprecated` | `bool` | Declares this operation to be deprecated. | `False` | | `responses` | `OpenAPIMetaResponse | None` | The responses the API can return. | `None` | | `security` | `list[dict[str, list[str]]] | None` | A declaration of which security mechanisms can be used for this operation. | `None` | | `external_docs` | `dict[str, str] | None` | Additional external documentation. | `None` | | `language` | `str | None` | Language code to use for I18nString values (default: current language). | `None` | | `prefix_config` | `ConventionalPrefixConfig | None` | Configuration object for parameter prefixes. | `None` | | `content_type` | `str | None` | Custom content type for request body. If None, will be auto-detected. | `None` | | `request_content_types` | `RequestContentTypes | None` | Multiple content types for request body. | `None` | | `response_content_types` | `ResponseContentTypes | None` | Multiple content types for response body. | `None` | | `content_type_resolver` | `Callable[[Any], str] | None` | Function to determine content type based on request. | `None` |

Returns:

| Type | Description | | --- | --- | | `Callable[[F], F] | F` | The decorated function with OpenAPI metadata attached. |

Examples:

```pycon
>>> from flask_restful import Resource
>>> from flask_x_openapi_schema.x.flask_restful import openapi_metadata
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
>>> class ItemResource(Resource):
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

Source code in `src/flask_x_openapi_schema/x/flask_restful/decorators.py`

```python
def openapi_metadata(
    *,
    summary: str | I18nStr | None = None,
    description: str | I18nStr | None = None,
    tags: list[str] | None = None,
    operation_id: str | None = None,
    deprecated: bool = False,
    responses: OpenAPIMetaResponse | None = None,
    security: list[dict[str, list[str]]] | None = None,
    external_docs: dict[str, str] | None = None,
    language: str | None = None,
    prefix_config: ConventionalPrefixConfig | None = None,
    content_type: str | None = None,
    request_content_types: RequestContentTypes | None = None,
    response_content_types: ResponseContentTypes | None = None,
    content_type_resolver: Callable[[Any], str] | None = None,
) -> Callable[[F], F] | F:
    """Decorator to add OpenAPI metadata to a Flask-RESTful Resource endpoint.

    This decorator adds OpenAPI metadata to a Flask-RESTful Resource endpoint and handles
    parameter binding for request data. It automatically binds request body, query parameters,
    path parameters, and file uploads to function parameters based on their type annotations
    and parameter name prefixes.

    Args:
        summary: A short summary of what the operation does.
        description: A verbose explanation of the operation behavior.
        tags: A list of tags for API documentation control.
        operation_id: Unique string used to identify the operation.
        deprecated: Declares this operation to be deprecated.
        responses: The responses the API can return.
        security: A declaration of which security mechanisms can be used for this operation.
        external_docs: Additional external documentation.
        language: Language code to use for I18nString values (default: current language).
        prefix_config: Configuration object for parameter prefixes.
        content_type: Custom content type for request body. If None, will be auto-detected.
        request_content_types: Multiple content types for request body.
        response_content_types: Multiple content types for response body.
        content_type_resolver: Function to determine content type based on request.


    Returns:
        The decorated function with OpenAPI metadata attached.

    Examples:
        >>> from flask_restful import Resource
        >>> from flask_x_openapi_schema.x.flask_restful import openapi_metadata
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
        >>> class ItemResource(Resource):
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
    return FlaskRestfulOpenAPIDecorator(
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

## Resources

Extension for the Flask-RESTful Api class to collect OpenAPI metadata.

This module provides mixins and utilities to integrate Flask-RESTful with OpenAPI schema generation. It extends Flask-RESTful's Api class to add OpenAPI schema generation capabilities, tracking resources added to the API and providing methods to generate OpenAPI schemas.

Examples:

Basic usage with Flask-RESTful:

```pycon
>>> from flask import Flask
>>> from flask_restful import Resource
>>> from flask_x_openapi_schema.x.flask_restful import OpenAPIIntegrationMixin, openapi_metadata
>>> from pydantic import BaseModel, Field
>>>
>>> app = Flask(__name__)
>>>
>>> class OpenAPIApi(OpenAPIIntegrationMixin):
...     pass
>>>
>>> api = OpenAPIApi(app)
>>>
>>> class ItemResource(Resource):
...     @openapi_metadata(summary="Get an item")
...     def get(self, item_id):
...         return {"id": item_id, "name": "Example Item"}
>>>
>>> api.add_resource(ItemResource, "/items/<item_id>")
>>>
>>> # Route to serve the OpenAPI schema
>>> schema = api.generate_openapi_schema(title="My API", version="1.0.0", description="API for managing items")

```

#### `OpenAPIBlueprintMixin`

A mixin class for Flask Blueprint to collect OpenAPI metadata from MethodView classes.

This mixin extends Flask's Blueprint class to add OpenAPI schema generation capabilities for MethodView classes. It tracks MethodView classes registered to the blueprint and provides methods to generate OpenAPI schemas.

Examples:

```pycon
>>> from flask import Blueprint, Flask
>>> from flask.views import MethodView
>>> from flask_x_openapi_schema.x.flask_restful import OpenAPIBlueprintMixin
>>> from flask_x_openapi_schema.x.flask import openapi_metadata, OpenAPIMethodViewMixin
>>>
>>> app = Flask(__name__)
>>>
>>> class OpenAPIBlueprint(OpenAPIBlueprintMixin, Blueprint):
...     pass
>>>
>>> bp = OpenAPIBlueprint("api", __name__, url_prefix="/api")
>>>
>>> class ItemView(OpenAPIMethodViewMixin, MethodView):
...     @openapi_metadata(summary="Get an item")
...     def get(self, item_id):
...         return {"id": item_id, "name": "Example Item"}
>>>
>>> # Register the view to the blueprint (returns a view function)
>>> view_func = ItemView.register_to_blueprint(bp, "/items/<item_id>")
>>>
>>> app.register_blueprint(bp)
>>>
>>> # Generate OpenAPI schema
>>> schema = bp.generate_openapi_schema(title="My API", version="1.0.0", description="API for managing items")

```

Source code in `src/flask_x_openapi_schema/x/flask_restful/resources.py`

```python
class OpenAPIBlueprintMixin:
    """A mixin class for Flask Blueprint to collect OpenAPI metadata from MethodView classes.

    This mixin extends Flask's Blueprint class to add OpenAPI schema generation capabilities
    for MethodView classes. It tracks MethodView classes registered to the blueprint and
    provides methods to generate OpenAPI schemas.

    Examples:
        >>> from flask import Blueprint, Flask
        >>> from flask.views import MethodView
        >>> from flask_x_openapi_schema.x.flask_restful import OpenAPIBlueprintMixin
        >>> from flask_x_openapi_schema.x.flask import openapi_metadata, OpenAPIMethodViewMixin
        >>>
        >>> app = Flask(__name__)
        >>>
        >>> class OpenAPIBlueprint(OpenAPIBlueprintMixin, Blueprint):
        ...     pass
        >>>
        >>> bp = OpenAPIBlueprint("api", __name__, url_prefix="/api")
        >>>
        >>> class ItemView(OpenAPIMethodViewMixin, MethodView):
        ...     @openapi_metadata(summary="Get an item")
        ...     def get(self, item_id):
        ...         return {"id": item_id, "name": "Example Item"}
        >>>
        >>> # Register the view to the blueprint (returns a view function)
        >>> view_func = ItemView.register_to_blueprint(bp, "/items/<item_id>")
        >>>
        >>> app.register_blueprint(bp)
        >>>
        >>> # Generate OpenAPI schema
        >>> schema = bp.generate_openapi_schema(title="My API", version="1.0.0", description="API for managing items")

    """

    def configure_openapi(self, *, prefix_config: ConventionalPrefixConfig = None, **kwargs: Any) -> None:
        """Configure OpenAPI settings for this Blueprint instance.

        Args:
            prefix_config: Configuration object with parameter prefixes
            **kwargs: For backward compatibility - will be used to create a config object if prefix_config is None

        """
        if prefix_config is not None:
            configure_prefixes(prefix_config)
        elif kwargs:
            new_config = ConventionalPrefixConfig(
                request_body_prefix=kwargs.get(
                    "request_body_prefix",
                    GLOBAL_CONFIG_HOLDER.get().request_body_prefix,
                ),
                request_query_prefix=kwargs.get(
                    "request_query_prefix",
                    GLOBAL_CONFIG_HOLDER.get().request_query_prefix,
                ),
                request_path_prefix=kwargs.get(
                    "request_path_prefix",
                    GLOBAL_CONFIG_HOLDER.get().request_path_prefix,
                ),
                request_file_prefix=kwargs.get(
                    "request_file_prefix",
                    GLOBAL_CONFIG_HOLDER.get().request_file_prefix,
                ),
            )
            configure_prefixes(new_config)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the mixin.

        Args:
            *args: Arguments to pass to the parent class.
            **kwargs: Keyword arguments to pass to the parent class.

        """
        super().__init__(*args, **kwargs)

        self._methodview_openapi_resources = []

    def generate_openapi_schema(
        self,
        title: str | I18nStr,
        version: str,
        description: str | I18nStr = "",
        output_format: Literal["json", "yaml"] = "yaml",
        language: str | None = None,
    ) -> Any:
        """Generate an OpenAPI schema for the API.

        Args:
            title: The title of the API (can be an I18nString).
            version: The version of the API.
            description: The description of the API (can be an I18nString).
            output_format: The output format (json or yaml).
            language: The language to use for internationalized strings (default: current language).

        Returns:
            The OpenAPI schema as a dictionary (if json) or string (if yaml).

        """
        current_lang = language or get_current_language()

        generator = MethodViewOpenAPISchemaGenerator(title, version, description, language=current_lang)

        generator.process_methodview_resources(self)

        schema = generator.generate_schema()

        if output_format == "yaml":
            return yaml.dump(schema, sort_keys=False, default_flow_style=False, allow_unicode=True)
        return schema

```

##### `__init__(*args, **kwargs)`

Initialize the mixin.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `*args` | `Any` | Arguments to pass to the parent class. | `()` | | `**kwargs` | `Any` | Keyword arguments to pass to the parent class. | `{}` |

Source code in `src/flask_x_openapi_schema/x/flask_restful/resources.py`

```python
def __init__(self, *args: Any, **kwargs: Any) -> None:
    """Initialize the mixin.

    Args:
        *args: Arguments to pass to the parent class.
        **kwargs: Keyword arguments to pass to the parent class.

    """
    super().__init__(*args, **kwargs)

    self._methodview_openapi_resources = []

```

##### `configure_openapi(*, prefix_config=None, **kwargs)`

Configure OpenAPI settings for this Blueprint instance.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `prefix_config` | `ConventionalPrefixConfig` | Configuration object with parameter prefixes | `None` | | `**kwargs` | `Any` | For backward compatibility - will be used to create a config object if prefix_config is None | `{}` |

Source code in `src/flask_x_openapi_schema/x/flask_restful/resources.py`

```python
def configure_openapi(self, *, prefix_config: ConventionalPrefixConfig = None, **kwargs: Any) -> None:
    """Configure OpenAPI settings for this Blueprint instance.

    Args:
        prefix_config: Configuration object with parameter prefixes
        **kwargs: For backward compatibility - will be used to create a config object if prefix_config is None

    """
    if prefix_config is not None:
        configure_prefixes(prefix_config)
    elif kwargs:
        new_config = ConventionalPrefixConfig(
            request_body_prefix=kwargs.get(
                "request_body_prefix",
                GLOBAL_CONFIG_HOLDER.get().request_body_prefix,
            ),
            request_query_prefix=kwargs.get(
                "request_query_prefix",
                GLOBAL_CONFIG_HOLDER.get().request_query_prefix,
            ),
            request_path_prefix=kwargs.get(
                "request_path_prefix",
                GLOBAL_CONFIG_HOLDER.get().request_path_prefix,
            ),
            request_file_prefix=kwargs.get(
                "request_file_prefix",
                GLOBAL_CONFIG_HOLDER.get().request_file_prefix,
            ),
        )
        configure_prefixes(new_config)

```

##### `generate_openapi_schema(title, version, description='', output_format='yaml', language=None)`

Generate an OpenAPI schema for the API.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `title` | `str | I18nStr` | The title of the API (can be an I18nString). | *required* | | `version` | `str` | The version of the API. | *required* | | `description` | `str | I18nStr` | The description of the API (can be an I18nString). | `''` | | `output_format` | `Literal['json', 'yaml']` | The output format (json or yaml). | `'yaml'` | | `language` | `str | None` | The language to use for internationalized strings (default: current language). | `None` |

Returns:

| Type | Description | | --- | --- | | `Any` | The OpenAPI schema as a dictionary (if json) or string (if yaml). |

Source code in `src/flask_x_openapi_schema/x/flask_restful/resources.py`

```python
def generate_openapi_schema(
    self,
    title: str | I18nStr,
    version: str,
    description: str | I18nStr = "",
    output_format: Literal["json", "yaml"] = "yaml",
    language: str | None = None,
) -> Any:
    """Generate an OpenAPI schema for the API.

    Args:
        title: The title of the API (can be an I18nString).
        version: The version of the API.
        description: The description of the API (can be an I18nString).
        output_format: The output format (json or yaml).
        language: The language to use for internationalized strings (default: current language).

    Returns:
        The OpenAPI schema as a dictionary (if json) or string (if yaml).

    """
    current_lang = language or get_current_language()

    generator = MethodViewOpenAPISchemaGenerator(title, version, description, language=current_lang)

    generator.process_methodview_resources(self)

    schema = generator.generate_schema()

    if output_format == "yaml":
        return yaml.dump(schema, sort_keys=False, default_flow_style=False, allow_unicode=True)
    return schema

```

#### `OpenAPIIntegrationMixin`

Bases: `Api`

A mixin class for the flask-restful Api to collect OpenAPI metadata.

This mixin extends Flask-RESTful's Api class to add OpenAPI schema generation capabilities. It tracks resources added to the API and provides methods to generate OpenAPI schemas.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `*args` | `Any` | Arguments to pass to the parent class. | `()` | | `**kwargs` | `Any` | Keyword arguments to pass to the parent class. | `{}` |

Examples:

```pycon
>>> from flask import Flask
>>> from flask_restful import Resource
>>> from flask_x_openapi_schema.x.flask_restful import OpenAPIIntegrationMixin, openapi_metadata
>>> from pydantic import BaseModel, Field
>>>
>>> app = Flask(__name__)
>>>
>>> class OpenAPIApi(OpenAPIIntegrationMixin):
...     pass
>>>
>>> api = OpenAPIApi(app)
>>>
>>> class ItemResource(Resource):
...     @openapi_metadata(summary="Get an item")
...     def get(self, item_id):
...         return {"id": item_id, "name": "Example Item"}
>>>
>>> api.add_resource(ItemResource, "/items/<item_id>")
>>>
>>> # Generate OpenAPI schema
>>> schema = api.generate_openapi_schema(title="My API", version="1.0.0", description="API for managing items")

```

Source code in `src/flask_x_openapi_schema/x/flask_restful/resources.py`

```python
class OpenAPIIntegrationMixin(Api):
    """A mixin class for the flask-restful Api to collect OpenAPI metadata.

    This mixin extends Flask-RESTful's Api class to add OpenAPI schema generation capabilities.
    It tracks resources added to the API and provides methods to generate OpenAPI schemas.

    Args:
        *args: Arguments to pass to the parent class.
        **kwargs: Keyword arguments to pass to the parent class.

    Examples:
        >>> from flask import Flask
        >>> from flask_restful import Resource
        >>> from flask_x_openapi_schema.x.flask_restful import OpenAPIIntegrationMixin, openapi_metadata
        >>> from pydantic import BaseModel, Field
        >>>
        >>> app = Flask(__name__)
        >>>
        >>> class OpenAPIApi(OpenAPIIntegrationMixin):
        ...     pass
        >>>
        >>> api = OpenAPIApi(app)
        >>>
        >>> class ItemResource(Resource):
        ...     @openapi_metadata(summary="Get an item")
        ...     def get(self, item_id):
        ...         return {"id": item_id, "name": "Example Item"}
        >>>
        >>> api.add_resource(ItemResource, "/items/<item_id>")
        >>>
        >>> # Generate OpenAPI schema
        >>> schema = api.generate_openapi_schema(title="My API", version="1.0.0", description="API for managing items")

    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the mixin.

        Args:
            *args: Arguments to pass to the parent class.
            **kwargs: Keyword arguments to pass to the parent class.

        """
        super().__init__(*args, **kwargs)

        if not hasattr(self, "resources"):
            self.resources = []

    def add_resource(self, resource: Any, *urls: str, **kwargs: Any) -> Any:
        """Add a resource to the API and register it for OpenAPI schema generation.

        Args:
            resource: The resource class.
            *urls: The URLs to register the resource with.
            **kwargs: Additional arguments to pass to the parent method.

        Returns:
            The result of the parent method.

        """
        result = super().add_resource(resource, *urls, **kwargs)

        if not hasattr(self, "resources"):
            self.resources = []

        for existing_resource, existing_urls, _ in self.resources:
            if existing_resource == resource and set(existing_urls) == set(urls):
                return result

        if "endpoint" not in kwargs and kwargs is not None:
            kwargs["endpoint"] = resource.__name__.lower()
        elif kwargs is None:
            kwargs = {"endpoint": resource.__name__.lower()}

        self.resources.append((resource, urls, kwargs))

        return result

    def configure_openapi(self, *, prefix_config: ConventionalPrefixConfig = None, **kwargs: Any) -> None:
        """Configure OpenAPI settings for this API instance.

        Args:
            prefix_config: Configuration object with parameter prefixes
            **kwargs: For backward compatibility - will be used to create a config object if prefix_config is None

        """
        if prefix_config is not None:
            configure_prefixes(prefix_config)
        elif kwargs:
            new_config = ConventionalPrefixConfig(
                request_body_prefix=kwargs.get(
                    "request_body_prefix",
                    GLOBAL_CONFIG_HOLDER.get().request_body_prefix,
                ),
                request_query_prefix=kwargs.get(
                    "request_query_prefix",
                    GLOBAL_CONFIG_HOLDER.get().request_query_prefix,
                ),
                request_path_prefix=kwargs.get(
                    "request_path_prefix",
                    GLOBAL_CONFIG_HOLDER.get().request_path_prefix,
                ),
                request_file_prefix=kwargs.get(
                    "request_file_prefix",
                    GLOBAL_CONFIG_HOLDER.get().request_file_prefix,
                ),
            )
            configure_prefixes(new_config)

    def generate_openapi_schema(
        self,
        title: str | I18nStr,
        version: str,
        description: str | I18nStr = "",
        output_format: Literal["json", "yaml"] = "yaml",
        language: str | None = None,
    ) -> Any:
        """Generate an OpenAPI schema for the API.

        This method generates an OpenAPI schema for all resources registered with the API.
        It supports internationalization through I18nStr objects and can output the schema
        in either JSON or YAML format.

        Args:
            title: The title of the API (can be an I18nString).
            version: The version of the API.
            description: The description of the API (can be an I18nString).
            output_format: The output format (json or yaml).
            language: The language to use for internationalized strings (default: current language).

        Returns:
            The OpenAPI schema as a dictionary (if json) or string (if yaml).

        Examples:
            >>> from flask import Flask
            >>> from flask_restful import Resource
            >>> from flask_x_openapi_schema.x.flask_restful import OpenAPIIntegrationMixin, openapi_metadata
            >>> app = Flask(__name__)
            >>> class OpenAPIApi(OpenAPIIntegrationMixin):
            ...     pass
            >>> api = OpenAPIApi(app)
            >>> yaml_schema = api.generate_openapi_schema(
            ...     title="My API", version="1.0.0", description="API for managing items"
            ... )
            >>>
            >>> json_schema = api.generate_openapi_schema(
            ...     title="My API", version="1.0.0", description="API for managing items", output_format="json"
            ... )
            >>>
            >>> from flask_x_openapi_schema import I18nStr
            >>> i18n_schema = api.generate_openapi_schema(
            ...     title=I18nStr({"en-US": "My API", "zh-Hans": "我的API"}),
            ...     version="1.0.0",
            ...     description=I18nStr({"en-US": "API for managing items", "zh-Hans": "用于管理项目的API"}),
            ...     language="zh-Hans",
            ... )

        """
        current_lang = language or get_current_language()

        generator = OpenAPISchemaGenerator(title, version, description, language=current_lang)

        url_prefix = None
        if hasattr(self, "blueprint") and hasattr(self.blueprint, "url_prefix"):
            url_prefix = self.blueprint.url_prefix

        for resource, urls, _ in self.resources:
            generator._process_resource(resource, urls, url_prefix)

        schema = generator.generate_schema()

        if output_format == "yaml":
            return yaml.dump(schema, sort_keys=False, default_flow_style=False, allow_unicode=True)
        return schema

```

##### `__init__(*args, **kwargs)`

Initialize the mixin.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `*args` | `Any` | Arguments to pass to the parent class. | `()` | | `**kwargs` | `Any` | Keyword arguments to pass to the parent class. | `{}` |

Source code in `src/flask_x_openapi_schema/x/flask_restful/resources.py`

```python
def __init__(self, *args: Any, **kwargs: Any) -> None:
    """Initialize the mixin.

    Args:
        *args: Arguments to pass to the parent class.
        **kwargs: Keyword arguments to pass to the parent class.

    """
    super().__init__(*args, **kwargs)

    if not hasattr(self, "resources"):
        self.resources = []

```

##### `add_resource(resource, *urls, **kwargs)`

Add a resource to the API and register it for OpenAPI schema generation.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `resource` | `Any` | The resource class. | *required* | | `*urls` | `str` | The URLs to register the resource with. | `()` | | `**kwargs` | `Any` | Additional arguments to pass to the parent method. | `{}` |

Returns:

| Type | Description | | --- | --- | | `Any` | The result of the parent method. |

Source code in `src/flask_x_openapi_schema/x/flask_restful/resources.py`

```python
def add_resource(self, resource: Any, *urls: str, **kwargs: Any) -> Any:
    """Add a resource to the API and register it for OpenAPI schema generation.

    Args:
        resource: The resource class.
        *urls: The URLs to register the resource with.
        **kwargs: Additional arguments to pass to the parent method.

    Returns:
        The result of the parent method.

    """
    result = super().add_resource(resource, *urls, **kwargs)

    if not hasattr(self, "resources"):
        self.resources = []

    for existing_resource, existing_urls, _ in self.resources:
        if existing_resource == resource and set(existing_urls) == set(urls):
            return result

    if "endpoint" not in kwargs and kwargs is not None:
        kwargs["endpoint"] = resource.__name__.lower()
    elif kwargs is None:
        kwargs = {"endpoint": resource.__name__.lower()}

    self.resources.append((resource, urls, kwargs))

    return result

```

##### `configure_openapi(*, prefix_config=None, **kwargs)`

Configure OpenAPI settings for this API instance.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `prefix_config` | `ConventionalPrefixConfig` | Configuration object with parameter prefixes | `None` | | `**kwargs` | `Any` | For backward compatibility - will be used to create a config object if prefix_config is None | `{}` |

Source code in `src/flask_x_openapi_schema/x/flask_restful/resources.py`

```python
def configure_openapi(self, *, prefix_config: ConventionalPrefixConfig = None, **kwargs: Any) -> None:
    """Configure OpenAPI settings for this API instance.

    Args:
        prefix_config: Configuration object with parameter prefixes
        **kwargs: For backward compatibility - will be used to create a config object if prefix_config is None

    """
    if prefix_config is not None:
        configure_prefixes(prefix_config)
    elif kwargs:
        new_config = ConventionalPrefixConfig(
            request_body_prefix=kwargs.get(
                "request_body_prefix",
                GLOBAL_CONFIG_HOLDER.get().request_body_prefix,
            ),
            request_query_prefix=kwargs.get(
                "request_query_prefix",
                GLOBAL_CONFIG_HOLDER.get().request_query_prefix,
            ),
            request_path_prefix=kwargs.get(
                "request_path_prefix",
                GLOBAL_CONFIG_HOLDER.get().request_path_prefix,
            ),
            request_file_prefix=kwargs.get(
                "request_file_prefix",
                GLOBAL_CONFIG_HOLDER.get().request_file_prefix,
            ),
        )
        configure_prefixes(new_config)

```

##### `generate_openapi_schema(title, version, description='', output_format='yaml', language=None)`

Generate an OpenAPI schema for the API.

This method generates an OpenAPI schema for all resources registered with the API. It supports internationalization through I18nStr objects and can output the schema in either JSON or YAML format.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `title` | `str | I18nStr` | The title of the API (can be an I18nString). | *required* | | `version` | `str` | The version of the API. | *required* | | `description` | `str | I18nStr` | The description of the API (can be an I18nString). | `''` | | `output_format` | `Literal['json', 'yaml']` | The output format (json or yaml). | `'yaml'` | | `language` | `str | None` | The language to use for internationalized strings (default: current language). | `None` |

Returns:

| Type | Description | | --- | --- | | `Any` | The OpenAPI schema as a dictionary (if json) or string (if yaml). |

Examples:

```pycon
>>> from flask import Flask
>>> from flask_restful import Resource
>>> from flask_x_openapi_schema.x.flask_restful import OpenAPIIntegrationMixin, openapi_metadata
>>> app = Flask(__name__)
>>> class OpenAPIApi(OpenAPIIntegrationMixin):
...     pass
>>> api = OpenAPIApi(app)
>>> yaml_schema = api.generate_openapi_schema(
...     title="My API", version="1.0.0", description="API for managing items"
... )
>>>
>>> json_schema = api.generate_openapi_schema(
...     title="My API", version="1.0.0", description="API for managing items", output_format="json"
... )
>>>
>>> from flask_x_openapi_schema import I18nStr
>>> i18n_schema = api.generate_openapi_schema(
...     title=I18nStr({"en-US": "My API", "zh-Hans": "我的API"}),
...     version="1.0.0",
...     description=I18nStr({"en-US": "API for managing items", "zh-Hans": "用于管理项目的API"}),
...     language="zh-Hans",
... )

```

Source code in `src/flask_x_openapi_schema/x/flask_restful/resources.py`

```python
def generate_openapi_schema(
    self,
    title: str | I18nStr,
    version: str,
    description: str | I18nStr = "",
    output_format: Literal["json", "yaml"] = "yaml",
    language: str | None = None,
) -> Any:
    """Generate an OpenAPI schema for the API.

    This method generates an OpenAPI schema for all resources registered with the API.
    It supports internationalization through I18nStr objects and can output the schema
    in either JSON or YAML format.

    Args:
        title: The title of the API (can be an I18nString).
        version: The version of the API.
        description: The description of the API (can be an I18nString).
        output_format: The output format (json or yaml).
        language: The language to use for internationalized strings (default: current language).

    Returns:
        The OpenAPI schema as a dictionary (if json) or string (if yaml).

    Examples:
        >>> from flask import Flask
        >>> from flask_restful import Resource
        >>> from flask_x_openapi_schema.x.flask_restful import OpenAPIIntegrationMixin, openapi_metadata
        >>> app = Flask(__name__)
        >>> class OpenAPIApi(OpenAPIIntegrationMixin):
        ...     pass
        >>> api = OpenAPIApi(app)
        >>> yaml_schema = api.generate_openapi_schema(
        ...     title="My API", version="1.0.0", description="API for managing items"
        ... )
        >>>
        >>> json_schema = api.generate_openapi_schema(
        ...     title="My API", version="1.0.0", description="API for managing items", output_format="json"
        ... )
        >>>
        >>> from flask_x_openapi_schema import I18nStr
        >>> i18n_schema = api.generate_openapi_schema(
        ...     title=I18nStr({"en-US": "My API", "zh-Hans": "我的API"}),
        ...     version="1.0.0",
        ...     description=I18nStr({"en-US": "API for managing items", "zh-Hans": "用于管理项目的API"}),
        ...     language="zh-Hans",
        ... )

    """
    current_lang = language or get_current_language()

    generator = OpenAPISchemaGenerator(title, version, description, language=current_lang)

    url_prefix = None
    if hasattr(self, "blueprint") and hasattr(self.blueprint, "url_prefix"):
        url_prefix = self.blueprint.url_prefix

    for resource, urls, _ in self.resources:
        generator._process_resource(resource, urls, url_prefix)

    schema = generator.generate_schema()

    if output_format == "yaml":
        return yaml.dump(schema, sort_keys=False, default_flow_style=False, allow_unicode=True)
    return schema

```

## Utilities

Utilities for Flask-RESTful integration.

This module provides utilities for integrating Pydantic models with Flask-RESTful, enabling automatic conversion of Pydantic models to Flask-RESTful RequestParser objects.

The main functionality allows for seamless integration between Pydantic's validation capabilities and Flask-RESTful's request parsing system.

#### `create_reqparse_from_pydantic(model, location='json', bundle_errors=True)`

Create a Flask-RESTful RequestParser from a Pydantic model.

Converts a Pydantic model into a Flask-RESTful RequestParser, mapping Pydantic field types to appropriate Python types for request parsing. Handles basic types as well as lists (arrays) and preserves field descriptions and required status.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `model` | `type[BaseModel]` | The Pydantic model class to convert to a RequestParser. | *required* | | `location` | `str` | The location to look for arguments. Options include 'json', 'form', 'args', 'headers', etc. Defaults to 'json'. | `'json'` | | `bundle_errors` | `bool` | Whether to bundle all errors in a single response. When False, the first error is returned. Defaults to True. | `True` |

Returns:

| Type | Description | | --- | --- | | `RequestParser` | reqparse.RequestParser: A configured Flask-RESTful RequestParser instance that can be used to parse and validate incoming requests. |

Examples:

```pycon
>>> from pydantic import BaseModel, Field
>>> from flask_restful import reqparse
>>> class UserModel(BaseModel):
...     name: str = Field(..., description="User's full name")
...     age: int = Field(..., description="User's age in years")
...     tags: list[str] = Field([], description="User tags")
>>> parser = create_reqparse_from_pydantic(UserModel)
>>> isinstance(parser, reqparse.RequestParser)
True

```

Source code in `src/flask_x_openapi_schema/x/flask_restful/utils.py`

```python
def create_reqparse_from_pydantic(
    model: type[BaseModel], location: str = "json", bundle_errors: bool = True
) -> reqparse.RequestParser:
    """Create a Flask-RESTful RequestParser from a Pydantic model.

    Converts a Pydantic model into a Flask-RESTful RequestParser, mapping Pydantic
    field types to appropriate Python types for request parsing. Handles basic types
    as well as lists (arrays) and preserves field descriptions and required status.

    Args:
        model: The Pydantic model class to convert to a RequestParser.
        location: The location to look for arguments. Options include 'json',
            'form', 'args', 'headers', etc. Defaults to 'json'.
        bundle_errors: Whether to bundle all errors in a single response.
            When False, the first error is returned. Defaults to True.

    Returns:
        reqparse.RequestParser: A configured Flask-RESTful RequestParser instance
            that can be used to parse and validate incoming requests.

    Examples:
        >>> from pydantic import BaseModel, Field
        >>> from flask_restful import reqparse
        >>> class UserModel(BaseModel):
        ...     name: str = Field(..., description="User's full name")
        ...     age: int = Field(..., description="User's age in years")
        ...     tags: list[str] = Field([], description="User tags")
        >>> parser = create_reqparse_from_pydantic(UserModel)
        >>> isinstance(parser, reqparse.RequestParser)
        True

    """
    parser = reqparse.RequestParser(bundle_errors=bundle_errors)

    schema = model.model_json_schema()
    properties = schema.get("properties", {})
    required = schema.get("required", [])

    for field_name, field_schema in properties.items():
        field_type = field_schema.get("type")
        field_description = field_schema.get("description", "")
        field_required = field_name in required

        type_mapping = {
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
            "array": list,
            "object": dict,
        }

        python_type = type_mapping.get(field_type, str)

        if field_type == "array":
            items = field_schema.get("items", {})
            item_type = items.get("type", "string")
            python_item_type = type_mapping.get(item_type, str)

            parser.add_argument(
                field_name,
                type=python_item_type,
                action="append",
                required=field_required,
                help=field_description,
                location=location,
            )
        else:
            parser.add_argument(
                field_name,
                type=python_type,
                required=field_required,
                help=field_description,
                location=location,
            )

    return parser

```
