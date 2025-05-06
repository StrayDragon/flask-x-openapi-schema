# Core Modules

This section provides documentation for the core components of Flask-X-OpenAPI-Schema.

## Configuration

Configuration management for OpenAPI schema generation.

This module provides configuration classes and utilities for managing parameter prefixes and other settings for OpenAPI schema generation.

Includes classes for managing conventional parameter prefixes, caching behavior, and OpenAPI schema generation settings, along with thread-safe global configuration.

#### `CacheConfig`

Configuration class for caching behavior.

This class holds configuration settings for controlling cache behavior in the library.

Attributes:

| Name | Type | Description | | --- | --- | --- | | `enabled` | `bool` | Global flag to enable/disable function metadata caching (default: True) |

Source code in `src/flask_x_openapi_schema/core/config.py`

```python
@dataclass(frozen=True)
class CacheConfig:
    """Configuration class for caching behavior.

    This class holds configuration settings for controlling cache behavior
    in the library.

    Attributes:
        enabled: Global flag to enable/disable function metadata caching (default: True)

    """

    enabled: bool = True

```

#### `ConventionalPrefixConfig`

Configuration class for OpenAPI parameter prefixes.

This class holds configuration settings for parameter prefixes used in binding request data to function parameters.

Attributes:

| Name | Type | Description | | --- | --- | --- | | `request_body_prefix` | `str` | Prefix for request body parameters (default: "\_x_body") | | `request_query_prefix` | `str` | Prefix for query parameters (default: "\_x_query") | | `request_path_prefix` | `str` | Prefix for path parameters (default: "\_x_path") | | `request_file_prefix` | `str` | Prefix for file parameters (default: "\_x_file") | | `extra_options` | `dict[str, Any]` | Additional configuration options |

Examples:

```pycon
>>> from flask_x_openapi_schema import ConventionalPrefixConfig
>>> config = ConventionalPrefixConfig(
...     request_body_prefix="req_body",
...     request_query_prefix="req_query",
...     request_path_prefix="req_path",
...     request_file_prefix="req_file",
... )

```

Source code in `src/flask_x_openapi_schema/core/config.py`

```python
@dataclass(frozen=True)
class ConventionalPrefixConfig:
    """Configuration class for OpenAPI parameter prefixes.

    This class holds configuration settings for parameter prefixes used in
    binding request data to function parameters.

    Attributes:
        request_body_prefix: Prefix for request body parameters (default: "_x_body")
        request_query_prefix: Prefix for query parameters (default: "_x_query")
        request_path_prefix: Prefix for path parameters (default: "_x_path")
        request_file_prefix: Prefix for file parameters (default: "_x_file")
        extra_options: Additional configuration options

    Examples:
        >>> from flask_x_openapi_schema import ConventionalPrefixConfig
        >>> config = ConventionalPrefixConfig(
        ...     request_body_prefix="req_body",
        ...     request_query_prefix="req_query",
        ...     request_path_prefix="req_path",
        ...     request_file_prefix="req_file",
        ... )

    """

    request_body_prefix: str = DEFAULT_BODY_PREFIX
    request_query_prefix: str = DEFAULT_QUERY_PREFIX
    request_path_prefix: str = DEFAULT_PATH_PREFIX
    request_file_prefix: str = DEFAULT_FILE_PREFIX
    extra_options: dict[str, Any] = field(default_factory=dict)

```

#### `OpenAPIConfig`

Configuration class for OpenAPI schema generation.

This class holds configuration settings for OpenAPI schema generation.

Attributes:

| Name | Type | Description | | --- | --- | --- | | `title` | `str` | API title | | `version` | `str` | API version | | `description` | `str` | API description | | `prefix_config` | `ConventionalPrefixConfig` | Parameter prefix configuration | | `security_schemes` | `dict[str, dict[str, Any]]` | Security schemes configuration | | `openapi_version` | `str` | OpenAPI specification version | | `servers` | `list[dict[str, Any]]` | List of server objects | | `external_docs` | `dict[str, Any] | None` | External documentation | | `webhooks` | `dict[str, dict[str, Any]]` | Webhook definitions | | `json_schema_dialect` | `str | None` | JSON Schema dialect | | `cache_config` | `CacheConfig` | Configuration for caching behavior |

Source code in `src/flask_x_openapi_schema/core/config.py`

```python
@dataclass(frozen=True)
class OpenAPIConfig:
    """Configuration class for OpenAPI schema generation.

    This class holds configuration settings for OpenAPI schema generation.

    Attributes:
        title: API title
        version: API version
        description: API description
        prefix_config: Parameter prefix configuration
        security_schemes: Security schemes configuration
        openapi_version: OpenAPI specification version
        servers: List of server objects
        external_docs: External documentation
        webhooks: Webhook definitions
        json_schema_dialect: JSON Schema dialect
        cache_config: Configuration for caching behavior

    """

    title: str = DEFAULT_TITLE
    version: str = DEFAULT_VERSION
    description: str = DEFAULT_DESCRIPTION
    prefix_config: ConventionalPrefixConfig = field(default_factory=ConventionalPrefixConfig)
    security_schemes: dict[str, dict[str, Any]] = field(default_factory=dict)
    openapi_version: str = "3.1.0"
    servers: list[dict[str, Any]] = field(default_factory=list)
    external_docs: dict[str, Any] | None = None
    webhooks: dict[str, dict[str, Any]] = field(default_factory=dict)
    json_schema_dialect: str | None = None
    cache_config: CacheConfig = field(default_factory=CacheConfig)

```

#### `ThreadSafeConfig`

Thread-safe configuration holder.

This class provides thread-safe access to configuration settings.

Source code in `src/flask_x_openapi_schema/core/config.py`

```python
class ThreadSafeConfig:
    """Thread-safe configuration holder.

    This class provides thread-safe access to configuration settings.
    """

    def __init__(self) -> None:  # noqa: D107
        self._prefix_config = ConventionalPrefixConfig()
        self._openapi_config = OpenAPIConfig()
        self._cache_config = CacheConfig(enabled=True)
        self._lock = threading.RLock()

    def get(self) -> ConventionalPrefixConfig:
        """Get the current prefix configuration.

        Returns:
            ConventionalPrefixConfig: Current prefix configuration

        """
        with self._lock:
            # Return a copy to prevent modification
            return ConventionalPrefixConfig(
                request_body_prefix=self._prefix_config.request_body_prefix,
                request_query_prefix=self._prefix_config.request_query_prefix,
                request_path_prefix=self._prefix_config.request_path_prefix,
                request_file_prefix=self._prefix_config.request_file_prefix,
                extra_options=dict(self._prefix_config.extra_options),
            )

    def get_cache_config(self) -> CacheConfig:
        """Get the current cache configuration.

        Returns:
            CacheConfig: Current cache configuration

        """
        with self._lock:
            # Return a copy to prevent modification
            return CacheConfig(
                enabled=self._cache_config.enabled,
            )

    def get_openapi_config(self) -> OpenAPIConfig:
        """Get the current OpenAPI configuration.

        Returns:
            OpenAPIConfig: Current OpenAPI configuration

        """
        with self._lock:
            # Return a copy to prevent modification
            return OpenAPIConfig(
                title=self._openapi_config.title,
                version=self._openapi_config.version,
                description=self._openapi_config.description,
                prefix_config=self.get(),
                security_schemes=dict(self._openapi_config.security_schemes),
                openapi_version=self._openapi_config.openapi_version,
                servers=[dict(server) for server in self._openapi_config.servers]
                if self._openapi_config.servers
                else [],
                external_docs=dict(self._openapi_config.external_docs) if self._openapi_config.external_docs else None,
                webhooks=dict(self._openapi_config.webhooks) if self._openapi_config.webhooks else {},
                json_schema_dialect=self._openapi_config.json_schema_dialect,
                cache_config=self.get_cache_config(),
            )

    def set(self, config: ConventionalPrefixConfig) -> None:
        """Set a new prefix configuration.

        Args:
            config: New prefix configuration

        """
        with self._lock:
            self._prefix_config = ConventionalPrefixConfig(
                request_body_prefix=config.request_body_prefix,
                request_query_prefix=config.request_query_prefix,
                request_path_prefix=config.request_path_prefix,
                request_file_prefix=config.request_file_prefix,
                extra_options=dict(config.extra_options),
            )

    def set_openapi_config(self, config: OpenAPIConfig) -> None:
        """Set a new OpenAPI configuration.

        Args:
            config: New OpenAPI configuration

        """
        with self._lock:
            self._openapi_config = OpenAPIConfig(
                title=config.title,
                version=config.version,
                description=config.description,
                prefix_config=config.prefix_config,
                security_schemes=dict(config.security_schemes),
                openapi_version=config.openapi_version,
                servers=[dict(server) for server in config.servers] if config.servers else [],
                external_docs=dict(config.external_docs) if config.external_docs else None,
                webhooks=dict(config.webhooks) if config.webhooks else {},
                json_schema_dialect=config.json_schema_dialect,
                cache_config=config.cache_config,
            )
            # Also update prefix config
            self.set(config.prefix_config)
            # Also update cache config
            self.set_cache_config(config.cache_config)

    def set_cache_config(self, config: CacheConfig) -> None:
        """Set a new cache configuration.

        Args:
            config: New cache configuration

        """
        with self._lock:
            self._cache_config = CacheConfig(
                enabled=config.enabled,
            )

    def reset(self) -> None:
        """Reset to default prefix configuration.

        Returns:
            None

        """
        with self._lock:
            self._prefix_config = ConventionalPrefixConfig(
                request_body_prefix=DEFAULT_BODY_PREFIX,
                request_query_prefix=DEFAULT_QUERY_PREFIX,
                request_path_prefix=DEFAULT_PATH_PREFIX,
                request_file_prefix=DEFAULT_FILE_PREFIX,
                extra_options={},
            )

    def reset_all(self) -> None:
        """Reset all configurations to defaults.

        Returns:
            None

        """
        with self._lock:
            self.reset()
            self._openapi_config = OpenAPIConfig()
            self._cache_config = CacheConfig(enabled=True)

```

##### `get()`

Get the current prefix configuration.

Returns:

| Name | Type | Description | | --- | --- | --- | | `ConventionalPrefixConfig` | `ConventionalPrefixConfig` | Current prefix configuration |

Source code in `src/flask_x_openapi_schema/core/config.py`

```python
def get(self) -> ConventionalPrefixConfig:
    """Get the current prefix configuration.

    Returns:
        ConventionalPrefixConfig: Current prefix configuration

    """
    with self._lock:
        # Return a copy to prevent modification
        return ConventionalPrefixConfig(
            request_body_prefix=self._prefix_config.request_body_prefix,
            request_query_prefix=self._prefix_config.request_query_prefix,
            request_path_prefix=self._prefix_config.request_path_prefix,
            request_file_prefix=self._prefix_config.request_file_prefix,
            extra_options=dict(self._prefix_config.extra_options),
        )

```

##### `get_cache_config()`

Get the current cache configuration.

Returns:

| Name | Type | Description | | --- | --- | --- | | `CacheConfig` | `CacheConfig` | Current cache configuration |

Source code in `src/flask_x_openapi_schema/core/config.py`

```python
def get_cache_config(self) -> CacheConfig:
    """Get the current cache configuration.

    Returns:
        CacheConfig: Current cache configuration

    """
    with self._lock:
        # Return a copy to prevent modification
        return CacheConfig(
            enabled=self._cache_config.enabled,
        )

```

##### `get_openapi_config()`

Get the current OpenAPI configuration.

Returns:

| Name | Type | Description | | --- | --- | --- | | `OpenAPIConfig` | `OpenAPIConfig` | Current OpenAPI configuration |

Source code in `src/flask_x_openapi_schema/core/config.py`

```python
def get_openapi_config(self) -> OpenAPIConfig:
    """Get the current OpenAPI configuration.

    Returns:
        OpenAPIConfig: Current OpenAPI configuration

    """
    with self._lock:
        # Return a copy to prevent modification
        return OpenAPIConfig(
            title=self._openapi_config.title,
            version=self._openapi_config.version,
            description=self._openapi_config.description,
            prefix_config=self.get(),
            security_schemes=dict(self._openapi_config.security_schemes),
            openapi_version=self._openapi_config.openapi_version,
            servers=[dict(server) for server in self._openapi_config.servers]
            if self._openapi_config.servers
            else [],
            external_docs=dict(self._openapi_config.external_docs) if self._openapi_config.external_docs else None,
            webhooks=dict(self._openapi_config.webhooks) if self._openapi_config.webhooks else {},
            json_schema_dialect=self._openapi_config.json_schema_dialect,
            cache_config=self.get_cache_config(),
        )

```

##### `reset()`

