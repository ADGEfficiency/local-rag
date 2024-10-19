import collections
import time

import loguru
import ollama
import typer
from typing_extensions import Annotated

import lrag
from lrag.config import LogLevel, defaults

logger = loguru.logger

cli = typer.Typer(rich_markup_mode=None)


def get_document_for_query(
    db_fi: str, query: str, embedding_model: str, n_chunks: int
) -> dict[str, list]:
    con = lrag.db.connect_db(db_fi)
    print(ollama.pull(embedding_model))
    embedding_dim = len(
        ollama.embeddings(model=embedding_model, prompt="a")["embedding"]
    )

    docs = con.execute(
        f"""
        SELECT chunk, array_distance(vector, CAST(? AS FLOAT[{embedding_dim}])) as dist, document_fi
        FROM embeddings
        ORDER BY dist
        LIMIT {n_chunks};
        """,
        [ollama.embeddings(model=embedding_model, prompt=query)["embedding"]],
    )
    assert docs.description is not None
    descriptions = [d[0] for d in docs.description]

    mapped = collections.defaultdict(list)
    for row in docs.fetchall():
        for key, value in zip(descriptions, row):
            mapped[key].append(value)

    # for v in mapped.values():
    #     assert len(v) == n_chunks

    return mapped


def synthesize_prompt(query: str, docs: dict[str, list]) -> str:
    prompt = f"You are a RAG agent, answering queries from users. You will be given a query to answer, and a number of chunks of context. These chunks of context are found using vector similarity between the query and a document database. Please answer the following query:\n\n<query>{query}</query>\n\nChunks start:"

    for chunk, dist, document_fi in zip(
        docs["chunk"], docs["dist"], docs["document_fi"]
    ):
        prompt += f"<chunk>{chunk}</chunk>"

        logger.debug(f"{document_fi=}, {dist=}, {chunk=}")
    prompt += f"Please answer the following query:\n\n<query>{query}</query>"
    return prompt


def generate_response(prompt: str, llm_model: str) -> str:
    logger.debug("start generating response...")

    tic = time.time()
    options = ollama.Options(
        num_predict=defaults.max_tokens,
        temperature=defaults.temperature,
    )
    ollama.pull(llm_model)
    response = ollama.generate(model=llm_model, prompt=prompt, options=options)[
        "response"
    ]
    logger.debug(f"generated response in {time.time() - tic:.2f}s")
    return str(response)


@cli.command()
def query(
    query: Annotated[str, typer.Argument()],
    log_level: Annotated[LogLevel, typer.Option()] = LogLevel.INFO,
    embedding_model: Annotated[
        str,
        typer.Option(
            "--embedding",
            help="Model to embed the query. Should be the same model as used to embed the query.",
        ),
    ] = defaults.embedding_model,
    llm_model: Annotated[
        str,
        typer.Option(
            "--llm",
            help="Model used to generate the response.",
        ),
    ] = defaults.llm_model,
    n_chunks: Annotated[
        int, typer.Option("--chunks", help="Number of chunks to use in the RAG prompt.")
    ] = defaults.n_chunks,
    db_fi: Annotated[
        str, typer.Option("--db", help="DuckDB database file.")
    ] = defaults.db_fi,
    generate_with_no_context: Annotated[
        bool,
        typer.Option("--raw", help="Whether to query the raw LLM after the RAG LLM."),
    ] = defaults.generate_response_with_raw_query,
) -> None:
    # setup logging
    logger = lrag.logger.setup_logging(log_level)
    # TODO - query rephrasing

    # get documents relevant for this query
    # TODO - should this return `chunks` - chunk dataclass objects?  yes
    docs = get_document_for_query(db_fi, query, embedding_model, n_chunks)
    logger.info(f"got {len(docs)} documents for {query=}")
    logger.debug(f"document_fis: {set(docs['document_fi'])}")

    # synthesise a response using the documents with an LLM
    # this includes inserting chunks & appending prompt again
    prompt = synthesize_prompt(query, docs)

    # generate a response with the LLM
    response = generate_response(prompt, llm_model)

    # run the query versus the LLM
    logger.info(f"generated {response=}")

    # optionally run the raw_query without any RAG context
    if generate_with_no_context:
        response = generate_response(query, llm_model)
        logger.info(f"generated {response=}")

    # TODO - dump output to a debug text markdown file
