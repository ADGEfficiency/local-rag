.PHONY: setup test

UV_ARGS=""
setup:
	pip install uv
	uv pip install -r uv.lock $(UV_ARGS)
	brew install duckdb

test: setup
	uv pip install -r uv-test.lock $(UV_ARGS)
	pytest tests.py

help:
	python ingest.py --help
	echo ""
	python query.py --help
