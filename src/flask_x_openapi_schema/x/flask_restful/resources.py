"""
Extension for the Flask-RESTful Api class to collect OpenAPI metadata.
"""

from typing import Any, Literal, Optional, Union

import yaml

from flask_x_openapi_schema._opt_deps._flask_restful import Api


from ...core.config import (
    ConventionalPrefixConfig,
    configure_prefixes,
    GLOBAL_CONFIG_HOLDER,
)
from ...core.schema_generator import OpenAPISchemaGenerator
from ...i18n.i18n_string import I18nStr, get_current_language
from ..flask.views import MethodViewOpenAPISchemaGenerator


class OpenAPIIntegrationMixin(Api):
    """
    A mixin class for the flask-restful Api to collect OpenAPI metadata.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the mixin.

        Args:
            *args: Arguments to pass to the parent class
            **kwargs: Keyword arguments to pass to the parent class
        """
        # 确保调用父类的 __init__ 方法
        super().__init__(*args, **kwargs)

        # 确保 resources 属性已初始化
        if not hasattr(self, "resources"):
            self.resources = []

    def add_resource(self, resource, *urls, **kwargs):
        """
        Add a resource to the API and register it for OpenAPI schema generation.

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

    def configure_openapi(
        self, *, prefix_config: ConventionalPrefixConfig = None, **kwargs
    ):
        """
        Configure OpenAPI settings for this API instance.

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
        title: Union[str, I18nStr],
        version: str,
        description: Union[str, I18nStr] = "",
        output_format: Literal["json", "yaml"] = "yaml",
        language: Optional[str] = None,
    ) -> Any:
        """
        Generate an OpenAPI schema for the API.

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

        generator = OpenAPISchemaGenerator(
            title, version, description, language=current_lang
        )

        # Get URL prefix from blueprint if available
        url_prefix = None
        if hasattr(self, "blueprint") and hasattr(self.blueprint, "url_prefix"):
            url_prefix = self.blueprint.url_prefix

        for resource, urls, _ in self.resources:
            generator._process_resource(resource, urls, url_prefix)

        schema = generator.generate_schema()

        if output_format == "yaml":
            return yaml.dump(
                schema, sort_keys=False, default_flow_style=False, allow_unicode=True
            )
        else:
            return schema


class OpenAPIBlueprintMixin:
    """
    A mixin class for Flask Blueprint to collect OpenAPI metadata from MethodView classes.
    """

    def configure_openapi(
        self, *, prefix_config: ConventionalPrefixConfig = None, **kwargs
    ):
        """
        Configure OpenAPI settings for this Blueprint instance.

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize a list to store MethodView resources
        self._methodview_openapi_resources = []

    def generate_openapi_schema(
        self,
        title: Union[str, I18nStr],
        version: str,
        description: Union[str, I18nStr] = "",
        output_format: Literal["json", "yaml"] = "yaml",
        language: Optional[str] = None,
    ) -> Any:
        """
        Generate an OpenAPI schema for the API.

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

        generator = MethodViewOpenAPISchemaGenerator(
            title, version, description, language=current_lang
        )

        # Process MethodView resources
        generator.process_methodview_resources(self)

        schema = generator.generate_schema()

        if output_format == "yaml":
            return yaml.dump(
                schema, sort_keys=False, default_flow_style=False, allow_unicode=True
            )
        else:
            return schema
