import collections

import ollama

import lrag
from lrag.config import ChunkExtensions, ChunkStrategies, defaults


def get_document_for_query(
    db_fi: str, query: str, embedding_model: str, n_chunks: int
) -> dict[str, list]:
    con = lrag.db.connect_db(db_fi)
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
    descriptions = [d[0] for d in docs.description]

    mapped = collections.defaultdict(list)
    for row in docs.fetchall():
        for key, value in zip(descriptions, row):
            mapped[key].append(value)

    for v in mapped.values():
        assert len(v) == n_chunks

    return mapped


def query() -> None:
    # cli
    log_level = "DEBUG"
    n_chunks = 10
    embedding_model = defaults.embedding_model
    llm_model = defaults.llm_model
    db_fi = "temp.db"
    raw_query = "technical debt"

    # setup logging
    logger = lrag.logger.setup_logging(log_level)

    # TODO - could rephrase this query with an LLM - query rephrasiing / query rewriting (this is an extension)
    # would include the raw query and rephrased query??? not sure
    query = raw_query

    # get documents relevant for this query

    # TODO - should this return `chunks` - chunk dataclass objects?  yes
    docs = get_document_for_query(db_fi, query, embedding_model, n_chunks)
    logger.debug(f"document_fis: {set(docs['document_fi'])}")

    # synthesise a response using the documents with an LLM
    prompt = f"You are a RAG agent, answering queries from users. You will be given a query to answer, and a number of chunks of context. These chunks of context are found using vector similarity between the query and a document database. Please answer the following query:\n\n<query>{query}</query>\n\nChunks start:"

    # TODO insert the chunks into the prompt

    # TODO add the query again

    # run the query versus the LLM

    # optionally run the raw_query without any RAG context
