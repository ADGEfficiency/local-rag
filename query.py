import click
import duckdb
import ollama

from common import defaults


def query_database(
    query: str,
    embedding_model: str,
    llm_model: str,
    embedding_dim: int,
    n_chunks: int,
    db: str,
    raw: bool,
) -> None:
    con = duckdb.connect(db)
    con.execute("install vss; load vss;")
    con.execute("SET hnsw_enable_experimental_persistence=true;")

    embedding = ollama.embeddings(model=embedding_model, prompt=query)["embedding"]
    results = con.execute(
        f"""
        SELECT chunk
        FROM embeddings
        ORDER BY array_distance(vector, CAST(? AS FLOAT[{embedding_dim}]))
        LIMIT {n_chunks};
        """,
        [embedding],
    )
    rows = results.fetchall()

    print("{n_chunks} CHUNKS:")
    for result in rows:
        print(result)
        print("")

    synthesized_prompt = "Here are some relevant pieces of information:\n\n"
    for row in rows:
        synthesized_prompt += row[0] + "\n\n"

    synthesized_prompt += f"Here is the original query: '{query}'\n\n"

    final_response = ollama.generate(
        model=llm_model,
        prompt=synthesized_prompt,
        options={"num_predict": 64, "temperature": 0},
    )

    print(f'RAG:\n{final_response["response"]}')

    if raw:
        raw_response = ollama.generate(
            model=llm_model,
            prompt=query,
            options={"num_predict": 64, "temperature": 0},
        )
        print(f'RAW:\n{raw_response["response"]}')


@click.command()
@click.argument("query", type=str)
@click.option(
    "--embedding-model",
    default=defaults.embedding_model,
    type=str,
    help="Model to embed the query.  Should be the same model as used to create the chunks in the database.",
)
@click.option(
    "--embedding-dim",
    default=1024,
    type=int,
    help="Dimension of the embeddings.  Should match the embedding model.",
)
@click.option("--llm", default=defaults.llm_model, type=str, help="The LLM model.")
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
