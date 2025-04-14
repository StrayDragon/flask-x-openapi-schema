format-and-lintfix:
	ruff format
	ruff check --fix

sync-all-deps:
	uv sync --all-extras

test:
	uv run pytest

benchmark-report:
	uv run python benchmarks/locust_report.py

benchmark: && benchmark-report
	uv run bash benchmarks/run_benchmark.sh
