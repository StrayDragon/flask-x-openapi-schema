"""
Pytest configuration file.
"""

import pytest
from flask_x_openapi_schema import reset_prefixes


@pytest.fixture(autouse=True)
def reset_parameter_prefixes():
    """Reset parameter prefixes before each test."""
    reset_prefixes()
    yield
