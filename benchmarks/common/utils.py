"""
Shared utilities for benchmarking.

This module contains utility functions used in benchmarks.
"""

import random
import time
from datetime import datetime
from typing import Dict, Any
from urllib.parse import urlencode

from benchmarks.common.factories import UserRequestFactory, UserQueryParamsFactory


def get_random_user_data() -> Dict[str, Any]:
    """Get a random user data dictionary.

    Uses polyfactory to generate valid data that will pass validation.
    """
    # Add a small delay to simulate real-world processing
    if random.random() < 0.05:  # 5% chance of a small delay
        time.sleep(random.uniform(0.001, 0.01))

    # Generate valid user data using the factory
    user_request = UserRequestFactory.build()

    # Convert to dictionary for compatibility with existing code
    return user_request.model_dump()


def get_random_user_id() -> str:
    """Get a random user ID."""
    return f"user-{random.randint(1000, 9999)}"


def get_query_params() -> str:
    """Get random query parameters for benchmarking.

    Uses polyfactory to generate valid query parameters that will pass validation.
    """
    # Generate valid query parameters using the factory
    query_params = UserQueryParamsFactory.build()

    # Convert to dictionary and filter out None values
    params = {k: v for k, v in query_params.model_dump().items() if v is not None}

    # Special handling for tags which should be comma-separated
    if params.get("tags") is not None and isinstance(params["tags"], str):
        # Ensure tags is a valid string format
        if params["tags"].strip() == "":
            params.pop("tags")

    # Convert to query string
    query_string = "?" + urlencode(params)
    return query_string


def get_performance_metrics() -> Dict[str, Any]:
    """Get performance metrics for the current request."""
    return {
        "timestamp": datetime.now().isoformat(),
        "cpu_usage": random.uniform(0.1, 100.0),
        "memory_usage": random.uniform(10.0, 1024.0),
        "request_duration_ms": random.uniform(1.0, 100.0),
        "db_query_count": random.randint(1, 20),
        "db_query_duration_ms": random.uniform(0.5, 50.0),
        "cache_hits": random.randint(0, 10),
        "cache_misses": random.randint(0, 5),
        "status_code": 201,  # For create user operations
        "error_count": 0,
    }
