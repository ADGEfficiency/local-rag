import click
import ollama
import rich

import core
import ext


def query_database(
    query: str,
    embedding_model: str,
    llm_model: str,
    embedding_dim: int,
    n_chunks: int,
    db_fi: str,
    raw: bool,
) -> None:
    console = rich.console.Console()
    con = core.connect_db(db_fi, embedding_dim)
    rows = con.execute(
        f"""
        SELECT chunk, array_distance(vector, CAST(? AS FLOAT[{embedding_dim}])) as dist, document_fi
        FROM embeddings
        ORDER BY dist
        LIMIT {n_chunks};
        """,
        [ollama.embeddings(model=embedding_model, prompt=query)["embedding"]],
    ).fetchall()

    docs = [row[2] for row in rows]
    import collections
    print(f"{len(rows)} chunks in document_fis: {collections.Counter(docs)}")

    prompt = f"You are a RAG agent, answering queries from users. You will be given a query to answer, and a number of chunks of context. These chunks of context are found using vector similarity between the query and a document database. Please answer the following query:\n\n<query>{query}</query>\n\nChunks start:"

    for chunk, dist, document_fi in rows:
        console.print(
            rich.panel.Panel(
                f"{dist=}, {chunk=}", title=f"[yellow]chunk from {document_fi}[/]"
            )
        )
        print("")
        prompt += f"<chunk>{chunk}</chunk>"
    prompt += f"Please answer the following query:\n\n<query>{query}</query>"

    options = ollama.Options(
        num_predict=core.defaults.max_tokens,
        temperature=core.defaults.temperature,
    )
    ollama.pull(llm_model)
    final_response = ollama.generate(
        model=llm_model,
        prompt=prompt,
        options=options,
    )

    if raw:
        raw_response = ollama.generate(
            model=llm_model,
            prompt=query,
            options=options,
        )
        console.print(rich.panel.Panel(raw_response["response"], title="[red]Raw LLM"))

    console.print(
        rich.panel.Panel(final_response["response"], title="[green]RAG Response[/]")
    )
    print(final_response["response"])


@click.command()
@click.argument("query", type=str)
@click.option(
    "--embedding-model",
    default=core.defaults.embedding_model,
    type=str,
    help="Model to embed the query.  Should be the same model as used to create the chunks in the database.",
)
@click.option(
    "--embedding-dim",
    default=1024,
    type=int,
    help="Dimension of the embeddings.  Should match the embedding model.",
)
@click.option("--llm", default=core.defaults.llm_model, type=str, help="The LLM model.")
@click.option(
    "--chunks", default=10, type=int, help="Number of chunks to use in the RAG prompt."
)
@click.option(
    "--db",
    default="db.duckdb",
    type=click.Path(exists=True),
    help="DuckDB database file.",
)
@click.option(
    "--raw/--no-raw",
    default=True,
    help="Whether to query the raw LLM after the RAG LLM.",
)
def main(
    query: str,
    embedding_model: str,
    embedding_dim: int,
    llm: str,
    chunks: int,
    db: str,
    raw: bool,
) -> None:
    ollama.pull(embedding_model)
    ollama.pull(llm)
    query_database(query, embedding_model, llm, embedding_dim, chunks, db, raw)


if __name__ == "__main__":
    main()
