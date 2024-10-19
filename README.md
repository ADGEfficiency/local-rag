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
uv run ingest --help
Usage: ingest [OPTIONS] FOLDERS...

Arguments:
  FOLDERS...  Folders to process. Multiple folders can be specified.
              [required]

Options:
  --log-level [DEBUG|INFO|WARNING|ERROR|CRITICAL]
                                  [default: INFO]
  --glob TEXT                     File extension(s) to include. Can supply
                                  multiple values.  [default: *.md]
  --db TEXT                       DuckDB database file.  [default: db.duckdb]
  --embedding TEXT                Model to embed the query. Should be the same
                                  model as used to embed the query.  [default:
                                  snowflake-arctic-embed:335m]
  --reingest-files / --no-reingest-files
                                  Whether to reingest files.  [default:
                                  reingest-files]
  --chunk-strategy [characters|markdown-objects]
                                  Strategy for chunking the text.  [default:
                                  characters]
  --chunk-size INTEGER            Size of the chunks to embed.  [default:
                                  4000]
  --overlap FLOAT                 Percentage overlap between chunks.
                                  [default: 0.15]
  --chunk-extensions <CHOICE>     Extensions for chunking
  --install-completion            Install completion for the current shell.
  --show-completion               Show completion for the current shell, to
                                  copy it or customize the installation.
  --help                          Show this message and exit.

uv run query --help
Usage: query [OPTIONS] QUERY

Arguments:
  QUERY  [required]

Options:
  --log-level [DEBUG|INFO|WARNING|ERROR|CRITICAL]
                                  [default: INFO]
  --embedding TEXT                Model to embed the query. Should be the same
                                  model as used to embed the query.  [default:
                                  snowflake-arctic-embed:335m]
  --llm TEXT                      Model used to generate the response.
                                  [default: llama3.1:8b]
  --chunks INTEGER                Number of chunks to use in the RAG prompt.
                                  [default: 10]
  --db TEXT                       DuckDB database file.  [default: db.duckdb]
  --raw                           Whether to query the raw LLM after the RAG
                                  LLM.
  --install-completion            Install completion for the current shell.
  --show-completion               Show completion for the current shell, to
                                  copy it or customize the installation.
  --help                          Show this message and exit.
```

## Config Explanation

Precedence (high precendec to low):
CLI arguments
Env vars
Defaults in Python object
