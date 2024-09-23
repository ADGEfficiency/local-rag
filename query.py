import click
import duckdb
import ollama


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
    )

    print(final_response["response"])

    if raw:
        raw_response = ollama.generate(model=llm_model, prompt=query)
        print(raw_response["response"])


@click.command()
@click.argument("query", type=str)
@click.option("--embedding-model", default="mxbai-embed-large", type=str)
@click.option("--embedding-dim", default=1024, type=int)
@click.option("--llm", default="codellama:13b", type=str)
@click.option("--chunks", default=20, type=int)
@click.option("--db", default="db.duckdb", type=click.Path(exists=True))
@click.option(
    "--raw/--no-raw", default=True, help="Whether to query the raw LLM as well."
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
    query_database(query, embedding_model, llm, embedding_dim, chunks, db, raw)


if __name__ == "__main__":
    main()
