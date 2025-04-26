"""Command-line interface for OpenAPI schema generation."""

from .commands import generate_openapi_command, register_commands

__all__ = [
    "generate_openapi_command",
    "register_commands",
]
