"""
Utility functions for Flask-X-OpenAPI-Schema examples.

This module contains utility functions for formatting and displaying data.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.json import JSON
from rich.syntax import Syntax


console = Console()


def print_request_info(
    method: str,
    path: str,
    path_params: Optional[Dict[str, Any]] = None,
    query_params: Optional[Dict[str, Any]] = None,
    body: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    file: Optional[Dict[str, Any]] = None,
):
    """Print request information in a formatted way."""
    console.print(
        Panel(
            f"[bold blue]{method}[/bold blue] [bold green]{path}[/bold green]",
            title="Request",
            border_style="blue",
        )
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
    data: Union[Dict[str, Any], List[Dict[str, Any]]],
    headers: Optional[Dict[str, str]] = None,
):
    """Print response information in a formatted way."""
    status_color = "green" if 200 <= status_code < 300 else "red"

    console.print(
        Panel(
            f"[bold {status_color}]Status: {status_code}[/bold {status_color}]",
            title="Response",
            border_style=status_color,
        )
    )

    if headers:
        console.print("[bold cyan]Headers:[/bold cyan]")
        _print_params_table(headers)

    console.print("[bold cyan]Response Body:[/bold cyan]")
    console.print(JSON(json.dumps(data, cls=DateTimeEncoder)))
    console.print()


def _print_params_table(params: Dict[str, Any]):
    """Print parameters in a table format."""
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Name", style="dim")
    table.add_column("Value")

    for name, value in params.items():
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        elif value is None:
            value = "null"
        elif isinstance(value, datetime):
            value = value.isoformat()
        else:
            value = str(value)

        table.add_row(name, value)

    console.print(table)
    console.print()


def print_code_example(code: str, language: str = "python"):
    """Print a code example with syntax highlighting."""
    console.print(
        Panel(
            Syntax(code, language, theme="monokai", line_numbers=True),
            title=f"{language.capitalize()} Example",
            border_style="green",
        )
    )
    console.print()


def print_section_header(title: str):
    """Print a section header."""
    console.print()
    console.print(f"[bold yellow]{'=' * 20} {title} {'=' * 20}[/bold yellow]")
    console.print()
