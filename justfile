format-and-lintfix:
	ruff format
	ruff check --fix

setup-pre-commit:
	uv pip install pre-commit
	pre-commit install

run-pre-commit:
	pre-commit run --all-files

sync-all-deps:
	uv sync --all-extras --dev

test:
	uv run pytest

test-flask:
	uv run pytest tests/flask

test-flask-restful:
	uv run pytest tests/flask_restful

test-core:
	uv run pytest tests/core

benchmark-report:
	uv run python benchmarks/generate_report.py

benchmark-flask:
	mkdir -p benchmarks/results
	uv run python -m benchmarks.flask.app &
	SERVER_PID=$!
	sleep 2
	uv run locust -f benchmarks/flask/locustfile.py --headless -u 200 -r 20 -t 60s --csv=benchmarks/results/flask
	kill $SERVER_PID || true
	sleep 1

benchmark-flask-restful:
	mkdir -p benchmarks/results
	uv run python -m benchmarks.flask_restful.app &
	SERVER_PID=$!
	sleep 2
	uv run locust -f benchmarks/flask_restful/locustfile.py --headless -u 200 -r 20 -t 60s --csv=benchmarks/results/flask_restful
	kill $SERVER_PID || true
	sleep 1

benchmark: benchmark-flask benchmark-flask-restful benchmark-report
	@echo Done


run-example-flask:
	uv run python -m examples.flask.app

run-example-flask-restful:
	uv run python -m examples.flask_restful.app

docs:
	mkdir -p docs/api
	uv run pdoc -o docs/api src/flask_x_openapi_schema \
		--show-source \
		--mermaid \
		--search \
		--favicon "https://flask.palletsprojects.com/en/3.0.x/_static/flask-icon.png" \
		--footer-text "flask-x-openapi-schema - 自动生成OpenAPI文档的Flask工具"
	echo "API文档已生成在 docs/api 目录中"
	# 尝试打开文档（如果支持）
	xdg-open docs/api/flask_x_openapi_schema.html &> /dev/null || open docs/api/flask_x_openapi_schema.html &> /dev/null || echo "无法自动打开文档，请手动打开 docs/api/flask_x_openapi_schema.html"

docs-markdown:
	mkdir -p docs/markdown
	uv run pdoc -o docs/markdown -d markdown src/flask_x_openapi_schema
