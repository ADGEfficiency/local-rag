.PHONY: setup test

UV_ARGS ?=
setup-python:
	pip install uv
	uv pip install -r uv.lock $(UV_ARGS)

setup-linux: setup-python
	wget https://github.com/duckdb/duckdb/releases/download/v1.1.1/duckdb_cli-linux-amd64.zip
	unzip duckdb_cli-linux-amd64.zip

setup-macos: setup-python
	brew install duckdb

test:
	uv pip install -r uv-test.lock $(UV_ARGS)
	pytest tests.py -s

static:
	mypy *.py

help:
	python ingest.py --help
	@echo ""
	python query.py --help

lock:
	uv pip compile requirements.txt > uv.lock
	uv pip compile requirements-test.txt > uv-test.lock
