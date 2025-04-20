"""
Configuration management for OpenAPI schema generation.
"""

import threading
from dataclasses import dataclass

# Default parameter prefixes
DEFAULT_BODY_PREFIX = "_x_body"
DEFAULT_QUERY_PREFIX = "_x_query"
DEFAULT_PATH_PREFIX = "_x_path"
DEFAULT_FILE_PREFIX = "_x_file"


@dataclass(frozen=True)
class ConventionalPrefixConfig:
    """Configuration class for OpenAPI parameter prefixes.

    This class holds configuration settings for parameter prefixes used in
    binding request data to function parameters.

    Attributes:
        request_body_prefix: Prefix for request body parameters
        request_query_prefix: Prefix for query parameters
        request_path_prefix: Prefix for path parameters
        request_file_prefix: Prefix for file parameters
    """

    request_body_prefix: str = DEFAULT_BODY_PREFIX
    request_query_prefix: str = DEFAULT_QUERY_PREFIX
    request_path_prefix: str = DEFAULT_PATH_PREFIX
    request_file_prefix: str = DEFAULT_FILE_PREFIX


# Global configuration instance with thread safety
class ThreadSafeConfig:
    """Thread-safe configuration holder."""

    def __init__(self):
        self._config = ConventionalPrefixConfig()
        self._lock = threading.RLock()

    def get(self) -> ConventionalPrefixConfig:
        """Get the current configuration."""
        with self._lock:
            return ConventionalPrefixConfig(
                request_body_prefix=self._config.request_body_prefix,
                request_query_prefix=self._config.request_query_prefix,
                request_path_prefix=self._config.request_path_prefix,
                request_file_prefix=self._config.request_file_prefix,
            )

    def set(self, config: ConventionalPrefixConfig) -> None:
        """Set a new configuration."""
        with self._lock:
            self._config = ConventionalPrefixConfig(
                request_body_prefix=config.request_body_prefix,
                request_query_prefix=config.request_query_prefix,
                request_path_prefix=config.request_path_prefix,
                request_file_prefix=config.request_file_prefix,
            )

    def reset(self) -> None:
        """Reset to default configuration."""
        with self._lock:
            self._config = ConventionalPrefixConfig(
                request_body_prefix=DEFAULT_BODY_PREFIX,
                request_query_prefix=DEFAULT_QUERY_PREFIX,
                request_path_prefix=DEFAULT_PATH_PREFIX,
                request_file_prefix=DEFAULT_FILE_PREFIX,
            )


# Create a singleton instance
GLOBAL_CONFIG_HOLDER = ThreadSafeConfig()


def configure_prefixes(config: ConventionalPrefixConfig) -> None:
    """Configure global parameter prefixes.

    Args:
        config: Configuration object with parameter prefixes
    """
    # Update the configuration in a thread-safe manner
    GLOBAL_CONFIG_HOLDER.set(config)


def reset_prefixes() -> None:
    """Reset parameter prefixes to default values."""
    # Reset the configuration in a thread-safe manner
    GLOBAL_CONFIG_HOLDER.reset()
