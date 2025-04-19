# Benchmarks for flask-x-openapi-schema

This directory contains benchmarks for comparing the performance of Flask and Flask-RESTful with and without flask-x-openapi-schema.

## Structure

- `common/`: Shared models and utilities for benchmarks
- `flask/`: Flask-specific benchmarks
- `flask_restful/`: Flask-RESTful specific benchmarks
- `results/`: Benchmark results (created when running benchmarks)
- `generate_report.py`: Script to generate a benchmark report

## Running Benchmarks

To run all benchmarks:

This will:
1. Start a Flask server with both standard and OpenAPI endpoints
2. Run Locust load tests against the server
3. Start a Flask-RESTful server with both standard and OpenAPI endpoints
4. Run Locust load tests against the server
5. Generate a benchmark report

## Running Individual Benchmarks

To run only Flask benchmarks:

```bash
# Start the Flask server
python -m benchmarks.flask.app &

# Run the Locust load test
locust -f benchmarks/flask/locustfile.py --headless -u 100 -r 10 -t 30s --csv=benchmarks/results/flask

# Kill the server
kill $!
```

To run only Flask-RESTful benchmarks:

```bash
# Start the Flask-RESTful server
python -m benchmarks.flask_restful.app &

# Run the Locust load test
locust -f benchmarks/flask_restful/locustfile.py --headless -u 100 -r 10 -t 30s --csv=benchmarks/results/flask_restful

# Kill the server
kill $!
```

## Generating a Report

To generate a benchmark report:

```bash
python -m benchmarks.generate_report
```

This will create a report in `benchmarks/results/report.txt` and also print it to the console.

## Requirements

- Locust: `pip install locust`
- Rich: `pip install rich`
- Pandas: `pip install pandas`