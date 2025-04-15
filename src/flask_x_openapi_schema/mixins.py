"""
Extension for the ExternalApi class to collect OpenAPI metadata.
"""

from typing import Any, Literal, Optional, Union

import yaml

try:
    from flask_restful import Api

    HAS_FLASK_RESTFUL = True
except ImportError:
    HAS_FLASK_RESTFUL = False

    # Create a placeholder class for when Flask-RESTful is not available
    class Api:
        pass


from .decorators import ConventionalPrefixConfig, configure_prefixes, GLOBAL_CONFIG_HOLDER
from .i18n.i18n_string import I18nStr, get_current_language
from .methodview_utils import MethodViewOpenAPISchemaGenerator
from .schema_generator import OpenAPISchemaGenerator


class OpenAPIIntegrationMixin(Api):
    """
    A mixin class for the flask-restful Api to collect OpenAPI metadata.
    """

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
                    "request_body_prefix", GLOBAL_CONFIG_HOLDER.get().request_body_prefix
                ),
                request_query_prefix=kwargs.get(
                    "request_query_prefix", GLOBAL_CONFIG_HOLDER.get().request_query_prefix
                ),
                request_path_prefix=kwargs.get(
                    "request_path_prefix", GLOBAL_CONFIG_HOLDER.get().request_path_prefix
                ),
                request_file_prefix=kwargs.get(
                    "request_file_prefix", GLOBAL_CONFIG_HOLDER.get().request_file_prefix
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

        for resource, urls, _ in self.resources:
            generator._process_resource(resource, urls, self.blueprint.url_prefix)

        schema = generator.generate_schema()

        if output_format == "yaml":
            return yaml.dump(schema, sort_keys=False, default_flow_style=False)
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
                    "request_body_prefix", GLOBAL_CONFIG_HOLDER.get().request_body_prefix
                ),
                request_query_prefix=kwargs.get(
                    "request_query_prefix", GLOBAL_CONFIG_HOLDER.get().request_query_prefix
                ),
                request_path_prefix=kwargs.get(
                    "request_path_prefix", GLOBAL_CONFIG_HOLDER.get().request_path_prefix
                ),
                request_file_prefix=kwargs.get(
                    "request_file_prefix", GLOBAL_CONFIG_HOLDER.get().request_file_prefix
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
            return yaml.dump(schema, sort_keys=False, default_flow_style=False)
        else:
            return schema
