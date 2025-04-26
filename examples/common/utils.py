"""Utility functions for Flask-X-OpenAPI-Schema examples.

This module contains utility functions for formatting and displaying data.
"""

import json
from datetime import datetime
from typing import Any

from rich.console import Console
from rich.json import JSON
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

console = Console()


def print_request_info(  # noqa: PLR0913
    method: str,
    path: str,
    path_params: dict[str, Any] | None = None,
    query_params: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    file: dict[str, Any] | None = None,
):
    """Print request information in a formatted way."""
    console.print(
        Panel(
            f"[bold blue]{method}[/bold blue] [bold green]{path}[/bold green]",
            title="Request",
            border_style="blue",
        ),
    )

    if path_params:
        console.print("[bold cyan]Path Parameters:[/bold cyan]")
        _print_params_table(path_params)

    if query_params:
        console.print("[bold cyan]Query Parameters:[/bold cyan]")
        _print_params_table(query_params)

    if headers:
        console.print("[bold cyan]Headers:[/bold cyan]")
        _print_params_table(headers)

    if body:
        console.print("[bold cyan]Request Body:[/bold cyan]")
        console.print(JSON(json.dumps(body, cls=DateTimeEncoder)))
        console.print()

    if file:
        console.print("[bold cyan]File Upload:[/bold cyan]")
        _print_params_table(file)
        console.print()


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects."""

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def print_response_info(
    status_code: int,
    data: dict[str, Any] | list[dict[str, Any]],
    headers: dict[str, str] | None = None,
):
    """Print response information in a formatted way."""
    status_color = "green" if 200 <= status_code < 300 else "red"

    console.print(
        Panel(
            f"[bold {status_color}]Status: {status_code}[/bold {status_color}]",
            title="Response",
            border_style=status_color,
        ),
    )

    if headers:
        console.print("[bold cyan]Headers:[/bold cyan]")
        _print_params_table(headers)

    console.print("[bold cyan]Response Body:[/bold cyan]")
    console.print(JSON(json.dumps(data, cls=DateTimeEncoder)))
    console.print()


def _print_params_table(params: dict[str, Any]):
    """Print parameters in a table format."""
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Name", style="dim")
    table.add_column("Value")

    for name, value in params.items():
        if isinstance(value, (dict, list)):
            v = json.dumps(value)
        elif value is None:
            v = "null"
        elif isinstance(value, datetime):
            v = value.isoformat()
        else:
            v = str(value)

        table.add_row(name, v)

    console.print(table)
    console.print()


def print_code_example(code: str, language: str = "python"):
    """Print a code example with syntax highlighting."""
    console.print(
        Panel(
            Syntax(code, language, theme="monokai", line_numbers=True),
            title=f"{language.capitalize()} Example",
            border_style="green",
        ),
    )
    console.print()


def print_section_header(title: str):
    """Print a section header."""
    console.print()
    console.print(f"[bold yellow]{'=' * 20} {title} {'=' * 20}[/bold yellow]")
    console.print()
