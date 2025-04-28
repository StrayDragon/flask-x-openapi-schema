"""Simplified caching mechanism for OpenAPI schema generation.

This module provides a minimal caching system focused only on the essential
caching needs for the @openapi_metadata decorator. It uses WeakKeyDictionary
to avoid memory leaks when functions are garbage collected.

Cache Types:
    - WeakKeyDictionary: For function metadata to avoid memory leaks

Thread Safety:
    This module is designed to be thread-safe for use in multi-threaded web servers.
"""

import weakref
from typing import Any

# Cache for decorated functions to avoid recomputing metadata (weak references)
# This uses WeakKeyDictionary to avoid memory leaks when functions are garbage collected
FUNCTION_METADATA_CACHE = weakref.WeakKeyDictionary()


def clear_all_caches() -> None:
    """Clear all caches to free memory or force regeneration.

    This function clears the function metadata cache.
    """
    FUNCTION_METADATA_CACHE.clear()


def get_parameter_prefixes(config: Any | None = None) -> tuple[str, str, str, str]:
    """Get parameter prefixes from config or global defaults.

    This function retrieves parameter prefixes from the provided config or global defaults.

    Args:
        config: Optional configuration object with custom prefixes

    Returns:
        Tuple of (body_prefix, query_prefix, path_prefix, file_prefix)

    """
    from .config import GLOBAL_CONFIG_HOLDER

    # If config is None, use global config
    prefix_config = GLOBAL_CONFIG_HOLDER.get() if config is None else config

    # Extract the prefixes directly
    return (
        prefix_config.request_body_prefix,
        prefix_config.request_query_prefix,
        prefix_config.request_path_prefix,
        prefix_config.request_file_prefix,
    )
