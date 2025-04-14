#!/usr/bin/env python
"""
Script to run all benchmarks and generate a report.
"""

import os
import sys
import subprocess
import json
from pathlib import Path

# Add the current directory to the path so we can import the models
sys.path.insert(0, str(Path(__file__).parent))


def run_benchmark(benchmark_file):
    """Run a benchmark file and return the results."""
    print(f"Running {benchmark_file}...")
    result = subprocess.run(
        ["pytest", benchmark_file, "--benchmark-json=output.json"],
        capture_output=True,
        text=True,
    )
    print(result.stdout)

    # Load the benchmark results
    try:
        with open("output.json", "r") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print("No benchmark results found.")
        return None


def generate_report(results):
    """Generate a report from the benchmark results."""
    if not results:
        return

    print("\n" + "=" * 80)
    print("BENCHMARK RESULTS")
    print("=" * 80)

    for result in results:
        if not result:
            continue

        print(f"\nBenchmark: {result.get('machine_info', {}).get('node', 'Unknown')}")
        print("-" * 80)

        benchmarks = result.get("benchmarks", [])
        for benchmark in benchmarks:
            name = benchmark.get("name", "Unknown")
            mean = benchmark.get("stats", {}).get("mean", 0) * 1000  # Convert to ms
            min_time = benchmark.get("stats", {}).get("min", 0) * 1000  # Convert to ms
            max_time = benchmark.get("stats", {}).get("max", 0) * 1000  # Convert to ms

            print(
                f"{name}: {mean:.2f}ms (min: {min_time:.2f}ms, max: {max_time:.2f}ms)"
            )

    print("\n" + "=" * 80)


def main():
    """Run all benchmarks and generate a report."""
    # Change to the benchmarks directory
    os.chdir(Path(__file__).parent)

    # Run the benchmarks
    results = []

    # Basic benchmark
    results.append(run_benchmark("test_benchmark.py"))

    # Comprehensive benchmark
    results.append(run_benchmark("test_comprehensive.py"))

    # Generate the report
    generate_report(results)

    # Clean up
    if os.path.exists("output.json"):
        os.remove("output.json")


if __name__ == "__main__":
    main()
