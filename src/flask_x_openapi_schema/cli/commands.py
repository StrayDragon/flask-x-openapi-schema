"""CLI commands for generating OpenAPI documentation.

This module provides command-line interface tools for generating OpenAPI schema
documentation from Flask applications with registered blueprints that use the
OpenAPIIntegrationMixin.

Examples:
    To generate OpenAPI documentation for a Flask application:

    ```python
    from flask import Flask
    from flask_x_openapi_schema.cli.commands import register_commands

    app = Flask(__name__)
    register_commands(app)
    ```

    Then run the command:

    ```bash
    flask generate-openapi --output openapi.yaml
    ```

"""

import json
import os
from typing import Literal

import click
from flask import Flask
from flask.cli import with_appcontext

from flask_x_openapi_schema.i18n import I18nStr, set_current_language
from flask_x_openapi_schema.x.flask_restful import OpenAPIIntegrationMixin


@click.command("generate-openapi")
@click.option(
    "--output",
    "-o",
    default="openapi.yaml",
    help="Output file for the OpenAPI schema",
)
@click.option(
    "--blueprint",
    "-b",
    default="service_api",
    help="Blueprint to generate schema for (default: service_api)",
)
@click.option(
    "--title",
    default="API",
    help="API title",
)
@click.option(
    "--version",
    default="1.0.0",
    help="API version",
)
@click.option(
    "--description",
    default="API Documentation",
    help="API description",
)
@click.option(
    "--format",
    "-f",
    "format_",
    default="yaml",
    type=click.Choice(["yaml", "json"]),
    help="Output format (yaml or json)",
)
@click.option(
    "--language",
    "-l",
    multiple=True,
    default=["en"],
    help="Languages to generate documentation for (can be used multiple times)",
)
@with_appcontext
def generate_openapi_command(
    output: str,
    blueprint: str | None,
    title: str,
    version: str,
    description: str,
    format_: Literal["yaml", "json"],
    language: list[str],
) -> None:
    """Generate OpenAPI schema and documentation for Flask blueprints.

    This command generates OpenAPI schema documentation for Flask blueprints
    that have an OpenAPIIntegrationMixin API instance. The generated schema
    can be output in either YAML or JSON format.

    Args:
        output: Path to the output file for the OpenAPI schema
        blueprint: Name of the blueprint to generate schema for (default: service_api)
            If None, generates for all blueprints with resources
        title: Title for the API documentation
        version: Version string for the API documentation
        description: Description text for the API documentation
        format_: Output format, either "yaml" or "json"
        language: List of language codes to generate documentation for

    Examples:
        To generate OpenAPI schema for a specific blueprint:

        ```bash
        flask generate-openapi --blueprint=api --output=openapi.yaml
        ```

        To generate schema with multiple languages:

        ```bash
        flask generate-openapi --language=en --language=zh --output=openapi.yaml
        ```

    """
    from flask import current_app

    blueprints = []
    for name, bp in current_app.blueprints.items():
        if hasattr(bp, "resources") and (blueprint is None or name == blueprint):
            blueprints.append((name, bp))

    if not blueprints:
        click.echo(f"No blueprints found{' with name ' + blueprint if blueprint else ''}.")
        return

    i18n_description = I18nStr(dict.fromkeys(language, description))

    for name, bp in blueprints:
        if not hasattr(bp, "api") or not isinstance(bp.api, OpenAPIIntegrationMixin):
            click.echo(f"Blueprint {name} does not have an OpenAPIExternalApi instance.")
            continue

        api = bp.api

        default_lang = language[0] if language else "en"
        set_current_language(default_lang)

        schema = api.generate_openapi_schema(
            title=I18nStr(dict.fromkeys(language, f"{title} - {name}")),
            version=version,
            description=i18n_description,
            output_format=format_,
            language=default_lang,
        )

        blueprint_output = output
        if len(blueprints) > 1:
            base, ext = os.path.splitext(output)  # noqa: PTH122
            blueprint_output = f"{base}_{name}{ext}"

        os.makedirs(os.path.dirname(os.path.abspath(blueprint_output)), exist_ok=True)  # noqa: PTH100, PTH103, PTH120
        with open(blueprint_output, "w") as f:  # noqa: PTH123
            if format_ == "yaml":
                # Schema is already a YAML string
                f.write(schema)
            else:
                # Schema is a dict, dump as JSON
                json.dump(schema, f, indent=2)

        click.echo(f"Generated OpenAPI schema for {name} blueprint: {blueprint_output}")


def register_commands(app: Flask) -> None:
    """Register OpenAPI commands with the Flask application.

    This function adds the generate-openapi command to the Flask application's
    CLI command group, making it available through the flask command-line tool.

    Args:
        app: The Flask application instance to register commands with

    Examples:
        ```python
        from flask import Flask
        from flask_x_openapi_schema.cli.commands import register_commands

        app = Flask(__name__)
        register_commands(app)
        # Now 'flask generate-openapi' is available
        ```

    """
    app.cli.add_command(generate_openapi_command)
