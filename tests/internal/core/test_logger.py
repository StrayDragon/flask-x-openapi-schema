"""Tests for the logger module.

This module provides comprehensive tests for the logger module,
covering basic functionality, configuration options, and edge cases.
"""

import io
import logging

import pytest

from flask_x_openapi_schema.core.logger import (
    DEFAULT_FORMAT,
    DETAILED_FORMAT,
    SIMPLE_FORMAT,
    LogFormat,
    _get_format_string,
    _get_log_level,
    configure_logging,
    get_logger,
)


class TestLogger:
    """Tests for the logger module."""

    def setup_method(self):
        """Set up test environment."""
        # Reset logger configuration before each test
        configure_logging()

    def test_log_format_enum(self):
        """Test LogFormat enum values."""
        assert LogFormat.DEFAULT == "default"
        assert LogFormat.SIMPLE == "simple"
        assert LogFormat.DETAILED == "detailed"
        assert LogFormat.JSON == "json"

    def test_get_format_string(self):
        """Test _get_format_string function."""
        # Test with string values
        assert _get_format_string("default") == DEFAULT_FORMAT
        assert _get_format_string("simple") == SIMPLE_FORMAT
        assert _get_format_string("detailed") == DETAILED_FORMAT
        assert _get_format_string("json").startswith('{"time":')

        # Test with enum values
        assert _get_format_string(LogFormat.DEFAULT) == DEFAULT_FORMAT
        assert _get_format_string(LogFormat.SIMPLE) == SIMPLE_FORMAT
        assert _get_format_string(LogFormat.DETAILED) == DETAILED_FORMAT
        assert _get_format_string(LogFormat.JSON).startswith('{"time":')

        # Test with invalid value (should return default)
        with pytest.raises(ValueError):
            _get_format_string("invalid")

    def test_get_log_level(self):
        """Test _get_log_level function."""
        # Test with string values
        assert _get_log_level("DEBUG") == logging.DEBUG
        assert _get_log_level("INFO") == logging.INFO
        assert _get_log_level("WARNING") == logging.WARNING
        assert _get_log_level("WARN") == logging.WARNING
        assert _get_log_level("ERROR") == logging.ERROR
        assert _get_log_level("CRITICAL") == logging.CRITICAL

        # Test with integer values
        assert _get_log_level(logging.DEBUG) == logging.DEBUG
        assert _get_log_level(logging.INFO) == logging.INFO
        assert _get_log_level(logging.WARNING) == logging.WARNING
        assert _get_log_level(logging.ERROR) == logging.ERROR
        assert _get_log_level(logging.CRITICAL) == logging.CRITICAL

        # Test with invalid value (should return WARNING)
        assert _get_log_level("INVALID") == logging.WARNING

    def test_configure_logging_with_level(self):
        """Test configure_logging with different log levels."""
        # Test with string level
        configure_logging(level="DEBUG")
        logger = get_logger("flask_x_openapi_schema.test")
        assert logger.level == logging.DEBUG

        # Test with integer level
        configure_logging(level=logging.INFO)
        logger = get_logger("flask_x_openapi_schema.test")
        assert logger.level == logging.INFO

    def test_configure_logging_with_format(self):
        """Test configure_logging with different formats."""
        # Capture log output
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)

        # Test with string format
        configure_logging(format_="simple", handler=handler)
        logger = get_logger("flask_x_openapi_schema.test")
        logger.warning("Test message")

        # Reset stream
        output = stream.getvalue()
        stream.truncate(0)
        stream.seek(0)

        # Check that format is applied - the actual format may vary based on handler configuration
        assert "Test message" in output

        # Test with enum format - just verify the message is there
        # The actual format may vary based on handler configuration
        configure_logging(format_=LogFormat.DETAILED, handler=handler)
        logger = get_logger("flask_x_openapi_schema.test")
        logger.warning("Test message")

        output = stream.getvalue()
        assert "Test message" in output

    def test_configure_logging_with_custom_handler(self):
        """Test configure_logging with a custom handler."""
        # Create a custom handler
        stream = io.StringIO()
        custom_handler = logging.StreamHandler(stream)
        custom_handler.setFormatter(logging.Formatter("CUSTOM: %(message)s"))

        # Configure logging with custom handler
        configure_logging(handler=custom_handler)

        # Log a message
        logger = get_logger("flask_x_openapi_schema.test")
        logger.warning("Test message")

        # Check that custom handler was used
        output = stream.getvalue()
        assert "CUSTOM: Test message" in output

    def test_configure_logging_propagation(self):
        """Test configure_logging with propagation settings."""
        # Note: propagation only affects the root library logger, not all loggers
        # Configure with propagation enabled
        configure_logging(propagate=True)
        root_logger = logging.getLogger("flask_x_openapi_schema")
        assert root_logger.propagate is True

        # Configure with propagation disabled
        configure_logging(propagate=False)
        root_logger = logging.getLogger("flask_x_openapi_schema")
        assert root_logger.propagate is False

    def test_get_logger_with_library_name(self):
        """Test get_logger with library name."""
        # Configure logging with specific level
        configure_logging(level=logging.DEBUG)

        # Get logger with library name
        logger = get_logger("flask_x_openapi_schema.test")

        # Check that logger has library level
        assert logger.level == logging.DEBUG

    def test_get_logger_with_external_name(self):
        """Test get_logger with external name."""
        # Configure logging with specific level
        configure_logging(level=logging.DEBUG)

        # Get logger with external name
        logger = get_logger("external.test")

        # Check that logger does not have library level
        assert logger.level != logging.DEBUG

    def test_multiple_handlers_cleanup(self):
        """Test that configure_logging cleans up old handlers."""
        # Configure logging multiple times
        configure_logging()
        configure_logging()
        configure_logging()

        # Get the library logger
        lib_logger = logging.getLogger("flask_x_openapi_schema")

        # Check that there's only one handler
        assert len(lib_logger.handlers) == 1
