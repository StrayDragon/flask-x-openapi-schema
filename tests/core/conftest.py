"""
Shared fixtures for core functionality tests.
"""

import io
import pytest
from werkzeug.datastructures import FileStorage

from flask_x_openapi_schema.i18n.i18n_string import set_current_language


@pytest.fixture(autouse=True)
def reset_language():
    """Reset the language to English before each test."""
    set_current_language("en-US")
    yield
    set_current_language("en-US")


@pytest.fixture
def test_file():
    """Create a test file for testing."""
    return FileStorage(
        stream=io.BytesIO(b"Test file content"),
        filename="test.txt",
        content_type="text/plain",
    )


@pytest.fixture
def test_image():
    """Create a test image for testing."""
    return FileStorage(
        stream=io.BytesIO(b"Test image content"),
        filename="test.jpg",
        content_type="image/jpeg",
    )


@pytest.fixture
def test_document():
    """Create a test document for testing."""
    return FileStorage(
        stream=io.BytesIO(b"Test document content"),
        filename="test.pdf",
        content_type="application/pdf",
    )