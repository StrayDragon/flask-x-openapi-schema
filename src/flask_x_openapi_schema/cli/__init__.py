"""
Command-line interface for OpenAPI schema generation.
"""

from .commands import register_commands, generate_openapi_command

__all__ = [
    "register_commands",
    "generate_openapi_command",
]
