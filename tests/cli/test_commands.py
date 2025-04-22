"""
Tests for CLI commands.
"""

import json
import os
import tempfile
from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner
from flask import Flask, Blueprint

from flask_x_openapi_schema.cli.commands import (
    generate_openapi_command,
    register_commands,
)
from flask_x_openapi_schema.x.flask_restful import OpenAPIIntegrationMixin


@pytest.fixture
def app():
    """Create a Flask app for testing."""
    app = Flask(__name__)
    return app


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def mock_blueprint():
    """Create a mock blueprint with OpenAPIIntegrationMixin."""
    bp = Blueprint("test_api", __name__)
    bp.api = MagicMock(spec=OpenAPIIntegrationMixin)
    bp.api.generate_openapi_schema.return_value = "test schema"
    bp.resources = ["test_resource"]
    return bp


def test_register_commands(app):
    """Test registering commands with a Flask app."""
    # Register commands
    register_commands(app)

    # Check that the command was registered
    assert "generate-openapi" in [cmd.name for cmd in app.cli.commands.values()]


def test_register_commands_adds_to_app_cli(app):
    """Test that register_commands adds the command to the app's CLI."""
    # Register commands
    register_commands(app)

    # Get all command names
    command_names = [cmd.name for cmd in app.cli.commands.values()]

    # Check that our command is in the list
    assert "generate-openapi" in command_names

    # Get the command object
    command = app.cli.commands.get("generate-openapi")

    # Check that it's the right command
    assert command is not None
    assert command.help is not None
    assert "Generate OpenAPI schema" in command.help


def test_generate_openapi_command_no_blueprints(runner, app):
    """Test generate_openapi_command with no blueprints."""
    # Create a test context
    with app.app_context():
        # Run the command
        result = runner.invoke(generate_openapi_command)

        # Check the output
        assert "No blueprints found" in result.output
        assert result.exit_code == 0


def test_generate_openapi_command_with_blueprint(runner, app, mock_blueprint):
    """Test generate_openapi_command with a blueprint."""
    # Add the blueprint to the app
    app.blueprints["test_api"] = mock_blueprint

    # Create a temporary directory for output
    with tempfile.TemporaryDirectory() as temp_dir:
        output_file = os.path.join(temp_dir, "openapi.yaml")

        # Create a test context
        with app.app_context():
            # Run the command
            result = runner.invoke(
                generate_openapi_command,
                [
                    "--output",
                    output_file,
                    "--blueprint",
                    "test_api",
                    "--title",
                    "Test API",
                    "--version",
                    "1.0.0",
                    "--description",
                    "Test API Description",
                    "--format",
                    "yaml",
                    "--language",
                    "en",
                ],
            )

            # Check the output
            assert "Generated OpenAPI schema for test_api blueprint" in result.output
            assert result.exit_code == 0

            # Check that the file was created
            assert os.path.exists(output_file)

            # Check the file content
            with open(output_file, "r") as f:
                content = f.read()
                assert content == "test schema"


def test_generate_openapi_command_json_format(runner, app, mock_blueprint):
    """Test generate_openapi_command with JSON format."""
    # Set up the mock to return a dict for JSON format
    mock_blueprint.api.generate_openapi_schema.return_value = {
        "openapi": "3.0.0",
        "info": {
            "title": "Test API - test_api",
            "version": "1.0.0",
            "description": "Test API Description",
        },
        "paths": {},
    }

    # Add the blueprint to the app
    app.blueprints["test_api"] = mock_blueprint

    # Create a temporary directory for output
    with tempfile.TemporaryDirectory() as temp_dir:
        output_file = os.path.join(temp_dir, "openapi.json")

        # Create a test context
        with app.app_context():
            # Run the command
            result = runner.invoke(
                generate_openapi_command,
                [
                    "--output",
                    output_file,
                    "--blueprint",
                    "test_api",
                    "--title",
                    "Test API",
                    "--version",
                    "1.0.0",
                    "--description",
                    "Test API Description",
                    "--format",
                    "json",
                    "--language",
                    "en",
                ],
            )

            # Check the output
            assert "Generated OpenAPI schema for test_api blueprint" in result.output
            assert result.exit_code == 0

            # Check that the file was created
            assert os.path.exists(output_file)

            # Check the file content
            with open(output_file, "r") as f:
                content = json.load(f)
                assert content["openapi"] == "3.0.0"
                assert content["info"]["title"] == "Test API - test_api"


