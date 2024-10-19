.PHONY: setup test

UV_ARGS ?=--system
setup-python:
	pip install uv
	uv pip install -r pyproject.toml $(UV_ARGS) --all-extras
	uv pip install -e . $(UV_ARGS)

setup-linux: setup-python
	wget https://github.com/duckdb/duckdb/releases/download/v1.1.1/duckdb_cli-linux-amd64.zip
	unzip duckdb_cli-linux-amd64.zip

setup-macos: setup-python
	brew install duckdb

setup-test: setup-python
	uv pip install -r pyproject.toml $(UV_ARGS) --extra test

test: setup-test
	uv run pytest tests -s

static: setup-test
	mypy *.py

help:
	python ingest.py --help
	@echo ""
	python query.py --help

lock:
	uv lock
