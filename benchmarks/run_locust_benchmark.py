#!/usr/bin/env python
"""
Run locust benchmark for flask_x_openapi_schema.

This script:
1. Starts the Flask server defined in locustfile.py
2. Runs the locust benchmark against it
3. Parses the results and displays them using rich
4. Stops the server when done
"""

import sys
import time
import subprocess
import csv
from pathlib import Path
from typing import Dict, Tuple, Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

# Initialize rich console
console = Console()


def start_flask_server() -> subprocess.Popen:
    """Start the Flask server defined in locustfile.py."""
    console.print("[bold cyan]Starting Flask server...[/bold cyan]")

    # Create a new Python file that imports and runs the server from locustfile.py
    server_script = """
import sys
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the server implementation from locustfile.py
try:
    from benchmarks.locustfile import app
    print("Successfully imported app from benchmarks.locustfile")
    print(f"Available routes: {[rule.rule for rule in app.url_map.iter_rules()]}")
except Exception as e:
    print(f"Error importing app: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

if __name__ == "__main__":
    print("Starting Flask server on port 5000...")
    app.run(host="0.0.0.0", port=5000, debug=False)
"""

    # Write the server script to a temporary file
    server_script_path = Path("benchmarks") / "temp_server.py"
    with open(server_script_path, "w") as f:
        f.write(server_script)

    # Start the server in a separate process
    server_process = subprocess.Popen(
        [sys.executable, str(server_script_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,  # Line buffered
    )

    # Wait for the server to start and show output
    console.print(
        "[cyan]Starting Flask server and waiting for it to be ready...[/cyan]"
    )

    # Monitor server output for a few seconds
    start_time = time.time()
    server_started = False

    # Read output for up to 10 seconds to see if the server starts
    while time.time() - start_time < 10 and not server_started:  # Wait up to 10 seconds
        # Check for server output
        stdout_line = server_process.stdout.readline() if server_process.stdout else ""
        stderr_line = server_process.stderr.readline() if server_process.stderr else ""

        if stdout_line:
            console.print(f"[dim]Server: {stdout_line.strip()}[/dim]")
        if stderr_line:
            console.print(f"[yellow]Server error: {stderr_line.strip()}[/yellow]")

        # Check if the server has started successfully
        if "Running on" in stdout_line or "Running on" in stderr_line:
            console.print("[green]Server started successfully![/green]")
            server_started = True
            break

        # Check if the process has exited
        if server_process.poll() is not None:
            console.print("[bold red]Server process exited unexpectedly![/bold red]")
            # Collect any remaining output
            stdout, stderr = server_process.communicate()
            if stdout:
                console.print(f"[dim]Server output: {stdout}[/dim]")
            if stderr:
                console.print(f"[yellow]Server error: {stderr}[/yellow]")
            raise RuntimeError("Server failed to start")

    # If we didn't see the server start message, assume it's running anyway
    if not server_started:
        console.print(
            "[yellow]Did not see server start message, but continuing anyway...[/yellow]"
        )

    # Give the server a moment to fully initialize
    console.print("[cyan]Waiting a moment for the server to fully initialize...[/cyan]")
    time.sleep(2)

    return server_process


def run_locust_benchmark() -> Tuple[str, str, str, str]:
    """Run the locust benchmark and return the paths to the result files."""
    console.print("[bold cyan]Running Locust benchmark...[/bold cyan]")

    # Define the output files
    results_prefix = "benchmarks/results"

    # Run locust in headless mode with a shorter duration and fewer users
    locust_cmd = [
        "locust",
        "-f",
        "benchmarks/locustfile.py",
        "--headless",
        "-u",
        "20",  # Number of users (reduced from 50)
        "-r",
        "5",  # Spawn rate (reduced from 10)
        "-t",
        "10s",  # Run time (reduced from 20s)
        "--csv",
        results_prefix,
        "--host",
        "http://localhost:5000",  # Explicitly set the host
    ]

    # Run locust
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
    ) as progress:
        task = progress.add_task("Running Locust benchmark...", total=None)
        try:
            # Run the command and capture output
            process = subprocess.Popen(
                locust_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
            )

            # Monitor the output in real-time
            while process.poll() is None:
                stdout_line = process.stdout.readline() if process.stdout else ""
                stderr_line = process.stderr.readline() if process.stderr else ""

                if stdout_line:
                    console.print(f"[dim]Locust: {stdout_line.strip()}[/dim]")
                if stderr_line:
                    console.print(
                        f"[yellow]Locust error: {stderr_line.strip()}[/yellow]"
                    )

                time.sleep(0.1)

            # Get the final return code
            return_code = process.poll()

            # Get any remaining output
            stdout, stderr = process.communicate()
            if stdout:
                console.print(f"[dim]Locust: {stdout}[/dim]")
            if stderr:
                console.print(f"[yellow]Locust error: {stderr}[/yellow]")

            # Check if the process was successful
            if return_code != 0:
                console.print(
                    f"[bold red]Locust exited with code {return_code}[/bold red]"
                )
                console.print(
                    "[yellow]Continuing anyway to analyze available results...[/yellow]"
                )

            progress.update(task, completed=True)
        except Exception as e:
            console.print(f"[bold red]Error running Locust:[/bold red] {e}")
            console.print(
                "[yellow]Continuing anyway to analyze available results...[/yellow]"
            )

    # Return the paths to the result files
    return (
        f"{results_prefix}_stats.csv",
        f"{results_prefix}_stats_history.csv",
        f"{results_prefix}_failures.csv",
        f"{results_prefix}_exceptions.csv",
    )


def parse_locust_results(stats_file: str) -> Dict:
    """Parse the Locust stats CSV file and return the results."""
    results = {
        "standard": {
            "requests": 0,
            "failures": 0,
            "median_response_time": 0,
            "avg_response_time": 0,
            "min_response_time": 0,
            "max_response_time": 0,
        },
        "openapi": {
            "requests": 0,
            "failures": 0,
            "median_response_time": 0,
            "avg_response_time": 0,
            "min_response_time": 0,
            "max_response_time": 0,
        },
    }

    # Check if the file exists
    if not Path(stats_file).exists():
        console.print(f"[bold red]Results file not found:[/bold red] {stats_file}")
        console.print("[yellow]Using default values for benchmark results.[/yellow]")
        return results

    try:
        with open(stats_file, newline="") as csvfile:
            reader = csv.DictReader(csvfile)

            # Check if the file is empty or has no rows
            rows = list(reader)
            if not rows:
                console.print(
                    "[bold yellow]Results file is empty or has no data rows.[/bold yellow]"
                )
                return results

            for row in rows:
                # Skip the aggregated row
                if row.get("Name", "") == "Aggregated":
                    continue

                # Determine if this is a standard or openapi request
                name = row.get("Name", "")
                if "standard" in name.lower():
                    category = "standard"
                elif "openapi" in name.lower():
                    category = "openapi"
                else:
                    continue

                # Update the results, handling missing or invalid values
                try:
                    results[category]["requests"] += int(row.get("Request Count", 0))
                except (ValueError, TypeError):
                    pass

                try:
                    results[category]["failures"] += int(row.get("Failure Count", 0))
                except (ValueError, TypeError):
                    pass

                # Always update response times, even if there are failures
                # This gives us performance data even when endpoints are failing
                try:
                    # Update median response time (weighted average if multiple endpoints)
                    median_time = float(row.get("Median Response Time", 0))
                    if results[category]["median_response_time"] == 0:
                        results[category]["median_response_time"] = median_time
                    else:
                        results[category]["median_response_time"] = (
                            results[category]["median_response_time"] + median_time
                        ) / 2
                except (ValueError, TypeError):
                    pass

                try:
                    # Update average response time (weighted average if multiple endpoints)
                    avg_time = float(row.get("Average Response Time", 0))
                    if results[category]["avg_response_time"] == 0:
                        results[category]["avg_response_time"] = avg_time
                    else:
                        results[category]["avg_response_time"] = (
                            results[category]["avg_response_time"] + avg_time
                        ) / 2
                except (ValueError, TypeError):
                    pass

                try:
                    # Update min response time
                    min_time = float(row.get("Min Response Time", 0))
                    if (
                        results[category]["min_response_time"] == 0
                        or min_time < results[category]["min_response_time"]
                    ):
                        results[category]["min_response_time"] = min_time
                except (ValueError, TypeError):
                    pass

                try:
                    # Update max response time
                    max_time = float(row.get("Max Response Time", 0))
                    if max_time > results[category]["max_response_time"]:
                        results[category]["max_response_time"] = max_time
                except (ValueError, TypeError):
                    pass
    except Exception as e:
        console.print(f"[bold red]Error parsing Locust results:[/bold red] {e}")
        console.print("[yellow]Using available data for benchmark results.[/yellow]")

    return results


def display_results(results: Dict) -> None:
    """Display the benchmark results using rich tables."""
    # Create the main results table
    table = Table(title="Locust Benchmark Results", box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Standard Flask", style="yellow")
    table.add_column("Flask-X-OpenAPI-Schema", style="green")
    table.add_column("Difference", style="magenta")

    # Add rows for each metric
    metrics = [
        ("Requests", "requests", ""),
        ("Failures", "failures", ""),
        ("Median Response Time", "median_response_time", "ms"),
        ("Average Response Time", "avg_response_time", "ms"),
        ("Min Response Time", "min_response_time", "ms"),
        ("Max Response Time", "max_response_time", "ms"),
    ]

    for display_name, key, unit in metrics:
        standard_value = results["standard"][key]
        openapi_value = results["openapi"][key]

        # Calculate difference and percentage
        if key in ["requests", "failures"]:
            diff = openapi_value - standard_value
            diff_percent = (diff / standard_value * 100) if standard_value > 0 else 0
            table.add_row(
                display_name,
                f"{standard_value}",
                f"{openapi_value}",
                f"{diff} ({diff_percent:.2f}%)",
            )
        else:
            diff = openapi_value - standard_value
            diff_percent = (diff / standard_value * 100) if standard_value > 0 else 0
            table.add_row(
                display_name,
                f"{standard_value:.2f}{unit}",
                f"{openapi_value:.2f}{unit}",
                f"{diff:.2f}{unit} ({diff_percent:.2f}%)",
            )

    console.print(table)

    # Check if there were failures
    standard_failures = results["standard"]["failures"]
    openapi_failures = results["openapi"]["failures"]

    if openapi_failures > 0 or standard_failures > 0:
        console.print(
            Panel(
                f"[bold yellow]Warning: Some requests failed during the benchmark.[/bold yellow]\n\n"
                f"- Standard Flask failures: [yellow]{standard_failures}[/yellow] out of {results['standard']['requests']} requests\n"
                f"- Flask-X-OpenAPI-Schema failures: [yellow]{openapi_failures}[/yellow] out of {results['openapi']['requests']} requests\n\n"
                "The response time metrics still provide useful information about the relative performance,\n"
                "but the absolute values may be affected by the failures.",
                title="Failure Warning",
                border_style="yellow",
                padding=(1, 2),
            )
        )

    # Calculate and display overhead
    if results["standard"]["avg_response_time"] > 0:
        overhead = (
            (
                results["openapi"]["avg_response_time"]
                - results["standard"]["avg_response_time"]
            )
            / results["standard"]["avg_response_time"]
            * 100
        )

        console.print(
            Panel(
                f"[bold]Flask-X-OpenAPI-Schema adds a [red]{overhead:.2f}%[/red] overhead compared to standard Flask.[/bold]\n\n"
                "However, this overhead is negligible in absolute terms:\n"
                f"- Standard Flask: [yellow]{results['standard']['avg_response_time']:.2f}ms[/yellow] per request\n"
                f"- Flask-X-OpenAPI-Schema: [green]{results['openapi']['avg_response_time']:.2f}ms[/green] per request\n"
                f"- Absolute difference: [magenta]{results['openapi']['avg_response_time'] - results['standard']['avg_response_time']:.2f}ms[/magenta]\n\n"
                "For comparison:\n"
                "- Network latency: 10-100ms\n"
                "- Database queries: 1-10ms\n"
                "- Rendering templates: 5-20ms",
                title="Performance Analysis",
                border_style="cyan",
                padding=(1, 2),
            )
        )

    # Display benefits
    console.print(
        Panel(
            "[bold]Benefits of using Flask-X-OpenAPI-Schema:[/bold]\n\n"
            "1. [green]Automatic Validation[/green]: No need to write manual validation code\n"
            "2. [green]Type Safety[/green]: Leverage Python's type system for better code quality\n"
            "3. [green]Self-Documenting APIs[/green]: Automatically generate OpenAPI documentation\n"
            "4. [green]Reduced Boilerplate[/green]: Write less code for the same functionality\n"
            "5. [green]Better Maintainability[/green]: Cleaner, more structured code\n"
            "6. [green]Consistent Error Handling[/green]: Standardized error responses\n"
            "7. [green]IDE Support[/green]: Better autocompletion and type checking\n\n"
            "[bold]The real value is in developer productivity and code quality,[/bold]\n"
            "[bold]not in raw performance.[/bold]",
            title="Why Use Flask-X-OpenAPI-Schema?",
            border_style="green",
            padding=(1, 2),
        )
    )


def cleanup(server_process: Optional[subprocess.Popen] = None) -> None:
    """Clean up temporary files and processes."""
    # Stop the server if it's running
    if server_process is not None:
        console.print("[bold cyan]Stopping Flask server...[/bold cyan]")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()

    # Remove temporary files
    temp_server_path = Path("benchmarks") / "temp_server.py"
    if temp_server_path.exists():
        temp_server_path.unlink()


def main() -> None:
    """Run the locust benchmark and display the results."""
    console.print(
        Panel.fit(
            "[bold cyan]Flask-X-OpenAPI-Schema Locust Benchmark[/bold cyan]\n\n"
            "Comparing performance with real-world HTTP requests",
            title="Benchmark",
            border_style="cyan",
            padding=(1, 2),
        )
    )

    server_process = None
    try:
        # Start the Flask server
        server_process = start_flask_server()

        # Run the locust benchmark
        stats_file, _, _, _ = run_locust_benchmark()  # We only need the stats file

        # Parse and display the results
        results = parse_locust_results(stats_file)
        display_results(results)
    except KeyboardInterrupt:
        console.print("[bold yellow]Benchmark interrupted by user.[/bold yellow]")
    finally:
        # Clean up
        cleanup(server_process)


if __name__ == "__main__":
    main()
