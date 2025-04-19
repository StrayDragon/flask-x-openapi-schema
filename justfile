format-and-lintfix:
	ruff format
	ruff check --fix

sync-all-deps:
	uv sync --all-extras

test:
	uv run pytest

test-flask:
	uv run pytest tests/flask

test-flask-restful:
	uv run pytest tests/flask_restful

test-core:
	uv run pytest tests/core

benchmark-report:
	#!/usr/bin/env bash
	# Generate benchmark report
	uv run python benchmarks/generate_report.py
	# Display the performance chart if available
	if [ -f benchmarks/results/performance_charts.png ]; then
		echo "\nOpening performance chart..."
		xdg-open benchmarks/results/performance_charts.png &> /dev/null || open benchmarks/results/performance_charts.png &> /dev/null || echo "Could not open performance chart automatically."
	fi

benchmark-flask:
	#!/usr/bin/env bash
	# Create results directory if it doesn't exist
	mkdir -p benchmarks/results
	# Run the Flask app in the background
	uv run python -m benchmarks.flask.app &
	SERVER_PID=$!
	sleep 2
	# Run Locust with more users and longer duration for better statistics
	uv run locust -f benchmarks/flask/locustfile.py --headless -u 200 -r 20 -t 60s --csv=benchmarks/results/flask
	kill $SERVER_PID || true
	sleep 1

benchmark-flask-restful:
	#!/usr/bin/env bash
	# Create results directory if it doesn't exist
	mkdir -p benchmarks/results
	# Run the Flask-RESTful app in the background
	uv run python -m benchmarks.flask_restful.app &
	SERVER_PID=$!
	sleep 2
	# Run Locust with more users and longer duration for better statistics
	uv run locust -f benchmarks/flask_restful/locustfile.py --headless -u 200 -r 20 -t 60s --csv=benchmarks/results/flask_restful
	kill $SERVER_PID || true
	sleep 1

benchmark:
	#!/usr/bin/env bash
	# Run all benchmarks
	just benchmark-flask
	just benchmark-flask-restful
	just benchmark-report
	# Show the report location
	echo "\nBenchmark report generated at: benchmarks/results/report.txt"
	echo "Performance charts (if available) at: benchmarks/results/performance_charts.png"

# 示例运行命令
run-example-flask-simple:
	uv run python -m examples.flask.simple_api

run-example-flask-file:
	uv run python -m examples.flask.file_upload

run-example-flask-i18n:
	uv run python -m examples.flask.i18n_demo

run-example-restful-simple:
	uv run python -m examples.flask_restful.simple_api

run-example-restful-file:
	uv run python -m examples.flask_restful.file_upload

run-example-restful-i18n:
	uv run python -m examples.flask_restful.i18n_demo

# 运行所有示例
run-all-examples:
	@echo "运行 Flask 基本示例..."
	just run-example-flask-simple
	@echo "\n运行 Flask 文件上传示例..."
	just run-example-flask-file
	@echo "\n运行 Flask 国际化示例..."
	just run-example-flask-i18n
	@echo "\n运行 Flask-RESTful 基本示例..."
	just run-example-restful-simple
	@echo "\n运行 Flask-RESTful 文件上传示例..."
	just run-example-restful-file
	@echo "\n运行 Flask-RESTful 国际化示例..."
	just run-example-restful-i18n