def test_generate_openapi_command_multiple_languages(runner, app, mock_blueprint):
    """Test generate_openapi_command with multiple languages."""
    # Add the blueprint to the app
    app.blueprints["test_api"] = mock_blueprint

    # Create a temporary directory for output
    with tempfile.TemporaryDirectory() as temp_dir:
        output_file = os.path.join(temp_dir, "openapi.yaml")

        # Create a test context
        with app.app_context():
            # Run the command
            result = runner.invoke(
                generate_openapi_command,
                [
                    "--output",
                    output_file,
                    "--blueprint",
                    "test_api",
                    "--title",
                    "Test API",
                    "--version",
                    "1.0.0",
                    "--description",
                    "Test API Description",
                    "--format",
                    "yaml",
                    "--language",
                    "en",
                    "--language",
                    "zh",
                ],
            )

            # Check the output
            assert "Generated OpenAPI schema for test_api blueprint" in result.output
            assert result.exit_code == 0

            # Check that the file was created
            assert os.path.exists(output_file)


def test_generate_openapi_command_specific_blueprint(runner, app, mock_blueprint):
    """Test generate_openapi_command with a specific blueprint."""
    # Create another blueprint that should be ignored
    other_bp = Blueprint("other_api", __name__)
    other_bp.api = MagicMock(spec=OpenAPIIntegrationMixin)
    other_bp.resources = ["other_resource"]

    # Add both blueprints to the app
    app.blueprints["test_api"] = mock_blueprint
    app.blueprints["other_api"] = other_bp

    # Create a temporary directory for output
    with tempfile.TemporaryDirectory() as temp_dir:
        output_file = os.path.join(temp_dir, "openapi.yaml")

        # Create a test context
        with app.app_context():
            # Run the command specifying only test_api
            result = runner.invoke(
                generate_openapi_command,
                [
                    "--output",
                    output_file,
                    "--blueprint",
                    "test_api",
                    "--title",
                    "Test API",
                    "--version",
                    "1.0.0",
                    "--description",
                    "Test API Description",
                ],
            )

            # Check the output
            assert "Generated OpenAPI schema for test_api blueprint" in result.output
            assert "other_api" not in result.output
            assert result.exit_code == 0


def test_generate_openapi_command_invalid_blueprint(runner, app, mock_blueprint):
    """Test generate_openapi_command with an invalid blueprint name."""
    # Add the blueprint to the app
    app.blueprints["test_api"] = mock_blueprint

    # Create a test context
    with app.app_context():
        # Run the command with a non-existent blueprint
        result = runner.invoke(
            generate_openapi_command,
            [
                "--blueprint",
                "non_existent_api",
                "--title",
                "Test API",
                "--version",
                "1.0.0",
                "--description",
                "Test API Description",
            ],
        )

        # Check the output
        assert "No blueprints found with name non_existent_api" in result.output
        assert result.exit_code == 0


def test_generate_openapi_command_blueprint_without_api(runner, app):
    """Test generate_openapi_command with a blueprint that has no API."""
    # Create a blueprint without an API
    bp = Blueprint("test_api", __name__)
    bp.resources = ["test_resource"]

    # Add the blueprint to the app
    app.blueprints["test_api"] = bp

    # Create a test context
    with app.app_context():
        # Run the command
        result = runner.invoke(
            generate_openapi_command,
            [
                "--blueprint",
                "test_api",
                "--title",
                "Test API",
                "--version",
                "1.0.0",
                "--description",
                "Test API Description",
            ],
        )

        # Check the output
        assert (
            "Blueprint test_api does not have an OpenAPIExternalApi instance"
            in result.output
        )
        assert result.exit_code == 0


def test_generate_openapi_command_no_languages(runner, app, mock_blueprint):
    """Test generate_openapi_command with no languages specified."""
    # Add the blueprint to the app
    app.blueprints["test_api"] = mock_blueprint

    # Create a temporary directory for output
    with tempfile.TemporaryDirectory() as temp_dir:
        output_file = os.path.join(temp_dir, "openapi.yaml")

        # Create a test context
        with app.app_context():
            # Run the command without specifying languages
            result = runner.invoke(
                generate_openapi_command,
                [
                    "--output",
                    output_file,
                    "--blueprint",
                    "test_api",
                    "--title",
                    "Test API",
                    "--version",
                    "1.0.0",
                    "--description",
                    "Test API Description",
                ],
            )

            # Check the output
            assert "Generated OpenAPI schema for test_api blueprint" in result.output
            assert result.exit_code == 0

            # Verify that the generate_openapi_schema was called with default language
            call_args = mock_blueprint.api.generate_openapi_schema.call_args[1]
            assert call_args["language"] == "en"  # Default language


