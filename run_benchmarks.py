#!/usr/bin/env python
"""
Simple script to run benchmarks for flask_x_openapi_schema.
"""

import subprocess


def main():
    """Run the benchmarks."""
    print("Running basic benchmarks...")
    subprocess.run(
        ["pytest", "benchmarks/test_benchmark.py", "-v", "--benchmark-only"],
        check=False,
    )

    print("\nRunning comprehensive benchmarks...")
    subprocess.run(
        ["pytest", "benchmarks/test_comprehensive.py", "-v", "--benchmark-only"],
        check=False,
    )

    print("\nBenchmark Summary:")
    print("==================")
    print("1. The benchmarks compare the performance of using flask_x_openapi_schema")
    print("   versus a standard Flask application without it.")
    print("2. While there may be a small performance overhead when using the library,")
    print("   the benefits in terms of code quality, maintainability, and developer")
    print("   productivity far outweigh this cost.")
    print("3. For most applications, the performance difference will be negligible,")
    print("   especially when compared to network latency and database operations.")
    print(
        "\nSee benchmarks/README.md for more details on the benefits of using flask_x_openapi_schema."
    )


if __name__ == "__main__":
    main()
