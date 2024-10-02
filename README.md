# Local RAG

RAG that you can run locally, on your own data. Ollama for embeddings and LLMs, with DuckDB as a vector database.

Alternative names for this project would be `Minimal RAG`, or `RAG From Scratch`.

## Setup

```shell-session
$ make setup
```

## Use

Ingest all Markdown files from `~/programming-resources` into a database `resource.duckdb`:

```shell-session
$ python ingest.py ~/programming-resources --glob "*.md" --embedding-model mxbai-embed-large --db resource.duckdb
```

Query the `resource.duckdb` database for the most relevant chunks to the query "how to install python":

```shell-session
$ python query.py "how to install python" --embedding-model mxbai-embed-large --db resource.duckdb
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
  --llm TEXT               The LLM model. Only used for propsitional chunking
                           of topics.
  --help                   Show this message and exit.

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
