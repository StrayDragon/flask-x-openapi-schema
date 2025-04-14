#!/usr/bin/env python
"""
Script to run the flask_x_openapi_schema benchmarks.
"""

import os
import subprocess
import sys
import argparse


def main():
    """Run the benchmarks."""
    parser = argparse.ArgumentParser(description="Run flask_x_openapi_schema benchmarks")
    parser.add_argument(
        "--enhanced",
        action="store_true",
        help="Run the enhanced benchmark with rich output"
    )
    parser.add_argument(
        "--simple",
        action="store_true",
        help="Run the simple benchmark"
    )
    args = parser.parse_args()

    # Change to the benchmarks directory
    os.chdir(os.path.join(os.path.dirname(__file__), "benchmarks"))

    # If no specific benchmark is selected, run the enhanced one by default
    if not (args.enhanced or args.simple):
        args.enhanced = True

    # Run the enhanced benchmark if requested
    if args.enhanced:
        print("Running enhanced benchmark with rich output...")
        subprocess.run([sys.executable, "enhanced_benchmark.py"], check=True)

    # Run the simple benchmark if requested
    if args.simple:
        print("\nRunning simple benchmark...")
        subprocess.run([sys.executable, "simple_benchmark.py"], check=True)

    # Print additional information
    print("\nFor more details on the benefits of using flask_x_openapi_schema,")
    print("see the benchmarks/README.md file.")


if __name__ == "__main__":
    main()
