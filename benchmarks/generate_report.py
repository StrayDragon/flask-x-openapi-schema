"""Generate a benchmark report for flask-x-openapi-schema.

This script reads the benchmark results and generates a report comparing the performance
of Flask and Flask-RESTful with and without flask-x-openapi-schema.
"""

import os

import matplotlib.pyplot as plt
import pandas as pd
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

    # Extract percentiles directly from the data
    percentiles = {}
    for p in ["50%", "75%", "90%", "95%", "99%"]:
        if p in data.columns:
            percentiles[p.replace("%", "")] = data[p].median()

    # Fallback for missing percentiles
    if "50" not in percentiles and "Median Response Time" in data.columns:
        percentiles["50"] = data["Median Response Time"].median()

    return percentiles


def generate_performance_charts(flask_results, flask_restful_results):
    """Generate performance charts for the report."""
    if flask_results is None and flask_restful_results is None:
        return

    # Create a figure with multiple subplots
    fig, axs = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle("Performance Comparison: Standard vs OpenAPI", fontsize=16)

    # Process Flask results
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

    # Process Flask-RESTful results
    if flask_restful_results is not None:
        standard_rows = flask_restful_results[flask_restful_results["Name"].str.contains("/standard/")]
        openapi_rows = flask_restful_results[flask_restful_results["Name"].str.contains("/openapi/")]

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


def calculate_metrics(data, endpoint_type):
    """Calculate metrics for a specific endpoint type."""
    if data is None or data.empty:
        return None

    rows = data[data["Name"].str.contains(f"/{endpoint_type}/")]
    if rows.empty:
        return None

    metrics = {
        "requests": rows["Request Count"].sum(),
        "failures": rows["Failure Count"].sum(),
        "success_rate": 100 - (rows["Failure Count"].sum() / rows["Request Count"].sum() * 100),
        "avg_response_time": rows["Average Response Time"].mean(),
        "min_response_time": rows["Min Response Time"].min(),
        "max_response_time": rows["Max Response Time"].max(),
        "rps": rows["Requests/s"].sum(),
    }

    # Add percentiles
    percentiles = calculate_percentiles(rows)
    for p, value in percentiles.items():
        metrics[f"p{p}"] = value

    return metrics


def generate_report():
    """Generate a benchmark report."""
    console = Console()

    # Load results
    flask_results = load_results("flask")
    flask_restful_results = load_results("flask_restful")

    if flask_results is None and flask_restful_results is None:
        console.print("[bold red]No benchmark results found.")
        # 创建一个空的报告文件,表示尝试过生成报告
        with open("benchmarks/results/report.txt", "w") as f:
            f.write("No benchmark results found.\n")
        return

    # 确保结果目录存在
    os.makedirs("benchmarks/results", exist_ok=True)

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
    table.add_column("Success Rate", style="green")
    table.add_column("Median (ms)", style="yellow")
    table.add_column("95%ile (ms)", style="yellow")
    table.add_column("Avg (ms)", style="yellow")
    table.add_column("RPS", style="magenta")
    table.add_column("Overhead", style="red")

    # Process Flask results
    if flask_results is not None:
        std_metrics = calculate_metrics(flask_results, "standard")
        api_metrics = calculate_metrics(flask_results, "openapi")

        if std_metrics and api_metrics:
            # Standard endpoint row
            table.add_row(
                "Flask",
                "Standard",
                str(int(std_metrics["requests"])),
                f"{std_metrics['success_rate']:.2f}%",
                f"{std_metrics.get('p50', 0):.2f}",
                f"{std_metrics.get('p95', 0):.2f}",
                f"{std_metrics['avg_response_time']:.2f}",
                f"{std_metrics['rps']:.2f}",
                "baseline",
            )

            # OpenAPI endpoint row
            overhead = (
                (api_metrics["avg_response_time"] - std_metrics["avg_response_time"])
                / std_metrics["avg_response_time"]
                * 100
            )

            table.add_row(
                "Flask",
                "OpenAPI",
                str(int(api_metrics["requests"])),
                f"{api_metrics['success_rate']:.2f}%",
                f"{api_metrics.get('p50', 0):.2f}",
                f"{api_metrics.get('p95', 0):.2f}",
                f"{api_metrics['avg_response_time']:.2f}",
                f"{api_metrics['rps']:.2f}",
                f"{overhead:+.2f}%",
            )

    # Process Flask-RESTful results
    if flask_restful_results is not None:
        std_metrics = calculate_metrics(flask_restful_results, "standard")
        api_metrics = calculate_metrics(flask_restful_results, "openapi")

        if std_metrics and api_metrics:
            # Standard endpoint row
            table.add_row(
                "Flask-RESTful",
                "Standard",
                str(int(std_metrics["requests"])),
                f"{std_metrics['success_rate']:.2f}%",
                f"{std_metrics.get('p50', 0):.2f}",
                f"{std_metrics.get('p95', 0):.2f}",
                f"{std_metrics['avg_response_time']:.2f}",
                f"{std_metrics['rps']:.2f}",
                "baseline",
            )

            # OpenAPI endpoint row
            overhead = (
                (api_metrics["avg_response_time"] - std_metrics["avg_response_time"])
                / std_metrics["avg_response_time"]
                * 100
            )

            table.add_row(
                "Flask-RESTful",
                "OpenAPI",
                str(int(api_metrics["requests"])),
                f"{api_metrics['success_rate']:.2f}%",
                f"{api_metrics.get('p50', 0):.2f}",
                f"{api_metrics.get('p95', 0):.2f}",
                f"{api_metrics['avg_response_time']:.2f}",
                f"{api_metrics['rps']:.2f}",
                f"{overhead:+.2f}%",
            )

    # Print the table
    console.print(table)

    # Save the report to a file
    with open("benchmarks/results/report.txt", "w") as f:
        console = Console(file=f)
        console.print(table)

    # Print chart info if available
    if os.path.exists("benchmarks/results/performance_charts.png"):
        print("\nPerformance charts generated: benchmarks/results/performance_charts.png")


if __name__ == "__main__":
    generate_report()
