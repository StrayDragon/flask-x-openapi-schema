format-and-lintfix:
	ruff format
	ruff check --fix

sync-all-deps:
	uv sync --all-extras --dev

test *pattern='':
    #!/usr/bin/env bash
    if [ -z "{{pattern}}" ]; then
        uv run pytest
    else
        uv run pytest {{pattern}}
    fi

benchmark-report:
	uv run python benchmarks/generate_report.py

benchmark-flask:
	#!/bin/bash
	mkdir -p benchmarks/results
	uv run python -m benchmarks.flask.app &
	SERVER_PID=$!
	sleep 2
	uv run locust -f benchmarks/flask/locustfile.py --headless -u 200 -r 20 -t 60s --csv=benchmarks/results/flask
	kill $SERVER_PID || true
	sleep 1

benchmark-flask-restful:
	#!/bin/bash
	mkdir -p benchmarks/results
	uv run python -m benchmarks.flask_restful.app &
	SERVER_PID=$!
	sleep 2
	uv run locust -f benchmarks/flask_restful/locustfile.py --headless -u 200 -r 20 -t 60s --csv=benchmarks/results/flask_restful
	kill $SERVER_PID || true
	sleep 1

benchmark: benchmark-flask benchmark-flask-restful benchmark-report
	@echo Done


example-flask:
	uv run python -m examples.flask.app

example-flask-restful:
	uv run python -m examples.flask_restful.app

mkdocs-build:
	uv run mkdocs build

mkdocs-serve:
	uv run mkdocs serve

mkdocs-deploy:
	uv run mkdocs gh-deploy --force
