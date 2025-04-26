"""Extension for the Flask-RESTful Api class to collect OpenAPI metadata."""

from typing import Any, Literal

import yaml

from flask_x_openapi_schema._opt_deps._flask_restful import Api, Resource
from flask_x_openapi_schema.core.config import GLOBAL_CONFIG_HOLDER, ConventionalPrefixConfig, configure_prefixes
from flask_x_openapi_schema.core.schema_generator import OpenAPISchemaGenerator
from flask_x_openapi_schema.i18n.i18n_string import I18nStr, get_current_language
from flask_x_openapi_schema.x.flask.views import MethodViewOpenAPISchemaGenerator


class OpenAPIIntegrationMixin(Api):
    """A mixin class for the flask-restful Api to collect OpenAPI metadata.

    This mixin extends Flask-RESTful's Api class to add OpenAPI schema generation capabilities.
    It tracks resources added to the API and provides methods to generate OpenAPI schemas.

    :param args: Arguments to pass to the parent class
    :param kwargs: Keyword arguments to pass to the parent class

    Example:
        >>> from flask import Flask
        >>> from flask_restful import Resource
        >>> from flask_x_openapi_schema.x.flask_restful import OpenAPIIntegrationMixin, openapi_metadata
        >>> from pydantic import BaseModel, Field
        >>>
        >>> app = Flask(__name__)
        >>>
        >>> # Create an OpenAPI-enabled API
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
        >>> # Register the resource
        >>> api.add_resource(ItemResource, "/items/<item_id>")
        >>>
        >>> # Generate OpenAPI schema
        >>> @app.route("/openapi.yaml")
        >>> def get_openapi_spec():
        ...     schema = api.generate_openapi_schema(
        ...         title="My API", version="1.0.0", description="API for managing items"
        ...     )
        ...     return schema

    """

    def __init__(self, *args, **kwargs) -> None:
        """Initialize the mixin.

        :param args: Arguments to pass to the parent class
        :param kwargs: Keyword arguments to pass to the parent class
        """
        # 确保调用父类的 __init__ 方法
        super().__init__(*args, **kwargs)

        # 确保 resources 属性已初始化
        if not hasattr(self, "resources"):
            self.resources = []

    def add_resource(self, resource: Resource, *urls, **kwargs) -> Any:
        """Add a resource to the API and register it for OpenAPI schema generation.

        Args:
            resource: The resource class
            *urls: The URLs to register the resource with
            **kwargs: Additional arguments to pass to the parent method

        Returns:
            The result of the parent method

        """
        # 调用父类的 add_resource 方法
        result = super().add_resource(resource, *urls, **kwargs)

        # 手动添加资源到 resources 属性
        # 这是为了确保在测试中也能正确工作
        if not hasattr(self, "resources"):
            self.resources = []

        # 检查资源是否已经存在
        for existing_resource, existing_urls, _ in self.resources:
            if existing_resource == resource and set(existing_urls) == set(urls):
                return result

        # 添加资源
        # 确保将 endpoint 作为字典中的一个键值对存储
        if "endpoint" not in kwargs and kwargs is not None:
            kwargs["endpoint"] = resource.__name__.lower()
        elif kwargs is None:
            kwargs = {"endpoint": resource.__name__.lower()}

        self.resources.append((resource, urls, kwargs))

        return result

    def configure_openapi(self, *, prefix_config: ConventionalPrefixConfig = None, **kwargs) -> None:
        """Configure OpenAPI settings for this API instance.

        Args:
            prefix_config: Configuration object with parameter prefixes
            **kwargs: For backward compatibility - will be used to create a config object if prefix_config is None

        """
        if prefix_config is not None:
            configure_prefixes(prefix_config)
        elif kwargs:
            # Create a new config with the provided values
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

        :param title: The title of the API (can be an I18nString)
        :type title: Union[str, I18nStr]
        :param version: The version of the API
        :type version: str
        :param description: The description of the API (can be an I18nString)
        :type description: Union[str, I18nStr]
        :param output_format: The output format (json or yaml)
        :type output_format: Literal["json", "yaml"]
        :param language: The language to use for internationalized strings (default: current language)
        :type language: Optional[str]
        :return: The OpenAPI schema as a dictionary (if json) or string (if yaml)
        :rtype: Union[Dict[str, Any], str]

        Example:
            >>> # Generate schema in YAML format
            >>> yaml_schema = api.generate_openapi_schema(
            ...     title="My API", version="1.0.0", description="API for managing items"
            ... )
            >>>
            >>> # Generate schema in JSON format
            >>> json_schema = api.generate_openapi_schema(
            ...     title="My API", version="1.0.0", description="API for managing items", output_format="json"
            ... )
            >>>
            >>> # Generate schema with internationalized strings
            >>> from flask_x_openapi_schema import I18nStr
            >>> i18n_schema = api.generate_openapi_schema(
            ...     title=I18nStr({"en-US": "My API", "zh-Hans": "我的API"}),
            ...     version="1.0.0",
            ...     description=I18nStr({"en-US": "API for managing items", "zh-Hans": "用于管理项目的API"}),
            ...     language="zh-Hans",  # Use Chinese for the schema
            ... )

        """
        # Use the specified language or get the current language
        current_lang = language or get_current_language()

        generator = OpenAPISchemaGenerator(title, version, description, language=current_lang)

        # Get URL prefix from blueprint if available
        url_prefix = None
        if hasattr(self, "blueprint") and hasattr(self.blueprint, "url_prefix"):
            url_prefix = self.blueprint.url_prefix

        for resource, urls, _ in self.resources:
            generator._process_resource(resource, urls, url_prefix)  # noqa: SLF001

        schema = generator.generate_schema()

        if output_format == "yaml":
            return yaml.dump(schema, sort_keys=False, default_flow_style=False, allow_unicode=True)
        return schema


class OpenAPIBlueprintMixin:
    """A mixin class for Flask Blueprint to collect OpenAPI metadata from MethodView classes.

    This mixin extends Flask's Blueprint class to add OpenAPI schema generation capabilities
    for MethodView classes. It tracks MethodView classes registered to the blueprint and
    provides methods to generate OpenAPI schemas.

    Example:
        >>> from flask import Blueprint, Flask
        >>> from flask.views import MethodView
        >>> from flask_x_openapi_schema.x.flask_restful import OpenAPIBlueprintMixin
        >>> from flask_x_openapi_schema.x.flask import openapi_metadata, OpenAPIMethodViewMixin
        >>>
        >>> app = Flask(__name__)
        >>>
        >>> # Create an OpenAPI-enabled Blueprint
        >>> class OpenAPIBlueprint(OpenAPIBlueprintMixin, Blueprint):
        ...     pass
        >>>
        >>> bp = OpenAPIBlueprint("api", __name__, url_prefix="/api")
        >>>
        >>> # Create a MethodView with OpenAPI metadata
        >>> class ItemView(OpenAPIMethodViewMixin, MethodView):
        ...     @openapi_metadata(summary="Get an item")
        ...     def get(self, item_id):
        ...         return {"id": item_id, "name": "Example Item"}
        >>>
        >>> # Register the view to the blueprint
        >>> ItemView.register_to_blueprint(bp, "/items/<item_id>")
        >>>
        >>> # Register the blueprint to the app
        >>> app.register_blueprint(bp)
        >>>
        >>> # Generate OpenAPI schema
        >>> @app.route("/openapi.yaml")
        >>> def get_openapi_spec():
        ...     schema = bp.generate_openapi_schema(
        ...         title="My API", version="1.0.0", description="API for managing items"
        ...     )
        ...     return schema

    """

    def configure_openapi(self, *, prefix_config: ConventionalPrefixConfig = None, **kwargs) -> None:
        """Configure OpenAPI settings for this Blueprint instance.

        Args:
            prefix_config: Configuration object with parameter prefixes
            **kwargs: For backward compatibility - will be used to create a config object if prefix_config is None

        """
        if prefix_config is not None:
            configure_prefixes(prefix_config)
        elif kwargs:
            # Create a new config with the provided values
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

    def __init__(self, *args, **kwargs) -> None:  # noqa: D107
        super().__init__(*args, **kwargs)
        # Initialize a list to store MethodView resources
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
            title: The title of the API (can be an I18nString)
            version: The version of the API
            description: The description of the API (can be an I18nString)
            output_format: The output format (json or yaml)
            language: The language to use for internationalized strings (default: current language)

        Returns:
            The OpenAPI schema as a dictionary (if json) or string (if yaml)

        """
        # Use the specified language or get the current language
        current_lang = language or get_current_language()

        generator = MethodViewOpenAPISchemaGenerator(title, version, description, language=current_lang)

        # Process MethodView resources
        generator.process_methodview_resources(self)

        schema = generator.generate_schema()

        if output_format == "yaml":
            return yaml.dump(schema, sort_keys=False, default_flow_style=False, allow_unicode=True)
        return schema
