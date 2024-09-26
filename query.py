import click
import ollama
import rich

import common


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
    con = common.connect_db(db_fi)
    rows = con.execute(
        f"""
        SELECT chunk, array_distance(vector, CAST(? AS FLOAT[{embedding_dim}])) as dist, document_fi
        FROM embeddings
        ORDER BY dist
        LIMIT {n_chunks};
        """,
        [ollama.embeddings(model=embedding_model, prompt=query)["embedding"]],
    ).fetchall()

    print("{n_chunks} CHUNKS:")

    synthesized_prompt = "Here are some relevant pieces of information:\n\n"
    for chunk, dist, document_fi in rows:
        console.print(rich.panel.Panel(f"{dist=}, {chunk=}", title=document_fi))
        print("")
        synthesized_prompt += chunk + "\n\n"
    synthesized_prompt += f"Here is the original query: '{query}'\n\n"

    options = {
        "num_predict": common.defaults.max_tokens,
        "temperature": common.defaults.temperature,
    }
    final_response = ollama.generate(
        model=llm_model,
        prompt=synthesized_prompt,
        options=options,
    )

    console.print(rich.panel.Panel(final_response["response"], title="RAG Response"))

    if raw:
        raw_response = ollama.generate(
            model=llm_model,
            prompt=query,
            options=options,
        )
        console.print(rich.panel.Panel(raw_response["response"], title="Raw LLM"))


@click.command()
@click.argument("query", type=str)
@click.option(
    "--embedding-model",
    default=common.defaults.embedding_model,
    type=str,
    help="Model to embed the query.  Should be the same model as used to create the chunks in the database.",
)
@click.option(
    "--embedding-dim",
    default=1024,
    type=int,
    help="Dimension of the embeddings.  Should match the embedding model.",
)
@click.option(
    "--llm", default=common.defaults.llm_model, type=str, help="The LLM model."
)
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
