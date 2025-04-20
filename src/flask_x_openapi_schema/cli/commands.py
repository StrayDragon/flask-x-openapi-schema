"""
Commands for generating OpenAPI documentation.
"""

import json
import os
from typing import Literal, Optional

import click
from flask import Flask
from flask.cli import with_appcontext

from ..i18n import I18nStr, set_current_language
from ..x.flask_restful import OpenAPIIntegrationMixin


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
    blueprint: Optional[str],
    title: str,
    version: str,
    description: str,
    format: Literal["yaml", "json"],
    language: list[str],
) -> None:
    """Generate OpenAPI schema and documentation."""
    from flask import current_app

    # Get all blueprints
    blueprints = []
    for name, bp in current_app.blueprints.items():
        if hasattr(bp, "resources") and (blueprint is None or name == blueprint):
            blueprints.append((name, bp))

    if not blueprints:
        click.echo(
            f"No blueprints found{' with name ' + blueprint if blueprint else ''}."
        )
        return

    # Create internationalized description
    i18n_description = I18nStr(dict.fromkeys(language, description))

    # Generate schema for each blueprint
    for name, bp in blueprints:
        if not hasattr(bp, "api") or not isinstance(bp.api, OpenAPIIntegrationMixin):
            click.echo(
                f"Blueprint {name} does not have an OpenAPIExternalApi instance."
            )
            continue

        api = bp.api

        # Set default language for initial schema generation
        default_lang = language[0] if language else "en"
        set_current_language(default_lang)

        # Generate schema with internationalized strings
        schema = api.generate_openapi_schema(
            title=I18nStr(dict.fromkeys(language, f"{title} - {name}")),
            version=version,
            description=i18n_description,
            output_format=format,
            language=default_lang,
        )

        # Save schema to file
        blueprint_output = output
        if len(blueprints) > 1:
            base, ext = os.path.splitext(output)
            blueprint_output = f"{base}_{name}{ext}"

        os.makedirs(os.path.dirname(os.path.abspath(blueprint_output)), exist_ok=True)
        with open(blueprint_output, "w") as f:
            if format == "yaml":
                # Schema is already a YAML string
                f.write(schema)
            else:
                # Schema is a dict, dump as JSON
                json.dump(schema, f, indent=2)

        click.echo(f"Generated OpenAPI schema for {name} blueprint: {blueprint_output}")


def register_commands(app: Flask) -> None:
    """
    Register OpenAPI commands with the Flask application.

    Args:
        app: The Flask application
    """
    app.cli.add_command(generate_openapi_command)