Reset to default prefix configuration.

Returns:

| Type | Description | | --- | --- | | `None` | None |

Source code in `src/flask_x_openapi_schema/core/config.py`

```python
def reset(self) -> None:
    """Reset to default prefix configuration.

    Returns:
        None

    """
    with self._lock:
        self._prefix_config = ConventionalPrefixConfig(
            request_body_prefix=DEFAULT_BODY_PREFIX,
            request_query_prefix=DEFAULT_QUERY_PREFIX,
            request_path_prefix=DEFAULT_PATH_PREFIX,
            request_file_prefix=DEFAULT_FILE_PREFIX,
            extra_options={},
        )

```

##### `reset_all()`

Reset all configurations to defaults.

Returns:

| Type | Description | | --- | --- | | `None` | None |

Source code in `src/flask_x_openapi_schema/core/config.py`

```python
def reset_all(self) -> None:
    """Reset all configurations to defaults.

    Returns:
        None

    """
    with self._lock:
        self.reset()
        self._openapi_config = OpenAPIConfig()
        self._cache_config = CacheConfig(enabled=True)

```

##### `set(config)`

Set a new prefix configuration.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `config` | `ConventionalPrefixConfig` | New prefix configuration | *required* |

Source code in `src/flask_x_openapi_schema/core/config.py`

```python
def set(self, config: ConventionalPrefixConfig) -> None:
    """Set a new prefix configuration.

    Args:
        config: New prefix configuration

    """
    with self._lock:
        self._prefix_config = ConventionalPrefixConfig(
            request_body_prefix=config.request_body_prefix,
            request_query_prefix=config.request_query_prefix,
            request_path_prefix=config.request_path_prefix,
            request_file_prefix=config.request_file_prefix,
            extra_options=dict(config.extra_options),
        )

```

##### `set_cache_config(config)`

Set a new cache configuration.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `config` | `CacheConfig` | New cache configuration | *required* |

Source code in `src/flask_x_openapi_schema/core/config.py`

```python
def set_cache_config(self, config: CacheConfig) -> None:
    """Set a new cache configuration.

    Args:
        config: New cache configuration

    """
    with self._lock:
        self._cache_config = CacheConfig(
            enabled=config.enabled,
        )

```

##### `set_openapi_config(config)`

Set a new OpenAPI configuration.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `config` | `OpenAPIConfig` | New OpenAPI configuration | *required* |

Source code in `src/flask_x_openapi_schema/core/config.py`

```python
def set_openapi_config(self, config: OpenAPIConfig) -> None:
    """Set a new OpenAPI configuration.

    Args:
        config: New OpenAPI configuration

    """
    with self._lock:
        self._openapi_config = OpenAPIConfig(
            title=config.title,
            version=config.version,
            description=config.description,
            prefix_config=config.prefix_config,
            security_schemes=dict(config.security_schemes),
            openapi_version=config.openapi_version,
            servers=[dict(server) for server in config.servers] if config.servers else [],
            external_docs=dict(config.external_docs) if config.external_docs else None,
            webhooks=dict(config.webhooks) if config.webhooks else {},
            json_schema_dialect=config.json_schema_dialect,
            cache_config=config.cache_config,
        )
        # Also update prefix config
        self.set(config.prefix_config)
        # Also update cache config
        self.set_cache_config(config.cache_config)

```

#### `configure_cache(config)`

Configure global cache settings.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `config` | `CacheConfig` | Configuration object with cache settings | *required* |

Examples:

```pycon
>>> from flask_x_openapi_schema import CacheConfig, configure_cache
>>> cache_config = CacheConfig(enabled=True)
>>> configure_cache(cache_config)

```

Source code in `src/flask_x_openapi_schema/core/config.py`

```python
def configure_cache(config: CacheConfig) -> None:
    """Configure global cache settings.

    Args:
        config: Configuration object with cache settings

    Examples:
        >>> from flask_x_openapi_schema import CacheConfig, configure_cache
        >>> cache_config = CacheConfig(enabled=True)
        >>> configure_cache(cache_config)

    """
    # Update the configuration in a thread-safe manner
    GLOBAL_CONFIG_HOLDER.set_cache_config(config)

```

#### `configure_openapi(config)`

Configure global OpenAPI settings.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `config` | `OpenAPIConfig` | Configuration object with OpenAPI settings | *required* |

Source code in `src/flask_x_openapi_schema/core/config.py`

```python
def configure_openapi(config: OpenAPIConfig) -> None:
    """Configure global OpenAPI settings.

    Args:
        config: Configuration object with OpenAPI settings

    """
    # Update the configuration in a thread-safe manner
    GLOBAL_CONFIG_HOLDER.set_openapi_config(config)

```

#### `configure_prefixes(config)`

Configure global parameter prefixes.

Sets the global configuration for parameter prefixes used in binding request data to function parameters. This affects all decorators that don't specify their own prefix configuration.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `config` | `ConventionalPrefixConfig` | Configuration object with parameter prefixes | *required* |

Examples:

```pycon
>>> from flask_x_openapi_schema import ConventionalPrefixConfig, configure_prefixes
>>> custom_config = ConventionalPrefixConfig(request_body_prefix="req_body", request_query_prefix="req_query")
>>> configure_prefixes(custom_config)

```

Source code in `src/flask_x_openapi_schema/core/config.py`

```python
def configure_prefixes(config: ConventionalPrefixConfig) -> None:
    """Configure global parameter prefixes.

    Sets the global configuration for parameter prefixes used in binding request data
    to function parameters. This affects all decorators that don't specify their own
    prefix configuration.

    Args:
        config: Configuration object with parameter prefixes

    Examples:
        >>> from flask_x_openapi_schema import ConventionalPrefixConfig, configure_prefixes
        >>> custom_config = ConventionalPrefixConfig(request_body_prefix="req_body", request_query_prefix="req_query")
        >>> configure_prefixes(custom_config)

    """
    # Update the configuration in a thread-safe manner
    GLOBAL_CONFIG_HOLDER.set(config)

```

#### `get_cache_config()`

Get the current cache configuration.

Returns:

| Name | Type | Description | | --- | --- | --- | | `CacheConfig` | `CacheConfig` | Current cache configuration |

Source code in `src/flask_x_openapi_schema/core/config.py`

```python
def get_cache_config() -> CacheConfig:
    """Get the current cache configuration.

    Returns:
        CacheConfig: Current cache configuration

    """
    return GLOBAL_CONFIG_HOLDER.get_cache_config()

```

#### `get_openapi_config()`

Get the current OpenAPI configuration.

Returns:

| Name | Type | Description | | --- | --- | --- | | `OpenAPIConfig` | `OpenAPIConfig` | Current OpenAPI configuration |

Source code in `src/flask_x_openapi_schema/core/config.py`

```python
def get_openapi_config() -> OpenAPIConfig:
    """Get the current OpenAPI configuration.

    Returns:
        OpenAPIConfig: Current OpenAPI configuration

    """
    return GLOBAL_CONFIG_HOLDER.get_openapi_config()

```

#### `reset_all_config()`

Reset all configuration to default values.

Resets all configuration settings to their default values, including parameter prefixes, OpenAPI settings, and cache configuration.

Source code in `src/flask_x_openapi_schema/core/config.py`

```python
def reset_all_config() -> None:
    """Reset all configuration to default values.

    Resets all configuration settings to their default values, including
    parameter prefixes, OpenAPI settings, and cache configuration.
    """
    # Reset the configuration in a thread-safe manner
    GLOBAL_CONFIG_HOLDER.reset_all()

```

#### `reset_prefixes()`

Reset parameter prefixes to default values.

Resets the global parameter prefix configuration to the default values:

- request_body_prefix: "\_x_body"
- request_query_prefix: "\_x_query"
- request_path_prefix: "\_x_path"
- request_file_prefix: "\_x_file"

Examples:

```pycon
>>> from flask_x_openapi_schema import reset_prefixes
>>> reset_prefixes()  # Resets to default prefixes

```

Source code in `src/flask_x_openapi_schema/core/config.py`

```python
def reset_prefixes() -> None:
    """Reset parameter prefixes to default values.

    Resets the global parameter prefix configuration to the default values:
    - request_body_prefix: "_x_body"
    - request_query_prefix: "_x_query"
    - request_path_prefix: "_x_path"
    - request_file_prefix: "_x_file"

    Examples:
        >>> from flask_x_openapi_schema import reset_prefixes
        >>> reset_prefixes()  # Resets to default prefixes

    """
    # Reset the configuration in a thread-safe manner
    GLOBAL_CONFIG_HOLDER.reset()

```

## Cache

Simplified caching mechanism for OpenAPI schema generation.

This module provides a minimal caching system focused only on the essential caching needs for the @openapi_metadata decorator. It uses WeakKeyDictionary to avoid memory leaks when functions are garbage collected.

Cache Types

- WeakKeyDictionary: For function metadata to avoid memory leaks

Thread Safety

This module is designed to be thread-safe for use in multi-threaded web servers.

#### `clear_all_caches()`

Clear all caches to free memory or force regeneration.

This function clears the function metadata cache.

Source code in `src/flask_x_openapi_schema/core/cache.py`

```python
def clear_all_caches() -> None:
    """Clear all caches to free memory or force regeneration.

    This function clears the function metadata cache.
    """
    FUNCTION_METADATA_CACHE.clear()

```

#### `get_parameter_prefixes(config=None)`

Get parameter prefixes from config or global defaults.

This function retrieves parameter prefixes from the provided config or global defaults.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `config` | `Any | None` | Optional configuration object with custom prefixes | `None` |

Returns:

| Type | Description | | --- | --- | | `tuple[str, str, str, str]` | Tuple of (body_prefix, query_prefix, path_prefix, file_prefix) |

Source code in `src/flask_x_openapi_schema/core/cache.py`

```python
def get_parameter_prefixes(config: Any | None = None) -> tuple[str, str, str, str]:
    """Get parameter prefixes from config or global defaults.

    This function retrieves parameter prefixes from the provided config or global defaults.

    Args:
        config: Optional configuration object with custom prefixes

    Returns:
        Tuple of (body_prefix, query_prefix, path_prefix, file_prefix)

    """
    from .config import GLOBAL_CONFIG_HOLDER

    # If config is None, use global config
    prefix_config = GLOBAL_CONFIG_HOLDER.get() if config is None else config

    # Extract the prefixes directly
    return (
        prefix_config.request_body_prefix,
        prefix_config.request_query_prefix,
        prefix_config.request_path_prefix,
        prefix_config.request_file_prefix,
    )

```

## Decorator Base

Base classes and utilities for OpenAPI metadata decorators.

This module provides the core functionality for creating OpenAPI metadata decorators that can be used with Flask and Flask-RESTful applications. It includes utilities for parameter extraction, metadata generation, and request processing.

The main classes are:

- OpenAPIDecoratorBase: Serves as the foundation for framework-specific decorator implementations. It handles parameter binding, metadata caching, and OpenAPI schema generation.
- DecoratorBase: A base class for framework-specific decorators that encapsulates common functionality for processing request bodies, query parameters, and path parameters.

#### `DecoratorBase`

Bases: `ABC`

Base class for framework-specific decorators.

This class encapsulates common functionality for processing request bodies, query parameters, and path parameters. It is designed to be inherited by framework-specific decorator implementations.

Attributes:

| Name | Type | Description | | --- | --- | --- | | `summary` | `str or I18nStr` | Short summary of the endpoint. | | `description` | `str or I18nStr` | Detailed description of the endpoint. | | `tags` | `list` | List of tags to categorize the endpoint. | | `operation_id` | `str` | Unique identifier for the operation. | | `responses` | `OpenAPIMetaResponse` | Response models configuration. | | `deprecated` | `bool` | Whether the endpoint is deprecated. | | `security` | `list` | Security requirements for the endpoint. | | `external_docs` | `dict` | External documentation references. | | `language` | `str` | Language code to use for I18nStr values. | | `prefix_config` | `ConventionalPrefixConfig` | Configuration for parameter prefixes. | | `content_type` | `str` | Custom content type for request body. | | `request_content_types` | `RequestContentTypes` | Multiple content types for request body. | | `response_content_types` | `ResponseContentTypes` | Multiple content types for response body. | | `content_type_resolver` | `Callable` | Function to determine content type based on request. | | `default_error_response` | `Type[BaseErrorResponse]` | Default error response class. |

Source code in `src/flask_x_openapi_schema/core/decorator_base.py`

