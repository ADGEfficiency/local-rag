import duckdb
import ollama
from rich import print

from lrag.config import defaults
from lrag.models import Chunk


def connect_db(db_fi: str) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(db_fi)
    con.execute("install vss; load vss;")
    con.execute("SET hnsw_enable_experimental_persistence=true;")
    return con


def setup_db(db_fi: str, embedding_dim: int) -> None:
    con = connect_db(db_fi)
    con.execute(
        f"""
        CREATE TABLE IF NOT EXISTS embeddings (
            document_fi TEXT,
            chunk TEXT,
            vector FLOAT[{embedding_dim}],
            UNIQUE(document_fi, chunk)
        )
        """
    )
    con.execute("DROP INDEX IF EXISTS idx;")
    con.execute("CREATE INDEX idx ON embeddings USING HNSW (vector);")


def insert_chunks(
    db_fi: str,
    chunks: list[Chunk],
    embedding_model: str = defaults.embedding_model,
) -> None:
    con = connect_db(db_fi)

    to_insert: list = []
    for chunk in chunks[:10]:
        print(f"embedding {chunk}")
        to_insert.append(
            (
                str(chunk.file.path),
                chunk.chunk_content,
                str(
                    ollama.embeddings(
                        model=embedding_model, prompt=chunk.chunk_content
                    )["embedding"]
                ),
            )
        )

    con.executemany(
        """
        INSERT OR REPLACE INTO embeddings (document_fi, chunk, vector)
        VALUES (?, ?, ?);
        """,
        to_insert,
    )
    print(f"inserted {len(to_insert)} chunks")


__all__ = ["setup_db", "insert_chunks"]
