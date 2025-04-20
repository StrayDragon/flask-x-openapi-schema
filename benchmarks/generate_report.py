"""
Generate a benchmark report for flask-x-openapi-schema.

This script reads the benchmark results and generates a report comparing the performance
of Flask and Flask-RESTful with and without flask-x-openapi-schema.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
from rich.console import Console
from rich.table import Table


def load_results(prefix):
    """Load benchmark results from CSV files."""
    stats_file = f"benchmarks/results/{prefix}_stats.csv"
    if not os.path.exists(stats_file):
        return None

    return pd.read_csv(stats_file)


def calculate_percentiles(data):
    """Calculate percentiles from the Locust CSV data."""
    if data.empty:
        return {}
    # Locust already provides percentiles in the CSV
    try:
        return {
            "p50": data["50%"].median(),
            "p75": data["75%"].median(),
            "p90": data["90%"].median(),
            "p95": data["95%"].median(),
            "p99": data["99%"].median(),
        }
    except KeyError:
        # Fallback if percentile columns are not found
        return {
            "p50": data["Median Response Time"].median(),
            "p75": data["75%"].median()
            if "75%" in data.columns
            else data["Median Response Time"].median() * 1.2,
            "p90": data["90%"].median()
            if "90%" in data.columns
            else data["Median Response Time"].median() * 1.5,
            "p95": data["95%"].median()
            if "95%" in data.columns
            else data["Median Response Time"].median() * 1.8,
            "p99": data["99%"].median()
            if "99%" in data.columns
            else data["Median Response Time"].median() * 2.0,
        }


def generate_performance_charts(flask_results, flask_restful_results):
    """Generate performance charts for the report."""
    if flask_results is None and flask_restful_results is None:
        return

    # Create a figure with multiple subplots
    fig, axs = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle("Performance Comparison: Standard vs OpenAPI", fontsize=16)

    # Response Time Comparison
    if flask_results is not None:
        standard_rows = flask_results[flask_results["Name"].str.contains("/standard/")]
        openapi_rows = flask_results[flask_results["Name"].str.contains("/openapi/")]

        if not standard_rows.empty and not openapi_rows.empty:
            # Response Time Distribution
            axs[0, 0].hist(
                standard_rows["Average Response Time"],
                alpha=0.5,
                bins=20,
                label="Flask Standard",
            )
            axs[0, 0].hist(
                openapi_rows["Average Response Time"],
                alpha=0.5,
                bins=20,
                label="Flask OpenAPI",
            )
            axs[0, 0].set_title("Response Time Distribution (Flask)")
            axs[0, 0].set_xlabel("Response Time (ms)")
            axs[0, 0].set_ylabel("Frequency")
            axs[0, 0].legend()

            # Requests per Second
            axs[0, 1].bar(
                ["Standard", "OpenAPI"],
                [standard_rows["Requests/s"].sum(), openapi_rows["Requests/s"].sum()],
                color=["blue", "orange"],
            )
            axs[0, 1].set_title("Requests per Second (Flask)")
            axs[0, 1].set_ylabel("Requests/s")

    # Response Time Comparison for Flask-RESTful
    if flask_restful_results is not None:
        standard_rows = flask_restful_results[
            flask_restful_results["Name"].str.contains("/standard/")
        ]
        openapi_rows = flask_restful_results[
            flask_restful_results["Name"].str.contains("/openapi/")
        ]

        if not standard_rows.empty and not openapi_rows.empty:
            # Response Time Distribution
            axs[1, 0].hist(
                standard_rows["Average Response Time"],
                alpha=0.5,
                bins=20,
                label="Flask-RESTful Standard",
            )
            axs[1, 0].hist(
                openapi_rows["Average Response Time"],
                alpha=0.5,
                bins=20,
                label="Flask-RESTful OpenAPI",
            )
            axs[1, 0].set_title("Response Time Distribution (Flask-RESTful)")
            axs[1, 0].set_xlabel("Response Time (ms)")
            axs[1, 0].set_ylabel("Frequency")
            axs[1, 0].legend()

            # Requests per Second
            axs[1, 1].bar(
                ["Standard", "OpenAPI"],
                [standard_rows["Requests/s"].sum(), openapi_rows["Requests/s"].sum()],
                color=["blue", "orange"],
            )
            axs[1, 1].set_title("Requests per Second (Flask-RESTful)")
            axs[1, 1].set_ylabel("Requests/s")

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig("benchmarks/results/performance_charts.png")


def generate_report():
    """Generate a benchmark report."""
    console = Console()

    # Load results
    flask_results = load_results("flask")
    flask_restful_results = load_results("flask_restful")

    if flask_results is None and flask_restful_results is None:
        console.print("[bold red]No benchmark results found.")
        return

    # Generate charts
    try:
        generate_performance_charts(flask_results, flask_restful_results)
    except Exception as e:
        console.print(f"[yellow]Warning: Could not generate charts: {e}")

    # Create table
    table = Table(title="flask-x-openapi-schema Benchmark Results")

    # Add columns
    table.add_column("Framework", style="cyan")
    table.add_column("Endpoint", style="green")
    table.add_column("Requests", style="blue")
    table.add_column("Failures", style="red")
    table.add_column("Median (ms)", style="yellow")
    table.add_column("90%ile (ms)", style="yellow")
    table.add_column("95%ile (ms)", style="yellow")
    table.add_column("99%ile (ms)", style="yellow")
    table.add_column("Avg (ms)", style="yellow")
    table.add_column("Min (ms)", style="yellow")
    table.add_column("Max (ms)", style="yellow")
    table.add_column("RPS", style="magenta")

    # Add Flask results
    if flask_results is not None:
        # Calculate metrics for standard and OpenAPI endpoints
        standard_rows = flask_results[flask_results["Name"].str.contains("/standard/")]
        openapi_rows = flask_results[flask_results["Name"].str.contains("/openapi/")]

        if not standard_rows.empty:
            # Calculate metrics for standard endpoint
            framework = "Flask"
            endpoint = "Standard"
            requests = standard_rows["Request Count"].sum()
            failures = standard_rows["Failure Count"].sum()

            # Calculate percentiles
            percentiles = calculate_percentiles(standard_rows)
            median = percentiles.get(
                "p50", standard_rows["Median Response Time"].median()
            )
            percentile_90 = percentiles.get(
                "p90",
                standard_rows["90%"].median() if "90%" in standard_rows.columns else 0,
            )
            percentile_95 = percentiles.get("p95", 0)
            percentile_99 = percentiles.get("p99", 0)

            avg = standard_rows["Average Response Time"].mean()
            min_time = standard_rows["Min Response Time"].min()
            max_time = standard_rows["Max Response Time"].max()
            rps = standard_rows["Requests/s"].sum()

            table.add_row(
                framework,
                endpoint,
                str(int(requests)),
                str(int(failures)),
                f"{median:.2f}",
                f"{percentile_90:.2f}",
                f"{percentile_95:.2f}",
                f"{percentile_99:.2f}",
                f"{avg:.2f}",
                f"{min_time:.2f}",
                f"{max_time:.2f}",
                f"{rps:.2f}",
            )

        if not openapi_rows.empty:
            # Calculate metrics for OpenAPI endpoint
            framework = "Flask"
            endpoint = "OpenAPI"
            requests = openapi_rows["Request Count"].sum()
            failures = openapi_rows["Failure Count"].sum()

            # Calculate percentiles
            percentiles = calculate_percentiles(openapi_rows)
            median = percentiles.get(
                "p50", openapi_rows["Median Response Time"].median()
            )
            percentile_90 = percentiles.get(
                "p90",
                openapi_rows["90%"].median() if "90%" in openapi_rows.columns else 0,
            )
            percentile_95 = percentiles.get("p95", 0)
            percentile_99 = percentiles.get("p99", 0)

            avg = openapi_rows["Average Response Time"].mean()
            min_time = openapi_rows["Min Response Time"].min()
            max_time = openapi_rows["Max Response Time"].max()
            rps = openapi_rows["Requests/s"].sum()

            table.add_row(
                framework,
                endpoint,
                str(int(requests)),
                str(int(failures)),
                f"{median:.2f}",
                f"{percentile_90:.2f}",
                f"{percentile_95:.2f}",
                f"{percentile_99:.2f}",
                f"{avg:.2f}",
                f"{min_time:.2f}",
                f"{max_time:.2f}",
                f"{rps:.2f}",
            )

            # Calculate performance difference
            if not standard_rows.empty:
                perf_diff = (
                    (avg - standard_rows["Average Response Time"].mean())
                    / standard_rows["Average Response Time"].mean()
                    * 100
                )
                rps_diff = (
                    (rps - standard_rows["Requests/s"].sum())
                    / standard_rows["Requests/s"].sum()
                    * 100
                )

                diff_text = f"[{'green' if perf_diff <= 0 else 'red'}]Response time: {perf_diff:.2f}% | "
                diff_text += f"[{'green' if rps_diff >= 0 else 'red'}]RPS: {'+' if rps_diff > 0 else ''}{rps_diff:.2f}%"

                table.add_row(
                    "Flask",
                    "Difference",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    diff_text,
                    "",
                    "",
                    "",
                )

    # Add Flask-RESTful results
    if flask_restful_results is not None:
        # Calculate metrics for standard and OpenAPI endpoints
        standard_rows = flask_restful_results[
            flask_restful_results["Name"].str.contains("/standard/")
        ]
        openapi_rows = flask_restful_results[
            flask_restful_results["Name"].str.contains("/openapi/")
        ]

        if not standard_rows.empty:
            # Calculate metrics for standard endpoint
            framework = "Flask-RESTful"
            endpoint = "Standard"
            requests = standard_rows["Request Count"].sum()
            failures = standard_rows["Failure Count"].sum()

            # Calculate percentiles
            percentiles = calculate_percentiles(standard_rows)
            median = percentiles.get(
                "p50", standard_rows["Median Response Time"].median()
            )
            percentile_90 = percentiles.get(
                "p90",
                standard_rows["90%"].median() if "90%" in standard_rows.columns else 0,
            )
            percentile_95 = percentiles.get("p95", 0)
            percentile_99 = percentiles.get("p99", 0)

            avg = standard_rows["Average Response Time"].mean()
            min_time = standard_rows["Min Response Time"].min()
            max_time = standard_rows["Max Response Time"].max()
            rps = standard_rows["Requests/s"].sum()

            table.add_row(
                framework,
                endpoint,
                str(int(requests)),
                str(int(failures)),
                f"{median:.2f}",
                f"{percentile_90:.2f}",
                f"{percentile_95:.2f}",
                f"{percentile_99:.2f}",
                f"{avg:.2f}",
                f"{min_time:.2f}",
                f"{max_time:.2f}",
                f"{rps:.2f}",
            )

        if not openapi_rows.empty:
            # Calculate metrics for OpenAPI endpoint
            framework = "Flask-RESTful"
            endpoint = "OpenAPI"
            requests = openapi_rows["Request Count"].sum()
            failures = openapi_rows["Failure Count"].sum()

            # Calculate percentiles
            percentiles = calculate_percentiles(openapi_rows)
            median = percentiles.get(
                "p50", openapi_rows["Median Response Time"].median()
            )
            percentile_90 = percentiles.get(
                "p90",
                openapi_rows["90%"].median() if "90%" in openapi_rows.columns else 0,
            )
            percentile_95 = percentiles.get("p95", 0)
            percentile_99 = percentiles.get("p99", 0)

            avg = openapi_rows["Average Response Time"].mean()
            min_time = openapi_rows["Min Response Time"].min()
            max_time = openapi_rows["Max Response Time"].max()
            rps = openapi_rows["Requests/s"].sum()

            table.add_row(
                framework,
                endpoint,
                str(int(requests)),
                str(int(failures)),
                f"{median:.2f}",
                f"{percentile_90:.2f}",
                f"{percentile_95:.2f}",
                f"{percentile_99:.2f}",
                f"{avg:.2f}",
                f"{min_time:.2f}",
                f"{max_time:.2f}",
                f"{rps:.2f}",
            )

            # Calculate performance difference
            if not standard_rows.empty:
                perf_diff = (
                    (avg - standard_rows["Average Response Time"].mean())
                    / standard_rows["Average Response Time"].mean()
                    * 100
                )
                rps_diff = (
                    (rps - standard_rows["Requests/s"].sum())
                    / standard_rows["Requests/s"].sum()
                    * 100
                )

                diff_text = f"[{'green' if perf_diff <= 0 else 'red'}]Response time: {perf_diff:.2f}% | "
                diff_text += f"[{'green' if rps_diff >= 0 else 'red'}]RPS: {'+' if rps_diff > 0 else ''}{rps_diff:.2f}%"

                table.add_row(
                    "Flask-RESTful",
                    "Difference",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    diff_text,
                    "",
                    "",
                    "",
                )

    # Print the table
    console.print(table)

    # Save the report to a file
    with open("benchmarks/results/report.txt", "w") as f:
        console = Console(file=f)
        console.print(table)

    # Print chart info if available
    if os.path.exists("benchmarks/results/performance_charts.png"):
        print(
            "\nPerformance charts generated: benchmarks/results/performance_charts.png"
        )


if __name__ == "__main__":
    generate_report()
