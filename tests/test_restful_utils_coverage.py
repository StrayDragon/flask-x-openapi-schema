"""
Tests for the restful_utils module to improve coverage.
"""

from enum import Enum

import pytest

from flask_x_openapi_schema.restful_utils import _get_field_type


class TestRestfulUtilsCoverage:
    """Tests for restful_utils to improve coverage."""

    def test_get_field_type_with_enum(self):
        """Test the _get_field_type function with an Enum type."""

        # Create an Enum class
        class Color(Enum):
            RED = "red"
            GREEN = "green"
            BLUE = "blue"

        # Get the field type function
        type_func = _get_field_type(Color)

        # Check that the function converts strings to Enum values
        assert type_func("red") == Color.RED
        assert type_func("green") == Color.GREEN
        assert type_func("blue") == Color.BLUE

        # Check that the function raises an error for invalid values
        with pytest.raises(ValueError):
            type_func("yellow")
