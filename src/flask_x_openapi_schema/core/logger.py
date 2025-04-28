"""Unified logging system for flask_x_openapi_schema.

This module provides a centralized logging system for the entire library,
with consistent formatting, configurable log levels, and automatic inclusion
of file and line information.

Usage:
    from flask_x_openapi_schema.core.logger import get_logger

    # Get a logger for the current module
    logger = get_logger(__name__)

    # Log messages
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")

    # Configure logging (typically done once at application startup)
    from flask_x_openapi_schema.core.logger import configure_logging
    configure_logging(level="INFO", format="detailed")
"""

import logging
import sys
from enum import Enum

# Default log format with file and line information
DEFAULT_FORMAT = "[%(levelname)s] %(asctime)s (%(name)s) %(pathname)s:%(lineno)d: %(message)s"
# Simple format for less verbose output
SIMPLE_FORMAT = "%(levelname)s: %(message)s"
# Detailed format with thread information
DETAILED_FORMAT = "%(asctime)s [%(levelname)s] [%(threadName)s] %(name)s (%(filename)s:%(lineno)d): %(message)s"

# Global logger configuration
_LOG_LEVEL = logging.WARNING
_LOG_FORMAT = DEFAULT_FORMAT
_HANDLER = None


class LogFormat(str, Enum):
    """Predefined log formats."""

    DEFAULT = "default"
    SIMPLE = "simple"
    DETAILED = "detailed"
    JSON = "json"


def _get_format_string(format_name: str | LogFormat) -> str:
    """Get the format string for the specified format name.

    Args:
        format_name: The name of the format to use

    Returns:
        The format string

    """
    if isinstance(format_name, str):
        format_name = LogFormat(format_name.lower())

    if format_name == LogFormat.SIMPLE:
        return SIMPLE_FORMAT
    if format_name == LogFormat.DETAILED:
        return DETAILED_FORMAT
    if format_name == LogFormat.JSON:
        return '{"time": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "file": "%(filename)s", "line": %(lineno)d, "message": "%(message)s"}'  # noqa: E501
    # Default
    return DEFAULT_FORMAT


def _get_log_level(level: str | int) -> int:  # noqa: PLR0911
    """Convert a string log level to the corresponding logging constant.

    Args:
        level: The log level as a string or integer

    Returns:
        The log level as a logging constant

    """
    if isinstance(level, int):
        return level

    level_upper = level.upper()
    if level_upper == "DEBUG":
        return logging.DEBUG
    if level_upper == "INFO":
        return logging.INFO
    if level_upper in {"WARNING", "WARN"}:
        return logging.WARNING
    if level_upper == "ERROR":
        return logging.ERROR
    if level_upper == "CRITICAL":
        return logging.CRITICAL
    return logging.WARNING


def configure_logging(
    level: str | int = "WARNING",
    format_: str | LogFormat = LogFormat.DEFAULT,
    handler: logging.Handler | None = None,
    propagate: bool = True,
) -> None:
    """Configure the logging system.

    Args:
        level: The log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_: The log format (default, simple, detailed, json)
        handler: A custom log handler (if None, logs to stderr)
        propagate: Whether to propagate logs to parent loggers

    Example:
        >>> from flask_x_openapi_schema.core.logger import configure_logging
        >>> configure_logging(level="DEBUG", format="detailed")

    """
    global _LOG_LEVEL, _LOG_FORMAT, _HANDLER  # noqa: PLW0603

    # Set the global log level
    _LOG_LEVEL = _get_log_level(level)

    # Set the global log format
    _LOG_FORMAT = _get_format_string(format_)

    # Create or use the provided handler
    if handler is not None:
        _HANDLER = handler
    else:
        _HANDLER = logging.StreamHandler(sys.stderr)
        _HANDLER.setFormatter(logging.Formatter(_LOG_FORMAT))

    # Configure the root logger for the library
    lib_logger = logging.getLogger("flask_x_openapi_schema")
    lib_logger.setLevel(_LOG_LEVEL)

    # Remove any existing handlers to avoid duplicates
    for hdlr in lib_logger.handlers[:]:
        lib_logger.removeHandler(hdlr)

    # Add the new handler
    lib_logger.addHandler(_HANDLER)

    # Set propagation
    lib_logger.propagate = propagate


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name.

    This function returns a logger that automatically includes file and line
    information in log messages. It ensures consistent formatting across the library.

    Args:
        name: The name of the logger, typically __name__

    Returns:
        A configured logger

    Example:
        >>> from flask_x_openapi_schema.core.logger import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.debug("Debug message")

    """
    logger = logging.getLogger(name)

    # Ensure the logger has the correct level
    if name.startswith("flask_x_openapi_schema"):
        logger.setLevel(_LOG_LEVEL)

    # Return the logger
    return logger


# Initialize logging with default settings
configure_logging()
