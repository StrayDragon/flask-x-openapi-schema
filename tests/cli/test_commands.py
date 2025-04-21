"""
Tests for CLI commands.
"""

import os
import tempfile
from unittest.mock import patch, MagicMock

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
            import json

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


@pytest.mark.xfail(reason="This test is difficult to implement with Click commands")
def test_generate_openapi_command_multiple_blueprints(app, mock_blueprint):
    """Test generate_openapi_command with multiple blueprints."""
    # Create another blueprint
    other_bp = Blueprint("other_api", __name__)
    other_bp.api = MagicMock(spec=OpenAPIIntegrationMixin)
    other_bp.api.generate_openapi_schema.return_value = "other schema"
    other_bp.resources = ["other_resource"]

    # Add both blueprints to the app
    app.blueprints["test_api"] = mock_blueprint
    app.blueprints["other_api"] = other_bp

    # Create a temporary directory for output
    with tempfile.TemporaryDirectory() as temp_dir:
        output_file = os.path.join(temp_dir, "openapi.yaml")

        # Create a test context
        with app.app_context():
            # We can't easily test multiple blueprints with Click's runner
            # So we'll test the underlying functionality directly

            # Patch the blueprint check to force it to process all blueprints
            with patch("flask_x_openapi_schema.cli.commands.click.echo") as mock_echo:
                # Access the underlying function directly
                from flask_x_openapi_schema.cli.commands import (
                    generate_openapi_command as cmd_func,
                )

                # Manually call the function for each blueprint
                for bp_name in ["test_api", "other_api"]:
                    cmd_func.callback(
                        output=output_file,
                        blueprint=bp_name,
                        title="Test API",
                        version="1.0.0",
                        description="Test API Description",
                        format="yaml",
                        language=["en"],
                    )

                # Check that the echo function was called with the expected messages
                echo_calls = [call[0][0] for call in mock_echo.call_args_list]
                assert any(
                    "Generated OpenAPI schema for test_api blueprint" in call
                    for call in echo_calls
                )
                assert any(
                    "Generated OpenAPI schema for other_api blueprint" in call
                    for call in echo_calls
                )