def test_generate_openapi_command_no_blueprint_specified(runner, app, mock_blueprint):
    """Test generate_openapi_command without specifying a blueprint."""
    # Add the blueprint to the app with the default name expected by the command
    app.blueprints["service_api"] = mock_blueprint

    # Create a temporary directory for output
    with tempfile.TemporaryDirectory() as temp_dir:
        output_file = os.path.join(temp_dir, "openapi.yaml")

        # Create a test context
        with app.app_context():
            # Run the command without specifying a blueprint
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
                ],
            )

            # Check the output
            assert "Generated OpenAPI schema for service_api blueprint" in result.output
            assert result.exit_code == 0

            # Check that the file was created
            assert os.path.exists(output_file)


def test_generate_openapi_command_multiple_blueprints(runner, app, mock_blueprint):
    """Test generate_openapi_command with multiple blueprints."""
    # Create a second blueprint
    second_bp = Blueprint("second_api", __name__)
    second_bp.api = MagicMock(spec=OpenAPIIntegrationMixin)
    second_bp.api.generate_openapi_schema.return_value = "second schema"
    second_bp.resources = ["second_resource"]

    # Add both blueprints to the app with one using the default name
    app.blueprints["service_api"] = mock_blueprint
    app.blueprints["second_api"] = second_bp

    # Create a temporary directory for output
    with tempfile.TemporaryDirectory() as temp_dir:
        output_file = os.path.join(temp_dir, "openapi.yaml")

        # Create a test context
        with app.app_context():
            # Run the command without specifying a blueprint (should generate for all)
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
                ],
            )

            # Check the output
            assert "Generated OpenAPI schema for service_api blueprint" in result.output
            assert result.exit_code == 0

            # Check that the file was created
            assert os.path.exists(output_file)


def test_generate_openapi_command_nested_output_directory(runner, app, mock_blueprint):
    """Test generate_openapi_command with a nested output directory."""
    # Add the blueprint to the app
    app.blueprints["test_api"] = mock_blueprint

    # Create a temporary directory for output
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a nested path that doesn't exist yet
        nested_dir = os.path.join(temp_dir, "docs", "openapi")
        output_file = os.path.join(nested_dir, "openapi.yaml")

        # Create a test context
        with app.app_context():
            # Run the command
            result = runner.invoke(
                generate_openapi_command,
                [
                    "--output",
                    output_file,
                    "--blueprint",
                    "test_api",
                    "--title",
                    "Test API",
                    "--version",
                    "1.0.0",
                    "--description",
                    "Test API Description",
                ],
            )

            # Check the output
            assert "Generated OpenAPI schema for test_api blueprint" in result.output
            assert result.exit_code == 0

            # Check that the file was created in the nested directory
            assert os.path.exists(output_file)


def test_generate_openapi_command_with_i18n_description(runner, app, mock_blueprint):
    """Test generate_openapi_command with internationalized description."""
    # Add the blueprint to the app
    app.blueprints["test_api"] = mock_blueprint

    # Create a temporary directory for output
    with tempfile.TemporaryDirectory() as temp_dir:
        output_file = os.path.join(temp_dir, "openapi.yaml")

        # Create a test context
        with app.app_context():
            # Run the command with multiple languages
            result = runner.invoke(
                generate_openapi_command,
                [
                    "--output",
                    output_file,
                    "--blueprint",
                    "test_api",
                    "--title",
                    "Test API",
                    "--version",
                    "1.0.0",
                    "--description",
                    "Test API Description",
                    "--language",
                    "en",
                    "--language",
                    "zh",
                    "--language",
                    "fr",
                ],
            )

            # Check the output
            assert "Generated OpenAPI schema for test_api blueprint" in result.output
            assert result.exit_code == 0

            # Verify that the generate_openapi_schema was called with i18n parameters
            call_args = mock_blueprint.api.generate_openapi_schema.call_args[1]
            assert call_args["language"] == "en"  # Default language

            # Check title and description are I18nStr objects
            assert call_args["title"].get("en") == "Test API - test_api"
            assert call_args["title"].get("zh") == "Test API - test_api"
            assert call_args["title"].get("fr") == "Test API - test_api"

            assert call_args["description"].get("en") == "Test API Description"
            assert call_args["description"].get("zh") == "Test API Description"
            assert call_args["description"].get("fr") == "Test API Description"
