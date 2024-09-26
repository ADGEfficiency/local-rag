.PHONY: setup test

UV_ARGS ?= ""
setup-python:
	pip install uv
	uv pip install -r uv.lock $(UV_ARGS)

setup-linux: setup-python
	wget https://github.com/duckdb/duckdb/releases/latest/download/duckdb_cli-linux-amd64
	chmod +x duckdb_cli-linux-amd64
	sudo mv duckdb_cli-linux-amd64 /usr/local/bin/duckdb

setup-macos: setup-python
	brew install duckdb

test:
	uv pip install -r uv-test.lock $(UV_ARGS)
	pytest tests.py

help:
	python ingest.py --help
	echo ""
	python query.py --help

lock:
	uv pip compile requirements.txt > uv.lock
	uv pip compile requirements-test.txt > uv-test.lock
