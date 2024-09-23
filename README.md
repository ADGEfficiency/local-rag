# RAG from Scratch

A RAG tool that can be run locally on your own data.

An alternative name for this project would be `Minimal RAG`.

It uses Ollama for embeddings and LLMs, and DuckDB as a vector database.

## Use

```shell-session
$ python ingest.py path/to/your/files
```

```shell-session
$ python query.py "your query here"
```
