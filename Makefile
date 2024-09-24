.PHONY: setup test

setup:
	pip install uv
	uv pip install -r uv.lock
	brew install duckdb

test: setup
	uv pip install -r uv-test.lock
	pytest tests.py
