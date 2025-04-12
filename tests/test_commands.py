"""
Tests for the commands module.

This module tests the command-line interface for generating OpenAPI documentation.
"""

import json
import os
import pytest
import yaml
from click.testing import CliRunner
from flask import Blueprint, Flask
from flask_restful import Api, Resource

from flask_x_openapi_schema.commands import generate_openapi_command, register_commands
from flask_x_openapi_schema.mixins import OpenAPIIntegrationMixin


class SampleOpenAPIApi(OpenAPIIntegrationMixin, Api):
    """Test API class with OpenAPI integration."""

    pass


@pytest.fixture
def app():
    """Create a Flask app for testing."""
    app = Flask(__name__)
    return app


@pytest.fixture
def blueprint():
    """Create a blueprint with OpenAPI API."""
    bp = Blueprint("service_api", __name__)
    api = SampleOpenAPIApi(bp)

    # Mock the generate_openapi_schema method
    def mock_generate_openapi_schema(
        title, version, description, output_format="yaml", language=None
    ):
        schema = {
            "openapi": "3.0.0",
            "info": {
                "title": str(title),
                "version": version,
                "description": str(description),
            },
            "paths": {},
        }

        if output_format == "yaml":
            return yaml.dump(schema)
        return schema

    api.generate_openapi_schema = mock_generate_openapi_schema

    # Add resources attribute to simulate Flask-RESTful registration
    bp.resources = [(Resource, ("/test",), {})]

    # Add api attribute to the blueprint
    bp.api = api

    return bp


@pytest.fixture
def app_with_blueprint(app, blueprint):
    """Register the blueprint with the app."""
    app.register_blueprint(blueprint)
    return app


def test_register_commands(app):
    """Test registering commands with the Flask app."""
    register_commands(app)

    # Check that the command was registered
    assert "generate-openapi" in app.cli.commands

    # Check command help text
    command = app.cli.commands["generate-openapi"]
    assert "Generate OpenAPI schema and documentation" in command.help


def test_generate_openapi_command_no_blueprints(app):
    """Test generate_openapi_command with no blueprints."""
    runner = CliRunner()

    with app.app_context():
        result = runner.invoke(generate_openapi_command)

    assert result.exit_code == 0
    assert "No blueprints found" in result.output


def test_generate_openapi_command_with_blueprint(app_with_blueprint, tmp_path):
    """Test generate_openapi_command with a blueprint."""
    runner = CliRunner()
    output_file = str(tmp_path / "openapi.yaml")

    with app_with_blueprint.app_context():
        result = runner.invoke(
            generate_openapi_command,
            [
                "--output",
                output_file,
                "--title",
                "Test API",
                "--version",
                "1.0.0",
                "--description",
                "Test API Description",
                "--format",
                "yaml",
            ],
        )

    assert result.exit_code == 0
    assert "Generated OpenAPI schema for service_api blueprint" in result.output
    assert os.path.exists(output_file)

    # Check the content of the generated file
    with open(output_file, "r") as f:
        content = f.read()

    schema = yaml.safe_load(content)
    assert schema["info"]["title"] == "Test API - service_api"
    assert schema["info"]["version"] == "1.0.0"
    assert schema["info"]["description"] == "Test API Description"


def test_generate_openapi_command_json_format(app_with_blueprint, tmp_path):
    """Test generate_openapi_command with JSON output format."""
    runner = CliRunner()
    output_file = str(tmp_path / "openapi.json")

    with app_with_blueprint.app_context():
        result = runner.invoke(
            generate_openapi_command,
            [
                "--output",
                output_file,
                "--title",
                "Test API",
                "--version",
                "1.0.0",
                "--description",
                "Test API Description",
                "--format",
                "json",
            ],
        )

    assert result.exit_code == 0
    assert "Generated OpenAPI schema for service_api blueprint" in result.output
    assert os.path.exists(output_file)

    # Check the content of the generated file
    with open(output_file, "r") as f:
        schema = json.load(f)

    assert schema["info"]["title"] == "Test API - service_api"
    assert schema["info"]["version"] == "1.0.0"
    assert schema["info"]["description"] == "Test API Description"


def test_generate_openapi_command_multiple_languages(app_with_blueprint, tmp_path):
    """Test generate_openapi_command with multiple languages."""
    runner = CliRunner()
    output_file = str(tmp_path / "openapi.yaml")

    with app_with_blueprint.app_context():
        result = runner.invoke(
            generate_openapi_command,
            [
                "--output",
                output_file,
                "--title",
                "Test API",
                "--version",
                "1.0.0",
                "--description",
                "Test API Description",
                "--language",
                "en",
                "--language",
                "zh-Hans",
                "--format",
                "yaml",
            ],
        )

    assert result.exit_code == 0
    assert "Generated OpenAPI schema for service_api blueprint" in result.output
    assert os.path.exists(output_file)


def test_generate_openapi_command_specific_blueprint(app_with_blueprint, tmp_path):
    """Test generate_openapi_command with a specific blueprint."""
    runner = CliRunner()
    output_file = str(tmp_path / "openapi.yaml")

    with app_with_blueprint.app_context():
        result = runner.invoke(
            generate_openapi_command,
            [
                "--output",
                output_file,
                "--blueprint",
                "service_api",
                "--title",
                "Test API",
                "--version",
                "1.0.0",
                "--description",
                "Test API Description",
                "--format",
                "yaml",
            ],
        )

    assert result.exit_code == 0
    assert "Generated OpenAPI schema for service_api blueprint" in result.output
    assert os.path.exists(output_file)


def test_generate_openapi_command_invalid_blueprint(app_with_blueprint, tmp_path):
    """Test generate_openapi_command with an invalid blueprint."""
    runner = CliRunner()
    output_file = str(tmp_path / "openapi.yaml")

    with app_with_blueprint.app_context():
        result = runner.invoke(
            generate_openapi_command,
            [
                "--output",
                output_file,
                "--blueprint",
                "nonexistent",
                "--title",
                "Test API",
                "--version",
                "1.0.0",
                "--description",
                "Test API Description",
                "--format",
                "yaml",
            ],
        )

    assert result.exit_code == 0
    assert "No blueprints found with name nonexistent" in result.output
    assert not os.path.exists(output_file)


def test_generate_openapi_command_blueprint_without_api(app, tmp_path):
    """Test generate_openapi_command with a blueprint that doesn't have an API."""
    # Create a blueprint without an API
    bp = Blueprint("no_api", __name__)
    app.register_blueprint(bp)

    runner = CliRunner()
    output_file = str(tmp_path / "openapi.yaml")

    with app.app_context():
        result = runner.invoke(
            generate_openapi_command,
            [
                "--output",
                output_file,
                "--title",
                "Test API",
                "--version",
                "1.0.0",
                "--description",
                "Test API Description",
                "--format",
                "yaml",
            ],
        )

    assert result.exit_code == 0
    assert "No blueprints found" in result.output
    assert not os.path.exists(output_file)
