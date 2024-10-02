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

    print(f"{n_chunks} CHUNKS:")

    prompt = f"query: {query}"
    topics = ext.get_topics(prompt, llm_model)
    prompt += f" topics: {topics}"
    print(f"{query=} {topics=}")

    for chunk, dist, document_fi in rows:
        console.print(
            rich.panel.Panel(
                f"{dist=}, {chunk=}", title=f"[yellow]CHUNK: {document_fi}[/]"
            )
        )
        print("")
        prompt += f" content: {chunk}"
    prompt += f"query: {query}"

    options = ollama.Options(
        num_predict=core.defaults.max_tokens,
        temperature=core.defaults.temperature,
    )
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
