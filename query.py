import click
import ollama

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
    con = common.connect_db(db_fi)
    rows = con.execute(
        f"""
        SELECT chunk
        FROM embeddings
        ORDER BY array_distance(vector, CAST(? AS FLOAT[{embedding_dim}]))
        LIMIT {n_chunks};
        """,
        [ollama.embeddings(model=embedding_model, prompt=query)["embedding"]],
    ).fetchall()

    print("{n_chunks} CHUNKS:")

    synthesized_prompt = "Here are some relevant pieces of information:\n\n"
    for row in rows:
        print(row)
        print("")
        synthesized_prompt += row[0] + "\n\n"
    synthesized_prompt += f"Here is the original query: '{query}'\n\n"

    final_response = ollama.generate(
        model=llm_model,
        prompt=synthesized_prompt,
        options={"num_predict": 64, "temperature": 0},
    )

    print(f'\nRAG:\n{final_response["response"]}')

    if raw:
        raw_response = ollama.generate(
            model=llm_model,
            prompt=query,
            options={"num_predict": 64, "temperature": 0},
        )
        print(f'\nRAW LLM:\n{raw_response["response"]}')


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