```python
class DecoratorBase(ABC):
    """Base class for framework-specific decorators.

    This class encapsulates common functionality for processing request bodies,
    query parameters, and path parameters. It is designed to be inherited by
    framework-specific decorator implementations.

    Attributes:
        summary (str or I18nStr): Short summary of the endpoint.
        description (str or I18nStr): Detailed description of the endpoint.
        tags (list): List of tags to categorize the endpoint.
        operation_id (str): Unique identifier for the operation.
        responses (OpenAPIMetaResponse): Response models configuration.
        deprecated (bool): Whether the endpoint is deprecated.
        security (list): Security requirements for the endpoint.
        external_docs (dict): External documentation references.
        language (str): Language code to use for I18nStr values.
        prefix_config (ConventionalPrefixConfig): Configuration for parameter prefixes.
        content_type (str): Custom content type for request body.
        request_content_types (RequestContentTypes): Multiple content types for request body.
        response_content_types (ResponseContentTypes): Multiple content types for response body.
        content_type_resolver (Callable): Function to determine content type based on request.
        default_error_response (Type[BaseErrorResponse]): Default error response class.

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
            summary: Short summary of the endpoint, can be an I18nStr for localization.
            description: Detailed description of the endpoint, can be an I18nStr.
            tags: List of tags to categorize the endpoint.
            operation_id: Unique identifier for the operation.
            responses: Response models configuration.
            deprecated: Whether the endpoint is deprecated. Defaults to False.
            security: Security requirements for the endpoint.
            external_docs: External documentation references.
            language: Language code to use for I18nStr values.
            prefix_config: Configuration for parameter prefixes.
            content_type: Custom content type for request body. If None, will be auto-detected.
            request_content_types: Multiple content types for request body.
            response_content_types: Multiple content types for response body.
            content_type_resolver: Function to determine content type based on request.

        """
        self.summary = summary
        self.description = description
        self.tags = tags
        self.operation_id = operation_id
        self.responses = responses
        self.deprecated = deprecated
        self.security = security
        self.external_docs = external_docs
        self.language = language
        self.prefix_config = prefix_config
        self.content_type = content_type
        self.request_content_types = request_content_types
        self.response_content_types = response_content_types
        self.content_type_resolver = content_type_resolver
        self.default_error_response = responses.default_error_response if responses else BaseErrorResponse

        # Initialize content type processor
        self.content_type_processor = ContentTypeProcessor(
            content_type=content_type,
            request_content_types=request_content_types,
            content_type_resolver=content_type_resolver,
            default_error_response=self.default_error_response,
        )

    @abstractmethod
    def __call__(self, func: Callable) -> Callable:
        """Apply the decorator to the function.

        Args:
            func: The function to decorate

        Returns:
            The decorated function

        """
        # This method should be implemented by subclasses
        msg = "Subclasses must implement __call__"
        raise NotImplementedError(msg)

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
                ]
            )

        if query_model:
            schema = query_model.model_json_schema()
            properties = schema.get("properties", {})
            required = schema.get("required", [])

            for field_name, field_schema in properties.items():
                fixed_schema = _fix_references(field_schema)
                param = {
                    "name": field_name,
                    "in": "query",
                    "required": field_name in required,
                    "schema": fixed_schema,
                }

                if "description" in field_schema:
                    param["description"] = field_schema["description"]

                parameters.append(param)

        return parameters

    def process_request_body(self, param_name: str, model: type[BaseModel], kwargs: dict[str, Any]) -> dict[str, Any]:
        """Process request body parameters.

        Args:
            param_name: The parameter name to bind the model instance to
            model: The Pydantic model class to use for validation
            kwargs: The keyword arguments to update

        Returns:
            Updated kwargs dictionary with the model instance

        """
        return self.content_type_processor.process_request_body(request, model, param_name, kwargs)

    @abstractmethod
    def process_query_params(self, param_name: str, model: type[BaseModel], kwargs: dict[str, Any]) -> dict[str, Any]:
        """Process query parameters.

        Args:
            param_name: The parameter name to bind the model instance to
            model: The Pydantic model class to use for validation
            kwargs: The keyword arguments to update

        Returns:
            Updated kwargs dictionary with the model instance

        """
        # This method should be implemented by subclasses
        msg = "Subclasses must implement process_query_params"
        raise NotImplementedError(msg)

    def process_additional_params(self, kwargs: dict[str, Any], param_names: list[str]) -> dict[str, Any]:  # noqa: ARG002
        """Process additional framework-specific parameters.

        Args:
            kwargs: The keyword arguments to update
            param_names: List of parameter names that have been processed

        Returns:
            Updated kwargs dictionary

        """
        # This method should be implemented by subclasses
        return kwargs

```

##### `__call__(func)`

Apply the decorator to the function.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `func` | `Callable` | The function to decorate | *required* |

Returns:

| Type | Description | | --- | --- | | `Callable` | The decorated function |

Source code in `src/flask_x_openapi_schema/core/decorator_base.py`

```python
@abstractmethod
def __call__(self, func: Callable) -> Callable:
    """Apply the decorator to the function.

    Args:
        func: The function to decorate

    Returns:
        The decorated function

    """
    # This method should be implemented by subclasses
    msg = "Subclasses must implement __call__"
    raise NotImplementedError(msg)

```

##### `__init__(summary=None, description=None, tags=None, operation_id=None, responses=None, deprecated=False, security=None, external_docs=None, language=None, prefix_config=None, content_type=None, request_content_types=None, response_content_types=None, content_type_resolver=None)`

Initialize the decorator with OpenAPI metadata parameters.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `summary` | `str | I18nStr | None` | Short summary of the endpoint, can be an I18nStr for localization. | `None` | | `description` | `str | I18nStr | None` | Detailed description of the endpoint, can be an I18nStr. | `None` | | `tags` | `list[str] | None` | List of tags to categorize the endpoint. | `None` | | `operation_id` | `str | None` | Unique identifier for the operation. | `None` | | `responses` | `OpenAPIMetaResponse | None` | Response models configuration. | `None` | | `deprecated` | `bool` | Whether the endpoint is deprecated. Defaults to False. | `False` | | `security` | `list[dict[str, list[str]]] | None` | Security requirements for the endpoint. | `None` | | `external_docs` | `dict[str, str] | None` | External documentation references. | `None` | | `language` | `str | None` | Language code to use for I18nStr values. | `None` | | `prefix_config` | `ConventionalPrefixConfig | None` | Configuration for parameter prefixes. | `None` | | `content_type` | `str | None` | Custom content type for request body. If None, will be auto-detected. | `None` | | `request_content_types` | `RequestContentTypes | None` | Multiple content types for request body. | `None` | | `response_content_types` | `ResponseContentTypes | None` | Multiple content types for response body. | `None` | | `content_type_resolver` | `Callable[[Any], str] | None` | Function to determine content type based on request. | `None` |

