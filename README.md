# RAG from Scratch

A RAG tool that can be run locally on your own data.

An alternative name for this project would be `Minimal RAG`.

It uses Ollama for embeddings and LLMs, and DuckDB as a vector database.

## Setup

```shell-session
$ make setup
```

## Use

```shell-session
$ python ingest.py path/to/your/files
```

```shell-session
$ python query.py "your query here"
```

## Examples

```shell-session
$ python ingest.py ~/personal/para/resource ~/programming-resources --glob "*.md" --embedding-model mxbai-embed-large --db resource.duckdb
```

## Help

```shell-session
$ make help
```

```
python ingest.py --help
Usage: ingest.py [OPTIONS] [FOLDERS]...

Options:
  --chunk-size INTEGER     Size of the chunks to embed.
  --overlap FLOAT          Percentage overlap between chunks.
  --db TEXT                DuckDB database file.
  --glob TEXT              File extension(s) to include. Should be quoted to
                           avoid shell expansion of the wildcard.  Usage
                           `--glob "*.md" --glob "*.txt"`.
  --embedding-model TEXT   Model to embed the query.  Should be the same model
                           as used to embed the query.
  --embedding-dim INTEGER  Dimension of the embeddings.  Should match the
                           embedding model.
  --help                   Show this message and exit.
echo ""

python query.py --help
Usage: query.py [OPTIONS] QUERY

Options:
  --embedding-model TEXT   Model to embed the query.  Should be the same model
                           as used to create the chunks in the database.
  --embedding-dim INTEGER  Dimension of the embeddings.  Should match the
                           embedding model.
  --llm TEXT               The LLM model.
  --chunks INTEGER         Number of chunks to use in the RAG prompt.
  --db PATH                DuckDB database file.
  --raw / --no-raw         Whether to query the raw LLM after the RAG LLM.
  --help                   Show this message and exit.
```
