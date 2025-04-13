"""
Test helpers for Flask-X-OpenAPI-Schema.
"""

import contextlib
from unittest.mock import MagicMock

from flask import Flask, request_started


@contextlib.contextmanager
def flask_request_context():
    """
    Create a Flask request context for testing.

    This context manager creates a Flask app and pushes a request context
    for testing functions that require a Flask request context.
    """
    app = Flask(__name__)
    with app.test_request_context():
        # Emit the request_started signal to initialize request local variables
        request_started.send(app)
        yield app


def create_mock_file(filename="test.txt", content=b"test content"):
    """
    Create a mock file for testing file uploads.

    Args:
        filename: The name of the file
        content: The content of the file

    Returns:
        A mock file object that mimics a FileStorage object
    """
    mock_file = MagicMock()
    mock_file.filename = filename
    mock_file.read.return_value = content
    mock_file.stream.read.return_value = content

    # Add seek and tell methods to simulate file size
    def mock_seek(position, whence=0):
        mock_file._position = position

    def mock_tell():
        return len(content)

    mock_file.seek = mock_seek
    mock_file.tell = mock_tell

    return mock_file