Source code in `src/flask_x_openapi_schema/core/decorator_base.py`

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
        summary: Short summary of the endpoint, can be an I18nStr for localization.
        description: Detailed description of the endpoint, can be an I18nStr.
        tags: List of tags to categorize the endpoint.
        operation_id: Unique identifier for the operation.
        responses: Response models configuration.
        deprecated: Whether the endpoint is deprecated. Defaults to False.
        security: Security requirements for the endpoint.
        external_docs: External documentation references.
        language: Language code to use for I18nStr values.
        prefix_config: Configuration for parameter prefixes.
        content_type: Custom content type for request body. If None, will be auto-detected.
        request_content_types: Multiple content types for request body.
        response_content_types: Multiple content types for response body.
        content_type_resolver: Function to determine content type based on request.

    """
    self.summary = summary
    self.description = description
    self.tags = tags
    self.operation_id = operation_id
    self.responses = responses
    self.deprecated = deprecated
    self.security = security
    self.external_docs = external_docs
    self.language = language
    self.prefix_config = prefix_config
    self.content_type = content_type
    self.request_content_types = request_content_types
    self.response_content_types = response_content_types
    self.content_type_resolver = content_type_resolver
    self.default_error_response = responses.default_error_response if responses else BaseErrorResponse

    # Initialize content type processor
    self.content_type_processor = ContentTypeProcessor(
        content_type=content_type,
        request_content_types=request_content_types,
        content_type_resolver=content_type_resolver,
        default_error_response=self.default_error_response,
    )

```

##### `extract_parameters_from_models(query_model, path_params)`

Extract OpenAPI parameters from models.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `query_model` | `type[BaseModel] | None` | The query parameter model | *required* | | `path_params` | `list[str] | None` | List of path parameter names | *required* |

Returns:

| Type | Description | | --- | --- | | `list[dict[str, Any]]` | List of OpenAPI parameter objects |

Source code in `src/flask_x_openapi_schema/core/decorator_base.py`

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
            ]
        )

    if query_model:
        schema = query_model.model_json_schema()
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        for field_name, field_schema in properties.items():
            fixed_schema = _fix_references(field_schema)
            param = {
                "name": field_name,
                "in": "query",
                "required": field_name in required,
                "schema": fixed_schema,
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

Source code in `src/flask_x_openapi_schema/core/decorator_base.py`

```python
def process_additional_params(self, kwargs: dict[str, Any], param_names: list[str]) -> dict[str, Any]:  # noqa: ARG002
    """Process additional framework-specific parameters.

    Args:
        kwargs: The keyword arguments to update
        param_names: List of parameter names that have been processed

    Returns:
        Updated kwargs dictionary

    """
    # This method should be implemented by subclasses
    return kwargs

```

##### `process_query_params(param_name, model, kwargs)`

Process query parameters.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `param_name` | `str` | The parameter name to bind the model instance to | *required* | | `model` | `type[BaseModel]` | The Pydantic model class to use for validation | *required* | | `kwargs` | `dict[str, Any]` | The keyword arguments to update | *required* |

Returns:

| Type | Description | | --- | --- | | `dict[str, Any]` | Updated kwargs dictionary with the model instance |

Source code in `src/flask_x_openapi_schema/core/decorator_base.py`

```python
@abstractmethod
def process_query_params(self, param_name: str, model: type[BaseModel], kwargs: dict[str, Any]) -> dict[str, Any]:
    """Process query parameters.

    Args:
        param_name: The parameter name to bind the model instance to
        model: The Pydantic model class to use for validation
        kwargs: The keyword arguments to update

    Returns:
        Updated kwargs dictionary with the model instance

    """
    # This method should be implemented by subclasses
    msg = "Subclasses must implement process_query_params"
    raise NotImplementedError(msg)

```

##### `process_request_body(param_name, model, kwargs)`

Process request body parameters.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `param_name` | `str` | The parameter name to bind the model instance to | *required* | | `model` | `type[BaseModel]` | The Pydantic model class to use for validation | *required* | | `kwargs` | `dict[str, Any]` | The keyword arguments to update | *required* |

Returns:

| Type | Description | | --- | --- | | `dict[str, Any]` | Updated kwargs dictionary with the model instance |

Source code in `src/flask_x_openapi_schema/core/decorator_base.py`

```python
def process_request_body(self, param_name: str, model: type[BaseModel], kwargs: dict[str, Any]) -> dict[str, Any]:
    """Process request body parameters.

    Args:
        param_name: The parameter name to bind the model instance to
        model: The Pydantic model class to use for validation
        kwargs: The keyword arguments to update

    Returns:
        Updated kwargs dictionary with the model instance

    """
    return self.content_type_processor.process_request_body(request, model, param_name, kwargs)

```

#### `OpenAPIDecoratorBase`

Base class for OpenAPI metadata decorators.

This class provides the foundation for framework-specific OpenAPI metadata decorators. It handles parameter extraction, metadata generation, and request processing in a framework-agnostic way, delegating framework-specific operations to subclasses.

The decorator adds OpenAPI metadata to API endpoint functions and handles parameter binding between HTTP requests and function parameters based on naming conventions.

Attributes:

| Name | Type | Description | | --- | --- | --- | | `summary` | `str or I18nStr` | Short summary of the endpoint. | | `description` | `str or I18nStr` | Detailed description of the endpoint. | | `tags` | `list` | List of tags to categorize the endpoint. | | `operation_id` | `str` | Unique identifier for the operation. | | `responses` | `OpenAPIMetaResponse` | Response models configuration. | | `deprecated` | `bool` | Whether the endpoint is deprecated. | | `security` | `list` | Security requirements for the endpoint. | | `external_docs` | `dict` | External documentation references. | | `language` | `str` | Language code to use for I18nStr values. | | `prefix_config` | `ConventionalPrefixConfig` | Configuration for parameter prefixes. | | `framework` | `str` | Framework name ('flask' or 'flask_restful'). | | `framework_decorator` | | Framework-specific decorator instance. |

Source code in `src/flask_x_openapi_schema/core/decorator_base.py`

```python
class OpenAPIDecoratorBase:
    """Base class for OpenAPI metadata decorators.

    This class provides the foundation for framework-specific OpenAPI metadata decorators.
    It handles parameter extraction, metadata generation, and request processing in a
    framework-agnostic way, delegating framework-specific operations to subclasses.

    The decorator adds OpenAPI metadata to API endpoint functions and handles parameter
    binding between HTTP requests and function parameters based on naming conventions.

    Attributes:
        summary (str or I18nStr): Short summary of the endpoint.
        description (str or I18nStr): Detailed description of the endpoint.
        tags (list): List of tags to categorize the endpoint.
        operation_id (str): Unique identifier for the operation.
        responses (OpenAPIMetaResponse): Response models configuration.
        deprecated (bool): Whether the endpoint is deprecated.
        security (list): Security requirements for the endpoint.
        external_docs (dict): External documentation references.
        language (str): Language code to use for I18nStr values.
        prefix_config (ConventionalPrefixConfig): Configuration for parameter prefixes.
        framework (str): Framework name ('flask' or 'flask_restful').
        framework_decorator: Framework-specific decorator instance.

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
        framework: str = "flask",
        content_type: str | None = None,
        request_content_types: RequestContentTypes | None = None,
        response_content_types: ResponseContentTypes | None = None,
        content_type_resolver: Callable[[Any], str] | None = None,
    ) -> None:
        """Initialize the decorator with OpenAPI metadata parameters.

        Args:
            summary: Short summary of the endpoint, can be an I18nStr for localization.
            description: Detailed description of the endpoint, can be an I18nStr.
            tags: List of tags to categorize the endpoint.
            operation_id: Unique identifier for the operation.
            responses: Response models configuration.
            deprecated: Whether the endpoint is deprecated. Defaults to False.
            security: Security requirements for the endpoint.
            external_docs: External documentation references.
            language: Language code to use for I18nStr values.
            prefix_config: Configuration for parameter prefixes.
            framework: Framework name ('flask' or 'flask_restful'). Defaults to "flask".
            content_type: Custom content type for request body. If None, will be auto-detected.
            request_content_types: Multiple content types for request body.
            response_content_types: Multiple content types for response body.
            content_type_resolver: Function to determine content type based on request.


        """
        self.summary = summary
        self.description = description
        self.tags = tags
        self.operation_id = operation_id
        self.responses = responses
        self.deprecated = deprecated
        self.security = security
        self.external_docs = external_docs
        self.language = language
        self.prefix_config = prefix_config
        self.framework = framework
        self.content_type = content_type
        self.request_content_types = request_content_types
        self.response_content_types = response_content_types
        self.content_type_resolver = content_type_resolver
        self.default_error_response = responses.default_error_response if responses else BaseErrorResponse

        self.framework_decorator = None

    def _initialize_framework_decorator(self) -> None:
        """Initialize the framework-specific decorator.

        This method uses lazy loading to avoid circular imports. It creates the appropriate
        framework-specific decorator based on the 'framework' attribute.

        Raises:
            ValueError: If an unsupported framework is specified.

        """
        if self.framework_decorator is None:
            if self.framework == "flask":
                from flask_x_openapi_schema.x.flask.decorators import FlaskOpenAPIDecorator

                self.framework_decorator = FlaskOpenAPIDecorator(
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
                    content_type=self.content_type,
                    request_content_types=self.request_content_types,
                    response_content_types=self.response_content_types,
                    content_type_resolver=self.content_type_resolver,
                )
            elif self.framework == "flask_restful":
                from flask_x_openapi_schema.x.flask_restful.decorators import FlaskRestfulOpenAPIDecorator

                self.framework_decorator = FlaskRestfulOpenAPIDecorator(
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
                    content_type=self.content_type,
                    request_content_types=self.request_content_types,
                    response_content_types=self.response_content_types,
                    content_type_resolver=self.content_type_resolver,
                )
            else:
                msg = f"Unsupported framework: {self.framework}"
                raise ValueError(msg)

    def _create_cached_wrapper(self, func: Callable[P, R], cached_data: dict[str, Any]) -> Callable[P, R]:
        """Create a wrapper function that reuses cached metadata.

        Args:
            func: The decorated function
            cached_data: Cached metadata and other information

        Returns:
            A wrapper function that reuses cached metadata

        """
        logger.debug(f"Using cached metadata for function {func.__name__}")
        logger.debug(f"Cached metadata: {cached_data['metadata']}")

        @wraps(func)
        def cached_wrapper(*args, **kwargs) -> Any:
            signature = cached_data["signature"]
            param_names = cached_data["param_names"]

            for param_name in param_names:
                if param_name not in kwargs and param_name in signature.parameters:
                    param = signature.parameters[param_name]
                    if param.default is param.empty and param_name in cached_data["type_hints"]:
                        param_type = cached_data["type_hints"][param_name]
                        if isinstance(param_type, type) and issubclass(param_type, BaseModel):
                            kwargs[param_name] = param_type()

            return self._process_request(func, cached_data, *args, **kwargs)

        cached_wrapper._openapi_metadata = cached_data["metadata"]
        cached_wrapper.__annotations__ = cached_data["annotations"]

        return cast("Callable[P, R]", cached_wrapper)

    def _extract_parameters(
        self, signature: inspect.Signature, type_hints: dict[str, Any]
    ) -> tuple[type[BaseModel] | None, type[BaseModel] | None, list[str]]:
        """Extract parameters from function signature.

        Args:
            signature: Function signature
            type_hints: Function type hints

        Returns:
            Tuple of (request_body, query_model, path_params)

        """
        return _extract_parameters_from_prefixes(
            signature,
            type_hints,
            self.prefix_config,
        )

    def _generate_metadata_cache_key(
        self,
        actual_request_body: type[BaseModel] | dict[str, Any] | None,
        actual_query_model: type[BaseModel] | None,
        actual_path_params: list[str],
    ) -> tuple:
        """Generate a cache key for metadata.

        Args:
            actual_request_body: Request body model or dict
            actual_query_model: Query parameters model
            actual_path_params: Path parameters

        Returns:
            A cache key for metadata

        """
        return (
            str(self.summary),
            str(self.description),
            str(self.tags) if self.tags else None,
            self.operation_id,
            self.deprecated,
            str(self.security) if self.security else None,
            str(self.external_docs) if self.external_docs else None,
            id(actual_request_body) if isinstance(actual_request_body, type) else str(actual_request_body),
            str(self.responses) if self.responses else None,
            id(actual_query_model) if actual_query_model else None,
            str(actual_path_params) if actual_path_params else None,
            self.language,
        )

    def _get_or_generate_metadata(
        self,
        cache_key: tuple,  # noqa: ARG002
        actual_request_body: type[BaseModel] | dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Generate OpenAPI metadata for an endpoint.

        This method delegates to the module-level _generate_openapi_metadata function
        using the decorator's attributes.

        Args:
            cache_key: Cache key for metadata (not used now).
            actual_request_body: Request body model or dict.

        Returns:
            dict: OpenAPI metadata dictionary ready to be included in the schema.

        """
        return _generate_openapi_metadata(
            summary=self.summary,
            description=self.description,
            tags=self.tags,
            operation_id=self.operation_id,
            deprecated=self.deprecated,
            security=self.security,
            external_docs=self.external_docs,
            actual_request_body=actual_request_body,
            responses=self.responses,
            language=self.language,
            content_type=self.content_type,
            request_content_types=self.request_content_types,
            response_content_types=self.response_content_types,
        )

    def _generate_openapi_parameters(
        self,
        actual_query_model: type[BaseModel] | None,
        actual_path_params: list[str],
        param_names: list[str],
        func_annotations: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Generate OpenAPI parameters.

        This method generates OpenAPI parameters from query models, path parameters,
        and file parameters. It uses caching to avoid regenerating parameters for
        the same models and parameters.

        Args:
            actual_query_model: Query parameters model
            actual_path_params: Path parameters
            param_names: Function parameter names
            func_annotations: Function type annotations

        Returns:
            List of OpenAPI parameters

        """
        openapi_parameters = []

        if actual_query_model or actual_path_params:
            model_parameters = self._get_or_generate_model_parameters(actual_query_model, actual_path_params)
            if model_parameters:
                logger.debug(f"Added parameters to metadata: {model_parameters}")
                openapi_parameters.extend(model_parameters)

        file_params = _detect_file_parameters(param_names, func_annotations, self.prefix_config)
        if file_params:
            openapi_parameters.extend(file_params)

        return openapi_parameters

    def _get_or_generate_model_parameters(
        self,
        query_model: type[BaseModel] | None,
        path_params: list[str],
    ) -> list[dict[str, Any]]:
        """Generate parameters from models and path parameters.

        This method is extracted from _generate_openapi_parameters to improve readability.
        It generates parameters from query models and path parameters.

        Args:
            query_model: Query parameters model
            path_params: Path parameters

        Returns:
            List of OpenAPI parameters

        """
        model_parameters = []

        if path_params:
            model_parameters.extend(self._generate_path_parameters(path_params))

        if query_model:
            model_parameters.extend(self._generate_query_parameters(query_model))

        return model_parameters

    def _generate_path_parameters(self, path_params: list[str]) -> list[dict[str, Any]]:
        """Generate OpenAPI parameters for path parameters.

        Args:
            path_params: List of path parameter names

        Returns:
            List of OpenAPI parameters for path parameters

        """
        return [
            {
                "name": param,
                "in": "path",
                "required": True,
                "schema": {"type": "string"},
            }
            for param in path_params
        ]

    def _generate_query_parameters(self, query_model: type[BaseModel]) -> list[dict[str, Any]]:
        """Generate OpenAPI parameters for query parameters.

        Args:
            query_model: Query parameters model

        Returns:
            List of OpenAPI parameters for query parameters

        """
        parameters = []
        schema = query_model.model_json_schema()
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        for field_name, field_schema in properties.items():
            fixed_schema = _fix_references(field_schema)
            param = {
                "name": field_name,
                "in": "query",
                "required": field_name in required,
                "schema": fixed_schema,
            }

            if "description" in field_schema:
                param["description"] = field_schema["description"]

            parameters.append(param)

        return parameters

    def _create_function_wrapper(
        self,
        func: Callable[P, R],
        cached_data: dict[str, Any],
        metadata: dict[str, Any],
        merged_hints: dict[str, Any],
    ) -> Callable[P, R]:
        """Create a wrapper function for the decorated function.

        Args:
            func: The decorated function
            cached_data: Cached metadata and other information
            metadata: OpenAPI metadata
            merged_hints: Merged type hints

        Returns:
            A wrapper function

        """

        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            return self._process_request(func, cached_data, *args, **kwargs)

        wrapper._openapi_metadata = metadata

        wrapper.__annotations__ = merged_hints

        return cast("Callable[P, R]", wrapper)

    def __call__(self, func: Callable[P, R]) -> Callable[P, R]:
        """Apply the decorator to the function.

        This method has been refactored to use smaller, more focused methods.

        Args:
            func: The function to decorate

        Returns:
            The decorated function

        """
        self._initialize_framework_decorator()

        if func in FUNCTION_METADATA_CACHE:
            cached_data = FUNCTION_METADATA_CACHE[func]
            return self._create_cached_wrapper(func, cached_data)

        signature = inspect.signature(func)
        param_names = list(signature.parameters.keys())

        type_hints = get_type_hints(func)

        actual_request_body, actual_query_model, actual_path_params = self._extract_parameters(signature, type_hints)

        logger.debug(
            f"Generating metadata with request_body={actual_request_body}, query_model={actual_query_model}, path_params={actual_path_params}",
        )

        cache_key = self._generate_metadata_cache_key(actual_request_body, actual_query_model, actual_path_params)

        metadata = self._get_or_generate_metadata(cache_key, actual_request_body)

        func_annotations = get_type_hints(func)
        openapi_parameters = self._generate_openapi_parameters(
            actual_query_model, actual_path_params, param_names, func_annotations
        )

        if any(param.get("in") == "formData" for param in openapi_parameters):
            metadata["consumes"] = ["multipart/form-data"]

        if openapi_parameters:
            metadata["parameters"] = openapi_parameters

        func._openapi_metadata = metadata

        param_types = {}

        if (
            actual_request_body
            and isinstance(actual_request_body, type)
            and issubclass(actual_request_body, BaseModel)
            and hasattr(actual_request_body, "model_fields")
        ):
            param_types.update(
                {field_name: field.annotation for field_name, field in actual_request_body.model_fields.items()}
            )

        if actual_query_model and hasattr(actual_query_model, "model_fields"):
            param_types.update(
                {field_name: field.annotation for field_name, field in actual_query_model.model_fields.items()}
            )

        existing_hints = get_type_hints(func)
        merged_hints = {**existing_hints, **param_types}

        cached_data = {
            "metadata": metadata,
            "annotations": merged_hints,
            "signature": signature,
            "param_names": param_names,
            "type_hints": type_hints,
            "actual_request_body": actual_request_body,
            "actual_query_model": actual_query_model,
            "actual_path_params": actual_path_params,
        }
        FUNCTION_METADATA_CACHE[func] = cached_data

        return self._create_function_wrapper(func, cached_data, metadata, merged_hints)

    def _process_request(self, func: Callable[P, R], cached_data: dict[str, Any], *args, **kwargs) -> Any:
        """Process a request using cached metadata.

        This method uses the ParameterProcessor to handle parameter binding using the Strategy pattern.
        It extracts parameters from the request context, binds them to function parameters,
        and handles model validation and conversion.

        Args:
            func: The decorated function to call.
            cached_data: Cached metadata and other information about the function.
            args: Positional arguments to the function.
            kwargs: Keyword arguments to the function.

        Returns:
            Any: The result of calling the function with bound parameters,
                processed by _handle_response if needed.

        """
        signature = cached_data["signature"]
        param_names = cached_data.get("param_names", [])

        from flask import request

        has_request_context = False
        with contextlib.suppress(RuntimeError):
            has_request_context = bool(request)

        if has_request_context and request.method == "POST" and request.is_json:
            json_data = request.get_json(silent=True)

            if json_data:
                for param_name in param_names:
                    if param_name in signature.parameters and param_name.startswith("_x_body"):
                        param_type = cached_data["type_hints"].get(param_name)
                        if param_type and isinstance(param_type, type) and issubclass(param_type, BaseModel):
                            with contextlib.suppress(Exception):
                                model_instance = param_type.model_validate(json_data)
                                kwargs[param_name] = model_instance

        for param_name in param_names:
            if param_name not in kwargs and param_name in signature.parameters:
                param = signature.parameters[param_name]
                if param.default is param.empty and param_name in cached_data["type_hints"]:
                    param_type = cached_data["type_hints"][param_name]
                    if isinstance(param_type, type) and issubclass(param_type, BaseModel):
                        if has_request_context and param_name.startswith("_x_body") and request.is_json:
                            json_data = request.get_json(silent=True)
                            if json_data:
                                with contextlib.suppress(Exception):
                                    kwargs[param_name] = param_type.model_validate(json_data)
                                    continue

                        with contextlib.suppress(Exception):
                            kwargs[param_name] = param_type()

        parameter_processor = ParameterProcessor(
            prefix_config=self.prefix_config,
            framework_decorator=self.framework_decorator,
        )

        if hasattr(kwargs, "status_code") and hasattr(kwargs, "data"):
            return kwargs

        kwargs = parameter_processor.process_parameters(func, cached_data, args, kwargs)

        if hasattr(kwargs, "status_code") and hasattr(kwargs, "data"):
            return kwargs

        sig_params = signature.parameters

        if not isinstance(kwargs, dict):
            logger.warning(f"kwargs is not a dict: {type(kwargs)}")
            valid_kwargs = {}
        else:
            valid_kwargs = {k: v for k, v in kwargs.items() if k in sig_params}

        for param_name, param in sig_params.items():
            if param_name not in valid_kwargs and param.default is param.empty:
                if param_name in {"self", "cls"}:
                    continue

                if param_name in cached_data["type_hints"]:
                    param_type = cached_data["type_hints"][param_name]
                    if isinstance(param_type, type) and issubclass(param_type, BaseModel):
                        if has_request_context and param_name.startswith("_x_body") and request.is_json:
                            json_data = request.get_json(silent=True)
                            if json_data:
                                with contextlib.suppress(Exception):
                                    valid_kwargs[param_name] = param_type.model_validate(json_data)
                                    continue

                        if hasattr(param_type, "model_json_schema"):
                            schema = param_type.model_json_schema()
                            required_fields = schema.get("required", [])
                            default_data = {}
                            for field in required_fields:
                                if field in param_type.model_fields:
                                    field_info = param_type.model_fields[field]
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

                            with contextlib.suppress(Exception):
                                valid_kwargs[param_name] = param_type.model_validate(default_data)
                        else:
                            with contextlib.suppress(Exception):
                                valid_kwargs[param_name] = param_type()

        result = func(*args, **valid_kwargs)

        return _handle_response(result)

```

##### `__call__(func)`

Apply the decorator to the function.

This method has been refactored to use smaller, more focused methods.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `func` | `Callable[P, R]` | The function to decorate | *required* |

Returns:

| Type | Description | | --- | --- | | `Callable[P, R]` | The decorated function |

Source code in `src/flask_x_openapi_schema/core/decorator_base.py`

```python
def __call__(self, func: Callable[P, R]) -> Callable[P, R]:
    """Apply the decorator to the function.

    This method has been refactored to use smaller, more focused methods.

    Args:
        func: The function to decorate

    Returns:
        The decorated function

    """
    self._initialize_framework_decorator()

    if func in FUNCTION_METADATA_CACHE:
        cached_data = FUNCTION_METADATA_CACHE[func]
        return self._create_cached_wrapper(func, cached_data)

    signature = inspect.signature(func)
    param_names = list(signature.parameters.keys())

    type_hints = get_type_hints(func)

    actual_request_body, actual_query_model, actual_path_params = self._extract_parameters(signature, type_hints)

    logger.debug(
        f"Generating metadata with request_body={actual_request_body}, query_model={actual_query_model}, path_params={actual_path_params}",
    )

    cache_key = self._generate_metadata_cache_key(actual_request_body, actual_query_model, actual_path_params)

    metadata = self._get_or_generate_metadata(cache_key, actual_request_body)

    func_annotations = get_type_hints(func)
    openapi_parameters = self._generate_openapi_parameters(
        actual_query_model, actual_path_params, param_names, func_annotations
    )

    if any(param.get("in") == "formData" for param in openapi_parameters):
        metadata["consumes"] = ["multipart/form-data"]

    if openapi_parameters:
        metadata["parameters"] = openapi_parameters

    func._openapi_metadata = metadata

    param_types = {}

    if (
        actual_request_body
        and isinstance(actual_request_body, type)
        and issubclass(actual_request_body, BaseModel)
        and hasattr(actual_request_body, "model_fields")
    ):
        param_types.update(
            {field_name: field.annotation for field_name, field in actual_request_body.model_fields.items()}
        )

    if actual_query_model and hasattr(actual_query_model, "model_fields"):
        param_types.update(
            {field_name: field.annotation for field_name, field in actual_query_model.model_fields.items()}
        )

    existing_hints = get_type_hints(func)
    merged_hints = {**existing_hints, **param_types}

    cached_data = {
        "metadata": metadata,
        "annotations": merged_hints,
        "signature": signature,
        "param_names": param_names,
        "type_hints": type_hints,
        "actual_request_body": actual_request_body,
        "actual_query_model": actual_query_model,
        "actual_path_params": actual_path_params,
    }
    FUNCTION_METADATA_CACHE[func] = cached_data

    return self._create_function_wrapper(func, cached_data, metadata, merged_hints)

```

##### `__init__(summary=None, description=None, tags=None, operation_id=None, responses=None, deprecated=False, security=None, external_docs=None, language=None, prefix_config=None, framework='flask', content_type=None, request_content_types=None, response_content_types=None, content_type_resolver=None)`

Initialize the decorator with OpenAPI metadata parameters.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `summary` | `str | I18nStr | None` | Short summary of the endpoint, can be an I18nStr for localization. | `None` | | `description` | `str | I18nStr | None` | Detailed description of the endpoint, can be an I18nStr. | `None` | | `tags` | `list[str] | None` | List of tags to categorize the endpoint. | `None` | | `operation_id` | `str | None` | Unique identifier for the operation. | `None` | | `responses` | `OpenAPIMetaResponse | None` | Response models configuration. | `None` | | `deprecated` | `bool` | Whether the endpoint is deprecated. Defaults to False. | `False` | | `security` | `list[dict[str, list[str]]] | None` | Security requirements for the endpoint. | `None` | | `external_docs` | `dict[str, str] | None` | External documentation references. | `None` | | `language` | `str | None` | Language code to use for I18nStr values. | `None` | | `prefix_config` | `ConventionalPrefixConfig | None` | Configuration for parameter prefixes. | `None` | | `framework` | `str` | Framework name ('flask' or 'flask_restful'). Defaults to "flask". | `'flask'` | | `content_type` | `str | None` | Custom content type for request body. If None, will be auto-detected. | `None` | | `request_content_types` | `RequestContentTypes | None` | Multiple content types for request body. | `None` | | `response_content_types` | `ResponseContentTypes | None` | Multiple content types for response body. | `None` | | `content_type_resolver` | `Callable[[Any], str] | None` | Function to determine content type based on request. | `None` |

Source code in `src/flask_x_openapi_schema/core/decorator_base.py`

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
    framework: str = "flask",
    content_type: str | None = None,
    request_content_types: RequestContentTypes | None = None,
    response_content_types: ResponseContentTypes | None = None,
    content_type_resolver: Callable[[Any], str] | None = None,
) -> None:
    """Initialize the decorator with OpenAPI metadata parameters.

    Args:
        summary: Short summary of the endpoint, can be an I18nStr for localization.
        description: Detailed description of the endpoint, can be an I18nStr.
        tags: List of tags to categorize the endpoint.
        operation_id: Unique identifier for the operation.
        responses: Response models configuration.
        deprecated: Whether the endpoint is deprecated. Defaults to False.
        security: Security requirements for the endpoint.
        external_docs: External documentation references.
        language: Language code to use for I18nStr values.
        prefix_config: Configuration for parameter prefixes.
        framework: Framework name ('flask' or 'flask_restful'). Defaults to "flask".
        content_type: Custom content type for request body. If None, will be auto-detected.
        request_content_types: Multiple content types for request body.
        response_content_types: Multiple content types for response body.
        content_type_resolver: Function to determine content type based on request.


    """
    self.summary = summary
    self.description = description
    self.tags = tags
    self.operation_id = operation_id
    self.responses = responses
    self.deprecated = deprecated
    self.security = security
    self.external_docs = external_docs
    self.language = language
    self.prefix_config = prefix_config
    self.framework = framework
    self.content_type = content_type
    self.request_content_types = request_content_types
    self.response_content_types = response_content_types
    self.content_type_resolver = content_type_resolver
    self.default_error_response = responses.default_error_response if responses else BaseErrorResponse

    self.framework_decorator = None

```

## Schema Generator

OpenAPI Schema Generator for API documentation.

This module provides the main class for generating OpenAPI schemas from Flask-RESTful resources. It handles scanning resources, extracting metadata, and generating a complete OpenAPI schema.

#### `OpenAPISchemaGenerator`

Generator for OpenAPI schemas from Flask-RESTful resources.

This class scans Flask-RESTful resources and generates OpenAPI schemas based on the resource methods, docstrings, and type annotations.

Source code in `src/flask_x_openapi_schema/core/schema_generator.py`

```python
class OpenAPISchemaGenerator:
    """Generator for OpenAPI schemas from Flask-RESTful resources.

    This class scans Flask-RESTful resources and generates OpenAPI schemas based on
    the resource methods, docstrings, and type annotations.
    """

    def __init__(
        self,
        title: str | None = None,
        version: str | None = None,
        description: str | None = None,
        language: str | None = None,
    ) -> None:
        """Initialize the OpenAPI schema generator.

        Args:
            title: The title of the API (default: from config)
            version: The version of the API (default: from config)
            description: The description of the API (default: from config)
            language: The language to use for internationalized strings (default: current language)

        """
        # Get defaults from config if not provided
        config = get_openapi_config()

        # Handle I18nString for title and description
        self.title = title if title is not None else config.title
        if isinstance(self.title, I18nStr):
            self.title = self.title.get(language)

        self.version = version if version is not None else config.version

        self.description = description if description is not None else config.description
        if isinstance(self.description, I18nStr):
            self.description = self.description.get(language)

        self.language = language or get_current_language()

        # Initialize data structures
        self.paths: dict[str, dict[str, Any]] = {}
        self.components: dict[str, dict[str, Any]] = {
            "schemas": {},
            "securitySchemes": config.security_schemes.copy() if config.security_schemes else {},
        }
        self.tags: list[dict[str, str]] = []
        self.webhooks: dict[str, dict[str, Any]] = {}
        self._registered_models: set[type[BaseModel]] = set()

        # Thread safety locks
        self._lock = threading.RLock()  # Main lock for coordinating access
        self._paths_lock = threading.RLock()
        self._components_lock = threading.RLock()
        self._tags_lock = threading.RLock()
        self._models_lock = threading.RLock()
        self._webhooks_lock = threading.RLock()

    def add_security_scheme(self, name: str, scheme: dict[str, Any]) -> None:
        """Add a security scheme to the OpenAPI schema.

        Args:
            name: The name of the security scheme
            scheme: The security scheme definition

        """
        with self._components_lock:
            self.components["securitySchemes"][name] = scheme

    def add_tag(self, name: str, description: str = "") -> None:
        """Add a tag to the OpenAPI schema.

        Args:
            name: The name of the tag
            description: The description of the tag

        """
        with self._tags_lock:
            self.tags.append({"name": name, "description": description})

    def add_webhook(self, name: str, webhook_data: dict[str, Any]) -> None:
        """Add a webhook to the OpenAPI schema.

        Args:
            name: The name of the webhook
            webhook_data: The webhook definition

        """
        with self._webhooks_lock:
            self.webhooks[name] = webhook_data

    def scan_blueprint(self, blueprint: Blueprint) -> None:
        """Scan a Flask blueprint for API resources and add them to the schema.

        Args:
            blueprint: The Flask blueprint to scan

        """
        # Get all resources registered to the blueprint
        if not hasattr(blueprint, "resources"):
            return

        for resource, urls, _ in blueprint.resources:
            self._process_resource(resource, urls, blueprint.url_prefix)

    def _process_resource(self, resource: Any, urls: tuple[str], prefix: str | None = None) -> None:
        """Process a Flask-RESTful resource and add its endpoints to the schema.

        Args:
            resource: The Flask-RESTful resource class
            urls: The URLs registered for the resource
            prefix: The URL prefix for the resource

        """
        for url in urls:
            full_url = f"{prefix or ''}{url}"
            # Convert Flask URL parameters to OpenAPI parameters
            openapi_path = self._convert_flask_path_to_openapi_path(full_url)

            # Process HTTP methods and build operations
            http_methods = [
                "get",
                "post",
                "put",
                "delete",
                "patch",
                "head",
                "options",
            ]

            operations = {}
            for method_name in http_methods:
                if hasattr(resource, method_name):
                    method = getattr(resource, method_name)
                    operation = self._build_operation_from_method(method, resource)

                    # Add parameters from URL
                    path_params = self._extract_path_parameters(full_url)
                    if path_params:
                        if "parameters" not in operation:
                            operation["parameters"] = []

                        # Add path parameters without duplicates
                        existing_param_names = {p["name"] for p in operation["parameters"] if p["in"] == "path"}
                        for param in path_params:
                            if param["name"] not in existing_param_names:
                                operation["parameters"].append(param)
                                existing_param_names.add(param["name"])

                    operations[method_name] = operation

            # Update paths in a thread-safe manner
            with self._paths_lock:
                # Initialize path item if it doesn't exist
                if openapi_path not in self.paths:
                    self.paths[openapi_path] = {}

                # Add all operations at once
                for method_name, operation in operations.items():
                    self.paths[openapi_path][method_name] = operation

    def _convert_flask_path_to_openapi_path(self, flask_path: str) -> str:
        """Convert a Flask URL path to an OpenAPI path.

        Args:
            flask_path: The Flask URL path

        Returns:
            The OpenAPI path

        """
        from .cache import get_parameter_prefixes

        # Get parameter prefixes from current configuration
        _, _, path_prefix, _ = get_parameter_prefixes()
        path_prefix_len = len(path_prefix) + 1  # +1 for the underscore

        # Replace Flask's <converter:param> with OpenAPI's {param}
        # and remove any prefix from the parameter name
        def replace_param(match: re.Match) -> str:
            param_name = match.group(1)

            # Remove prefix if present (e.g., _x_path_)
            if param_name.startswith(f"{path_prefix}_"):
                param_name = param_name[path_prefix_len:]

            return f"{{{param_name}}}"

        return re.sub(r"<(?:[^:>]+:)?([^>]+)>", replace_param, flask_path)

    def _extract_path_parameters(self, flask_path: str) -> list[dict[str, Any]]:
        """Extract path parameters from a Flask URL path.

        Args:
            flask_path: The Flask URL path

        Returns:
            A list of OpenAPI parameter objects

        """
        from .cache import get_parameter_prefixes

        # Get parameter prefixes from current configuration
        _, _, path_prefix, _ = get_parameter_prefixes()
        path_prefix_len = len(path_prefix) + 1  # +1 for the underscore

        parameters = []
        # Match Flask's <converter:param> or <param>
        for match in re.finditer(r"<(?:([^:>]+):)?([^>]+)>", flask_path):
            converter, param_name = match.groups()

            # Remove prefix if present (e.g., _x_path_)
            actual_param_name = param_name
            if param_name.startswith(f"{path_prefix}_"):
                actual_param_name = param_name[path_prefix_len:]

            param = {
                "name": actual_param_name,
                "in": "path",
                "required": True,
                "schema": self._get_schema_for_converter(converter or "string"),
            }
            parameters.append(param)
        return parameters

    def _get_schema_for_converter(self, converter: str) -> dict[str, Any]:
        """Get an OpenAPI schema for a Flask URL converter.

        Args:
            converter: The Flask URL converter

        Returns:
            An OpenAPI schema object

        """
        # Map Flask URL converters to OpenAPI types
        converter_map = {
            "string": {"type": "string"},
            "int": {"type": "integer"},
            "float": {"type": "number", "format": "float"},
            "path": {"type": "string"},
            "uuid": {"type": "string", "format": "uuid"},
            "any": {"type": "string"},
        }
        return converter_map.get(converter, {"type": "string"})

    def _build_operation_from_method(self, method: Any, resource_cls: Any) -> dict[str, Any]:
        """Build an OpenAPI operation object from a Flask-RESTful resource method.

        Args:
            method: The resource method
            resource_cls: The resource class

        Returns:
            An OpenAPI operation object

        """
        operation: dict[str, Any] = {}

        # Get metadata from method if available
        metadata = getattr(method, "_openapi_metadata", {})

        # Process metadata, handling I18nString values
        for key, value in metadata.items():
            if isinstance(value, I18nStr):
                operation[key] = value.get(self.language)
            elif isinstance(value, dict):
                # Handle nested dictionaries that might contain I18nString values
                operation[key] = self._process_i18n_dict(value)
            else:
                operation[key] = value

        # Extract summary and description from docstring
        if method.__doc__:
            docstring = method.__doc__.strip()
            lines = docstring.split("\n")
            operation["summary"] = lines[0].strip()
            if len(lines) > 1:
                operation["description"] = "\n".join(line.strip() for line in lines[1:]).strip()

        # Get operation ID
        if "operationId" not in operation:
            operation["operationId"] = _get_operation_id(resource_cls.__name__, method.__name__)

        # Extract request and response schemas from type annotations
        self._add_request_schema(method, operation)
        self._add_response_schema(method, operation)

        return operation

    def _add_request_schema(self, method: Any, operation: dict[str, Any]) -> None:
        """Add request schema to an OpenAPI operation based on method type annotations.

        Args:
            method: The resource method
            operation: The OpenAPI operation object to update

        """
        type_hints = get_type_hints(method)

        # Look for parameters that might be request bodies
        for param_name, param_type in type_hints.items():
            if param_name == "return":
                continue

            # Check if the parameter is a Pydantic model
            if isinstance(param_type, type) and issubclass(param_type, BaseModel):
                self._register_model(param_type)

                # Check if this is a file upload model
                is_file_upload = False
                has_binary_fields = False

                # Check model config for multipart/form-data flag
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

                # Check if model has any binary fields
                if hasattr(param_type, "model_fields"):
                    for field_info in param_type.model_fields.values():
                        field_schema = getattr(field_info, "json_schema_extra", None)
                        if field_schema is not None and field_schema.get("format") == "binary":
                            has_binary_fields = True
                            break

                # Determine content type based on model properties
                content_type = "multipart/form-data" if (is_file_upload or has_binary_fields) else "application/json"

                # Add request body with appropriate content type
                operation["requestBody"] = {
                    "content": {content_type: {"schema": {"$ref": f"#/components/schemas/{param_type.__name__}"}}},
                    "required": True,
                }

                # If this is a file upload model, remove any file parameters from parameters
                # as they will be included in the requestBody
                if (is_file_upload or has_binary_fields) and "parameters" in operation:
                    # Keep only path and query parameters
                    operation["parameters"] = [p for p in operation["parameters"] if p["in"] in ["path", "query"]]
                break

    def _add_response_schema(self, method: Any, operation: dict[str, Any]) -> None:
        """Add response schema to an OpenAPI operation based on method return type annotation.

        Args:
            method: The resource method
            operation: The OpenAPI operation object to update

        """
        type_hints = get_type_hints(method)

        # Check if there's a return type hint
        if "return" in type_hints:
            return_type = type_hints["return"]

            # Handle Pydantic models
            if isinstance(return_type, type) and issubclass(return_type, BaseModel):
                self._register_model(return_type)

                operation["responses"] = {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {"schema": {"$ref": f"#/components/schemas/{return_type.__name__}"}},
                        },
                    },
                }
            else:
                # Default response
                operation["responses"] = {"200": {"description": "Successful response"}}
        else:
            # Default response if no return type is specified
            operation["responses"] = {"200": {"description": "Successful response"}}

    def _register_model(self, model: type) -> None:
        """Register a Pydantic model or enum in the components schemas.

        Args:
            model: The model to register (Pydantic model or enum)

        """
        with self._models_lock:
            # Skip if already registered
            if model in self._registered_models:
                return

            # Add to registered models set
            self._registered_models.add(model)

        # Handle enum types
        if hasattr(model, "__members__"):
            # This is an enum type
            with self._components_lock:
                enum_schema = {"type": "string", "enum": [e.value for e in model]}

                if model.__name__ not in self.components["schemas"]:
                    self.components["schemas"][model.__name__] = enum_schema
            return

        # Handle Pydantic models
        if not issubclass(model, BaseModel):
            return

        if issubclass(model, I18nBaseModel):
            # Create a language-specific version of the model
            language_model = model.for_language(self.language)
            schema = pydantic_to_openapi_schema(language_model)
        else:
            # Use the cached version from utils.py
            schema = pydantic_to_openapi_schema(model)

        # Update components in a thread-safe manner
        with self._components_lock:
            self.components["schemas"][model.__name__] = schema

        # Register nested models
        self._register_nested_models(model)

    def _register_nested_models(self, model: type[BaseModel]) -> None:
        """Register nested Pydantic models found in fields of the given model.

        Args:
            model: The Pydantic model to scan for nested models

        """
        # Get model fields
        if not hasattr(model, "model_fields"):
            return

        # Check each field for nested models
        for field_info in model.model_fields.values():
            field_type = field_info.annotation

            # Handle direct BaseModel references
            if isinstance(field_type, type) and issubclass(field_type, BaseModel):
                self._register_model(field_type)
                continue

            # Handle List[BaseModel] and similar container types
            origin = getattr(field_type, "__origin__", None)
            args = getattr(field_type, "__args__", [])

            if origin and args:
                for arg in args:
                    if isinstance(arg, type) and issubclass(arg, BaseModel):
                        self._register_model(arg)
                    elif hasattr(arg, "__members__"):
                        # Handle enum types
                        # Register enum in components/schemas
                        with self._components_lock:
                            enum_schema = {
                                "type": "string",
                                "enum": [e.value for e in arg],
                            }

                            if arg.__name__ not in self.components["schemas"]:
                                self.components["schemas"][arg.__name__] = enum_schema

            # Handle enum types directly
            elif hasattr(field_type, "__members__"):
                # Register enum in components/schemas
                with self._components_lock:
                    enum_schema = {
                        "type": "string",
                        "enum": [e.value for e in field_type],
                    }

                    if field_type.__name__ not in self.components["schemas"]:
                        self.components["schemas"][field_type.__name__] = enum_schema

    def _process_i18n_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Process a dictionary that might contain I18nString values.

        Args:
            data: The dictionary to process

        Returns:
            A new dictionary with I18nString values converted to strings

        """
        return process_i18n_dict(data, self.language)

    def _process_i18n_value(self, value: Any) -> Any:
        """Process a value that might be an I18nString or contain I18nString values.

        Args:
            value: The value to process

        Returns:
            The processed value

        """
        return process_i18n_value(value, self.language)

    def generate_schema(self) -> dict[str, Any]:
        """Generate the complete OpenAPI schema.

        Returns:
            The OpenAPI schema as a dictionary

        """
        # Use a lock to ensure consistent state during schema generation
        with self._lock:
            # Get OpenAPI configuration
            config = get_openapi_config()

            schema = {
                "openapi": config.openapi_version,
                "info": {
                    "title": self.title,
                    "version": self.version,
                    "description": self.description,
                },
                "paths": self.paths,
                "components": self.components,
                "tags": self.tags,
            }

            # Add webhooks if defined
            if self.webhooks:
                schema["webhooks"] = self.webhooks

            # Add servers if defined in config
            if config.servers:
                schema["servers"] = config.servers

            # Add external docs if defined in config
            if config.external_docs:
                schema["externalDocs"] = config.external_docs

            # Add JSON Schema dialect if defined in config
            if config.json_schema_dialect:
                schema["jsonSchemaDialect"] = config.json_schema_dialect

            return schema

```

##### `__init__(title=None, version=None, description=None, language=None)`

Initialize the OpenAPI schema generator.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `title` | `str | None` | The title of the API (default: from config) | `None` | | `version` | `str | None` | The version of the API (default: from config) | `None` | | `description` | `str | None` | The description of the API (default: from config) | `None` | | `language` | `str | None` | The language to use for internationalized strings (default: current language) | `None` |

Source code in `src/flask_x_openapi_schema/core/schema_generator.py`

```python
def __init__(
    self,
    title: str | None = None,
    version: str | None = None,
    description: str | None = None,
    language: str | None = None,
) -> None:
    """Initialize the OpenAPI schema generator.

    Args:
        title: The title of the API (default: from config)
        version: The version of the API (default: from config)
        description: The description of the API (default: from config)
        language: The language to use for internationalized strings (default: current language)

    """
    # Get defaults from config if not provided
    config = get_openapi_config()

    # Handle I18nString for title and description
    self.title = title if title is not None else config.title
    if isinstance(self.title, I18nStr):
        self.title = self.title.get(language)

    self.version = version if version is not None else config.version

    self.description = description if description is not None else config.description
    if isinstance(self.description, I18nStr):
        self.description = self.description.get(language)

    self.language = language or get_current_language()

    # Initialize data structures
    self.paths: dict[str, dict[str, Any]] = {}
    self.components: dict[str, dict[str, Any]] = {
        "schemas": {},
        "securitySchemes": config.security_schemes.copy() if config.security_schemes else {},
    }
    self.tags: list[dict[str, str]] = []
    self.webhooks: dict[str, dict[str, Any]] = {}
    self._registered_models: set[type[BaseModel]] = set()

    # Thread safety locks
    self._lock = threading.RLock()  # Main lock for coordinating access
    self._paths_lock = threading.RLock()
    self._components_lock = threading.RLock()
    self._tags_lock = threading.RLock()
    self._models_lock = threading.RLock()
    self._webhooks_lock = threading.RLock()

```

##### `add_security_scheme(name, scheme)`

Add a security scheme to the OpenAPI schema.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `name` | `str` | The name of the security scheme | *required* | | `scheme` | `dict[str, Any]` | The security scheme definition | *required* |

Source code in `src/flask_x_openapi_schema/core/schema_generator.py`

```python
def add_security_scheme(self, name: str, scheme: dict[str, Any]) -> None:
    """Add a security scheme to the OpenAPI schema.

    Args:
        name: The name of the security scheme
        scheme: The security scheme definition

    """
    with self._components_lock:
        self.components["securitySchemes"][name] = scheme

```

##### `add_tag(name, description='')`

Add a tag to the OpenAPI schema.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `name` | `str` | The name of the tag | *required* | | `description` | `str` | The description of the tag | `''` |

Source code in `src/flask_x_openapi_schema/core/schema_generator.py`

```python
def add_tag(self, name: str, description: str = "") -> None:
    """Add a tag to the OpenAPI schema.

    Args:
        name: The name of the tag
        description: The description of the tag

    """
    with self._tags_lock:
        self.tags.append({"name": name, "description": description})

```

##### `add_webhook(name, webhook_data)`

Add a webhook to the OpenAPI schema.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `name` | `str` | The name of the webhook | *required* | | `webhook_data` | `dict[str, Any]` | The webhook definition | *required* |

Source code in `src/flask_x_openapi_schema/core/schema_generator.py`

```python
def add_webhook(self, name: str, webhook_data: dict[str, Any]) -> None:
    """Add a webhook to the OpenAPI schema.

    Args:
        name: The name of the webhook
        webhook_data: The webhook definition

    """
    with self._webhooks_lock:
        self.webhooks[name] = webhook_data

```

##### `generate_schema()`

Generate the complete OpenAPI schema.

Returns:

| Type | Description | | --- | --- | | `dict[str, Any]` | The OpenAPI schema as a dictionary |

Source code in `src/flask_x_openapi_schema/core/schema_generator.py`

```python
def generate_schema(self) -> dict[str, Any]:
    """Generate the complete OpenAPI schema.

    Returns:
        The OpenAPI schema as a dictionary

    """
    # Use a lock to ensure consistent state during schema generation
    with self._lock:
        # Get OpenAPI configuration
        config = get_openapi_config()

        schema = {
            "openapi": config.openapi_version,
            "info": {
                "title": self.title,
                "version": self.version,
                "description": self.description,
            },
            "paths": self.paths,
            "components": self.components,
            "tags": self.tags,
        }

        # Add webhooks if defined
        if self.webhooks:
            schema["webhooks"] = self.webhooks

        # Add servers if defined in config
        if config.servers:
            schema["servers"] = config.servers

        # Add external docs if defined in config
        if config.external_docs:
            schema["externalDocs"] = config.external_docs

        # Add JSON Schema dialect if defined in config
        if config.json_schema_dialect:
            schema["jsonSchemaDialect"] = config.json_schema_dialect

        return schema

```

##### `scan_blueprint(blueprint)`

Scan a Flask blueprint for API resources and add them to the schema.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `blueprint` | `Blueprint` | The Flask blueprint to scan | *required* |

Source code in `src/flask_x_openapi_schema/core/schema_generator.py`

```python
def scan_blueprint(self, blueprint: Blueprint) -> None:
    """Scan a Flask blueprint for API resources and add them to the schema.

    Args:
        blueprint: The Flask blueprint to scan

    """
    # Get all resources registered to the blueprint
    if not hasattr(blueprint, "resources"):
        return

    for resource, urls, _ in blueprint.resources:
        self._process_resource(resource, urls, blueprint.url_prefix)

```

## Utilities

Utility functions for OpenAPI schema generation.

This module provides utility functions for converting Pydantic models to OpenAPI schemas, handling references, and processing internationalized strings. It includes functions for:

- Converting Pydantic models to OpenAPI schemas
- Converting Python types to OpenAPI types
- Generating response schemas for API endpoints
- Processing internationalized strings in schemas

#### `clear_i18n_cache()`

Clear the i18n processing cache.

Clears any cached results from I18n string processing functions. Call this function when you need to ensure that I18n strings are re-processed, such as after changing the language configuration.

Source code in `src/flask_x_openapi_schema/core/utils.py`

```python
def clear_i18n_cache() -> None:
    """Clear the i18n processing cache.

    Clears any cached results from I18n string processing functions.
    Call this function when you need to ensure that I18n strings are
    re-processed, such as after changing the language configuration.
    """

```

#### `clear_references_cache()`

Clear the references processing cache.

Clears any cached results from schema reference processing functions. Call this function when you need to ensure that schema references are re-processed, such as after modifying schema definitions.

Source code in `src/flask_x_openapi_schema/core/utils.py`

```python
def clear_references_cache() -> None:
    """Clear the references processing cache.

    Clears any cached results from schema reference processing functions.
    Call this function when you need to ensure that schema references are
    re-processed, such as after modifying schema definitions.
    """

```

#### `error_response_schema(description, status_code=400)`

Generate an OpenAPI error response schema.

Creates a simple OpenAPI error response object with a description. Unlike success responses, error responses don't include content schema.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `description` | `str` | Description of the error | *required* | | `status_code` | `int | str` | HTTP status code for the error (default: 400) | `400` |

Returns:

| Name | Type | Description | | --- | --- | --- | | `dict` | `dict[str, Any]` | An OpenAPI error response schema object |

Examples:

```pycon
>>> schema = error_response_schema("Bad Request", 400)
>>> schema["400"]["description"]
'Bad Request'

```

Source code in `src/flask_x_openapi_schema/core/utils.py`

```python
def error_response_schema(
    description: str,
    status_code: int | str = 400,
) -> dict[str, Any]:
    """Generate an OpenAPI error response schema.

    Creates a simple OpenAPI error response object with a description.
    Unlike success responses, error responses don't include content schema.

    Args:
        description: Description of the error
        status_code: HTTP status code for the error (default: 400)

    Returns:
        dict: An OpenAPI error response schema object

    Examples:
        >>> schema = error_response_schema("Bad Request", 400)
        >>> schema["400"]["description"]
        'Bad Request'

    """
    return {
        str(status_code): {
            "description": description,
        },
    }

```

#### `process_i18n_dict(data, language)`

Process a dictionary that might contain I18nString values.

Recursively processes all I18nString values in a dictionary, converting them to language-specific strings. Also handles nested dictionaries and lists that might contain I18nString values.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `data` | `dict[str, Any]` | The dictionary to process, which might contain I18nString values | *required* | | `language` | `str` | The language code to use for extracting localized strings | *required* |

Returns:

| Name | Type | Description | | --- | --- | --- | | `dict` | `dict[str, Any]` | A new dictionary with I18nString values converted to language-specific strings |

Examples:

```pycon
>>> from flask_x_openapi_schema.i18n.i18n_string import I18nStr
>>> data = {
...     "title": I18nStr({"en": "Hello", "fr": "Bonjour"}),
...     "nested": {"subtitle": I18nStr({"en": "World", "fr": "Monde"})},
... }
>>> result = process_i18n_dict(data, "en")
>>> result["title"]
'Hello'
>>> result["nested"]["subtitle"]
'World'

```

Source code in `src/flask_x_openapi_schema/core/utils.py`

```python
def process_i18n_dict(data: dict[str, Any], language: str) -> dict[str, Any]:
    """Process a dictionary that might contain I18nString values.

    Recursively processes all I18nString values in a dictionary, converting them
    to language-specific strings. Also handles nested dictionaries and lists that
    might contain I18nString values.

    Args:
        data: The dictionary to process, which might contain I18nString values
        language: The language code to use for extracting localized strings

    Returns:
        dict: A new dictionary with I18nString values converted to language-specific strings

    Examples:
        >>> from flask_x_openapi_schema.i18n.i18n_string import I18nStr
        >>> data = {
        ...     "title": I18nStr({"en": "Hello", "fr": "Bonjour"}),
        ...     "nested": {"subtitle": I18nStr({"en": "World", "fr": "Monde"})},
        ... }
        >>> result = process_i18n_dict(data, "en")
        >>> result["title"]
        'Hello'
        >>> result["nested"]["subtitle"]
        'World'

    """
    from flask_x_openapi_schema.i18n.i18n_string import I18nStr

    result = {}
    for key, value in data.items():
        if isinstance(value, I18nStr):
            result[key] = value.get(language)
        elif isinstance(value, dict):
            result[key] = process_i18n_dict(value, language)
        elif isinstance(value, list):
            result[key] = [process_i18n_value(item, language) for item in value]
        else:
            result[key] = value

    return result

```

#### `process_i18n_value(value, language)`

Process a value that might be an I18nString or contain I18nString values.

Recursively processes values that might be I18nString instances or contain I18nString instances (in lists or dictionaries). For I18nString instances, returns the string for the specified language.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `value` | `Any` | The value to process, which might be an I18nString or contain I18nString values | *required* | | `language` | `str` | The language code to use for extracting localized strings | *required* |

Returns:

| Name | Type | Description | | --- | --- | --- | | `Any` | `Any` | The processed value with I18nString instances replaced by their language-specific strings |

Examples:

```pycon
>>> from flask_x_openapi_schema.i18n.i18n_string import I18nStr
>>> i18n_str = I18nStr({"en": "Hello", "fr": "Bonjour"})
>>> process_i18n_value(i18n_str, "en")
'Hello'
>>> process_i18n_value(i18n_str, "fr")
'Bonjour'
>>> process_i18n_value({"greeting": i18n_str}, "en")
{'greeting': 'Hello'}

```

Source code in `src/flask_x_openapi_schema/core/utils.py`

```python
def process_i18n_value(value: Any, language: str) -> Any:
    """Process a value that might be an I18nString or contain I18nString values.

    Recursively processes values that might be I18nString instances or contain
    I18nString instances (in lists or dictionaries). For I18nString instances,
    returns the string for the specified language.

    Args:
        value: The value to process, which might be an I18nString or contain I18nString values
        language: The language code to use for extracting localized strings

    Returns:
        Any: The processed value with I18nString instances replaced by their
            language-specific strings

    Examples:
        >>> from flask_x_openapi_schema.i18n.i18n_string import I18nStr
        >>> i18n_str = I18nStr({"en": "Hello", "fr": "Bonjour"})
        >>> process_i18n_value(i18n_str, "en")
        'Hello'
        >>> process_i18n_value(i18n_str, "fr")
        'Bonjour'
        >>> process_i18n_value({"greeting": i18n_str}, "en")
        {'greeting': 'Hello'}

    """
    from flask_x_openapi_schema.i18n.i18n_string import I18nStr

    if not isinstance(value, (I18nStr, dict, list)):
        return value

    if isinstance(value, I18nStr):
        return value.get(language)
    if isinstance(value, dict):
        return process_i18n_dict(value, language)
    if isinstance(value, list):
        return [process_i18n_value(item, language) for item in value]
    return value

```

#### `pydantic_to_openapi_schema(model)`

Convert a Pydantic model to an OpenAPI schema.

Extracts schema information from a Pydantic model and converts it to a format compatible with OpenAPI specifications. The function handles property types, required fields, and includes the model's docstring as the schema description.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `model` | `type[BaseModel]` | The Pydantic model class to convert to an OpenAPI schema | *required* |

Returns:

| Name | Type | Description | | --- | --- | --- | | `dict` | `dict[str, Any]` | The OpenAPI schema representation of the model |

Examples:

```pycon
>>> from pydantic import BaseModel, Field
>>> class User(BaseModel):
...     '''A user model.'''
...
...     name: str = Field(..., description="The user's name")
...     age: int = Field(..., description="The user's age")
>>> schema = pydantic_to_openapi_schema(User)
>>> schema["type"]
'object'
>>> "name" in schema["properties"]
True
>>> "age" in schema["properties"]
True
>>> schema["description"]
'A user model.'

```

Source code in `src/flask_x_openapi_schema/core/utils.py`

```python
def pydantic_to_openapi_schema(model: type[BaseModel]) -> dict[str, Any]:
    """Convert a Pydantic model to an OpenAPI schema.

    Extracts schema information from a Pydantic model and converts it to a format
    compatible with OpenAPI specifications. The function handles property types,
    required fields, and includes the model's docstring as the schema description.

    Args:
        model: The Pydantic model class to convert to an OpenAPI schema

    Returns:
        dict: The OpenAPI schema representation of the model

    Examples:
        >>> from pydantic import BaseModel, Field
        >>> class User(BaseModel):
        ...     '''A user model.'''
        ...
        ...     name: str = Field(..., description="The user's name")
        ...     age: int = Field(..., description="The user's age")
        >>> schema = pydantic_to_openapi_schema(User)
        >>> schema["type"]
        'object'
        >>> "name" in schema["properties"]
        True
        >>> "age" in schema["properties"]
        True
        >>> schema["description"]
        'A user model.'

    """
    schema: dict[str, Any] = {"type": "object", "properties": {}, "required": []}

    model_schema = model.model_json_schema()

    if "properties" in model_schema:
        properties = {}
        for prop_name, prop_schema in model_schema["properties"].items():
            properties[prop_name] = _fix_references(prop_schema)
        schema["properties"] = properties

    if "required" in model_schema:
        schema["required"] = model_schema["required"]

    if model.__doc__:
        schema["description"] = model.__doc__.strip()

    return schema

```

#### `python_type_to_openapi_type(python_type)`

Convert a Python type to an OpenAPI type.

Maps Python types to their corresponding OpenAPI type definitions. Handles basic types, container types (lists, dicts), and special types like UUID and datetime. Also supports Union types and Pydantic models.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `python_type` | `Any` | The Python type to convert to an OpenAPI type | *required* |

Returns:

| Name | Type | Description | | --- | --- | --- | | `dict` | `dict[str, Any]` | The OpenAPI type definition for the given Python type |

Examples:

```pycon
>>> python_type_to_openapi_type(str)
{'type': 'string'}
>>> python_type_to_openapi_type(int)
{'type': 'integer'}
>>> python_type_to_openapi_type(list[str])["type"]
'array'

```

Source code in `src/flask_x_openapi_schema/core/utils.py`

```python
def python_type_to_openapi_type(python_type: Any) -> dict[str, Any]:
    """Convert a Python type to an OpenAPI type.

    Maps Python types to their corresponding OpenAPI type definitions. Handles
    basic types, container types (lists, dicts), and special types like UUID
    and datetime. Also supports Union types and Pydantic models.

    Args:
        python_type: The Python type to convert to an OpenAPI type

    Returns:
        dict: The OpenAPI type definition for the given Python type

    Examples:
        >>> python_type_to_openapi_type(str)
        {'type': 'string'}
        >>> python_type_to_openapi_type(int)
        {'type': 'integer'}
        >>> python_type_to_openapi_type(list[str])["type"]
        'array'

    """
    from .config import get_openapi_config

    config = get_openapi_config()
    is_openapi_31 = config.openapi_version.startswith("3.1")

    if python_type is str:
        return {"type": "string"}
    if python_type is int:
        return {"type": "integer"}
    if python_type is float:
        return {"type": "number"}
    if python_type is bool:
        return {"type": "boolean"}
    if python_type is None or python_type is type(None):
        return {"type": "null"} if is_openapi_31 else {"nullable": True}

    origin = getattr(python_type, "__origin__", None)
    if python_type is list or origin is list:
        args = getattr(python_type, "__args__", [])
        if args:
            item_type = python_type_to_openapi_type(args[0])
            return {"type": "array", "items": item_type}
        return {"type": "array"}
    if python_type is dict or origin is dict:
        args = getattr(python_type, "__args__", [])
        if len(args) == 2 and is_openapi_31 and args[0] is str:
            value_type = python_type_to_openapi_type(args[1])
            return {"type": "object", "additionalProperties": value_type}
        return {"type": "object"}

    if python_type == UUID:
        return {"type": "string", "format": "uuid"}
    if python_type == datetime:
        return {"type": "string", "format": "date-time"}
    if python_type == date:
        return {"type": "string", "format": "date"}
    if python_type == time:
        return {"type": "string", "format": "time"}

    if inspect.isclass(python_type):
        if issubclass(python_type, Enum):
            return {"type": "string", "enum": [e.value for e in python_type]}
        if issubclass(python_type, BaseModel):
            return {"$ref": f"#/components/schemas/{python_type.__name__}"}

    if origin is Union:
        args = getattr(python_type, "__args__", [])
        if len(args) == 2 and args[1] is type(None):
            inner_type = python_type_to_openapi_type(args[0])
            if is_openapi_31:
                if "type" in inner_type:
                    if isinstance(inner_type["type"], list):
                        if "null" not in inner_type["type"]:
                            inner_type["type"].append("null")
                    else:
                        inner_type["type"] = [inner_type["type"], "null"]
                else:
                    inner_type = {"oneOf": [inner_type, {"type": "null"}]}
            else:
                inner_type["nullable"] = True
            return inner_type

        if is_openapi_31 and len(args) > 1:
            return {"oneOf": [python_type_to_openapi_type(arg) for arg in args]}

    return {"type": "string"}

```

#### `response_schema(model, description, status_code=200)`

Generate an OpenAPI response schema for a Pydantic model.

Creates an OpenAPI response object that references a Pydantic model schema. The response includes a description and specifies that the content type is application/json.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `model` | `type[BaseModel]` | The Pydantic model to use for the response schema | *required* | | `description` | `str` | Description of the response | *required* | | `status_code` | `int | str` | HTTP status code for the response (default: 200) | `200` |

Returns:

| Name | Type | Description | | --- | --- | --- | | `dict` | `dict[str, Any]` | An OpenAPI response schema object |

Examples:

```pycon
>>> from pydantic import BaseModel
>>> class User(BaseModel):
...     name: str
...     age: int
>>> schema = response_schema(User, "A user object", 200)
>>> schema["200"]["description"]
'A user object'
>>> schema["200"]["content"]["application/json"]["schema"]["$ref"]
'#/components/schemas/User'

```

Source code in `src/flask_x_openapi_schema/core/utils.py`

```python
def response_schema(
    model: type[BaseModel],
    description: str,
    status_code: int | str = 200,
) -> dict[str, Any]:
    """Generate an OpenAPI response schema for a Pydantic model.

    Creates an OpenAPI response object that references a Pydantic model schema.
    The response includes a description and specifies that the content type is
    application/json.

    Args:
        model: The Pydantic model to use for the response schema
        description: Description of the response
        status_code: HTTP status code for the response (default: 200)

    Returns:
        dict: An OpenAPI response schema object

    Examples:
        >>> from pydantic import BaseModel
        >>> class User(BaseModel):
        ...     name: str
        ...     age: int
        >>> schema = response_schema(User, "A user object", 200)
        >>> schema["200"]["description"]
        'A user object'
        >>> schema["200"]["content"]["application/json"]["schema"]["$ref"]
        '#/components/schemas/User'

    """
    return {
        str(status_code): {
            "description": description,
            "content": {"application/json": {"schema": {"$ref": f"#/components/schemas/{model.__name__}"}}},
        },
    }

```

#### `responses_schema(success_responses, errors=None)`

Generate a complete OpenAPI responses schema with success and error responses.

Creates a comprehensive OpenAPI responses object that includes both success responses (with schemas) and error responses. This is useful for documenting all possible responses from an API endpoint.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `success_responses` | `dict[int | str, tuple[type[BaseModel], str]]` | Dictionary mapping status codes to (model, description) tuples for success responses | *required* | | `errors` | `dict[int | str, str] | None` | Optional dictionary mapping status codes to descriptions for error responses | `None` |

Returns:

| Name | Type | Description | | --- | --- | --- | | `dict` | `dict[str, Any]` | A complete OpenAPI responses schema object |

Examples:

```pycon
>>> from pydantic import BaseModel
>>> class User(BaseModel):
...     name: str
>>> class Error(BaseModel):
...     message: str
>>> success = {200: success_response(User, "Success")}
>>> errors = {400: "Bad Request", 404: "Not Found"}
>>> schema = responses_schema(success, errors)
>>> "200" in schema and "400" in schema and "404" in schema
True

```

Source code in `src/flask_x_openapi_schema/core/utils.py`

```python
def responses_schema(
    success_responses: dict[int | str, tuple[type[BaseModel], str]],
    errors: dict[int | str, str] | None = None,
) -> dict[str, Any]:
    """Generate a complete OpenAPI responses schema with success and error responses.

    Creates a comprehensive OpenAPI responses object that includes both success
    responses (with schemas) and error responses. This is useful for documenting
    all possible responses from an API endpoint.

    Args:
        success_responses: Dictionary mapping status codes to (model, description)
            tuples for success responses
        errors: Optional dictionary mapping status codes to descriptions for error
            responses

    Returns:
        dict: A complete OpenAPI responses schema object

    Examples:
        >>> from pydantic import BaseModel
        >>> class User(BaseModel):
        ...     name: str
        >>> class Error(BaseModel):
        ...     message: str
        >>> success = {200: success_response(User, "Success")}
        >>> errors = {400: "Bad Request", 404: "Not Found"}
        >>> schema = responses_schema(success, errors)
        >>> "200" in schema and "400" in schema and "404" in schema
        True

    """
    responses = {}

    for status_code, (model, description) in success_responses.items():
        responses.update(response_schema(model, description, status_code))

    if errors:
        for status_code, description in errors.items():
            responses.update(error_response_schema(description, status_code))

    return responses

```

#### `success_response(model, description)`

Create a success response tuple for use with responses_schema.

Helper function that creates a tuple containing a model and description, which can be used with the responses_schema function to generate complete OpenAPI response schemas.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `model` | `type[BaseModel]` | The Pydantic model to use for the response schema | *required* | | `description` | `str` | Description of the response | *required* |

Returns:

| Name | Type | Description | | --- | --- | --- | | `tuple` | `tuple[type[BaseModel], str]` | A tuple of (model, description) for use with responses_schema |

Examples:

```pycon
>>> from pydantic import BaseModel
>>> class User(BaseModel):
...     name: str
>>> response = success_response(User, "A user object")
>>> response[0] == User
True
>>> response[1]
'A user object'

```

Source code in `src/flask_x_openapi_schema/core/utils.py`

```python
def success_response(
    model: type[BaseModel],
    description: str,
) -> tuple[type[BaseModel], str]:
    """Create a success response tuple for use with responses_schema.

    Helper function that creates a tuple containing a model and description,
    which can be used with the responses_schema function to generate complete
    OpenAPI response schemas.

    Args:
        model: The Pydantic model to use for the response schema
        description: Description of the response

    Returns:
        tuple: A tuple of (model, description) for use with responses_schema

    Examples:
        >>> from pydantic import BaseModel
        >>> class User(BaseModel):
        ...     name: str
        >>> response = success_response(User, "A user object")
        >>> response[0] == User
        True
        >>> response[1]
        'A user object'

    """
    return (model, description)

```
