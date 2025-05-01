"""Unified logging system for flask_x_openapi_schema.

This module provides a centralized logging system for the entire library,
with consistent formatting, configurable log levels, and automatic inclusion
of file and line information.

Examples:
    Basic usage with default configuration:

    >>> from flask_x_openapi_schema.core.logger import get_logger
    >>> logger = get_logger(__name__)
    >>> logger.debug("Debug message")
    >>> logger.info("Info message")
    >>> logger.warning("Warning message")
    >>> logger.error("Error message")

    Configuring the logging system:

    >>> from flask_x_openapi_schema.core.logger import configure_logging
    >>> configure_logging(level="INFO", format_="detailed")

Attributes:
    DEFAULT_FORMAT (str): Default log format with basic information.
    SIMPLE_FORMAT (str): Simplified log format with only level and message.
    DETAILED_FORMAT (str): Detailed log format with thread and file information.

"""

import logging
import sys
from enum import Enum

DEFAULT_FORMAT = "[%(levelname)s] %(asctime)s (%(name)s) %(pathname)s:%(lineno)d: %(message)s"

SIMPLE_FORMAT = "%(levelname)s: %(message)s"

DETAILED_FORMAT = "%(asctime)s [%(levelname)s] [%(threadName)s] %(name)s (%(filename)s:%(lineno)d): %(message)s"


_LOG_LEVEL = logging.WARNING
_LOG_FORMAT = DEFAULT_FORMAT
_HANDLER = None


class LogFormat(str, Enum):
    """Predefined log formats.

    This enum defines the available log format options that can be used
    with the configure_logging function.

    Attributes:
        DEFAULT: Standard format with basic information.
        SIMPLE: Simplified format with only level and message.
        DETAILED: Detailed format with thread and file information.
        JSON: JSON-formatted logs for machine parsing.

    """

    DEFAULT = "default"
    SIMPLE = "simple"
    DETAILED = "detailed"
    JSON = "json"


def _get_format_string(format_name: str | LogFormat) -> str:
    """Get the format string for the specified format name.

    Args:
        format_name: The name of the format to use. Can be a string or LogFormat enum.

    Returns:
        str: The corresponding format string for the specified format.

    """
    if isinstance(format_name, str):
        format_name = LogFormat(format_name.lower())

    if format_name == LogFormat.SIMPLE:
        return SIMPLE_FORMAT
    if format_name == LogFormat.DETAILED:
        return DETAILED_FORMAT
    if format_name == LogFormat.JSON:
        return '{"time": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "file": "%(filename)s", "line": %(lineno)d, "message": "%(message)s"}'

    return DEFAULT_FORMAT


def _get_log_level(level: str | int) -> int:
    """Convert a string log level to the corresponding logging constant.

    Args:
        level: The log level as a string (e.g., "DEBUG", "INFO") or integer.

    Returns:
        int: The log level as a logging constant (e.g., logging.DEBUG, logging.INFO).

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
    """Configure the logging system for the flask_x_openapi_schema library.

    This function sets up the logging configuration for the entire library,
    including log level, format, handler, and propagation settings.

    Args:
        level: The log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
            Can be provided as a string or as a logging constant.
        format_: The log format to use. Can be a string name of a predefined format
            or a LogFormat enum value. Options are "default", "simple", "detailed", or "json".
        handler: A custom log handler to use. If None, logs will be sent to stderr.
        propagate: Whether to propagate logs to parent loggers. Set to False to
            prevent duplicate log messages if parent loggers are already configured.

    Examples:
        >>> from flask_x_openapi_schema.core.logger import configure_logging
        >>> configure_logging(level="DEBUG", format_="detailed")
        >>> configure_logging(level=logging.INFO, format_=LogFormat.JSON)

    """
    global _LOG_LEVEL, _LOG_FORMAT, _HANDLER  # noqa: PLW0603

    _LOG_LEVEL = _get_log_level(level)

    _LOG_FORMAT = _get_format_string(format_)

    if handler is not None:
        _HANDLER = handler
    else:
        _HANDLER = logging.StreamHandler(sys.stderr)
        _HANDLER.setFormatter(logging.Formatter(_LOG_FORMAT))

    lib_logger = logging.getLogger("flask_x_openapi_schema")
    lib_logger.setLevel(_LOG_LEVEL)

    for hdlr in lib_logger.handlers[:]:
        lib_logger.removeHandler(hdlr)

    lib_logger.addHandler(_HANDLER)

    lib_logger.propagate = propagate


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name.

    This function returns a logger that automatically includes file and line
    information in log messages. It ensures consistent formatting across the library.
    If the logger name starts with "flask_x_openapi_schema", it will be configured
    with the library's log level.

    Args:
        name: The name of the logger, typically __name__.

    Returns:
        logging.Logger: A configured logger instance.

    Examples:
        >>> from flask_x_openapi_schema.core.logger import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.debug("Debug message")
        >>> logger.info("Info message")
        >>> logger.warning("Warning message")

    """
    logger = logging.getLogger(name)

    if name.startswith("flask_x_openapi_schema"):
        logger.setLevel(_LOG_LEVEL)

    return logger


configure_logging()
