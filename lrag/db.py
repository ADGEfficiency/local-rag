import pathlib

import duckdb
import ollama
from loguru import logger
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


def get_previous_ingested_files(db_fi: str, reingest_files: bool) -> set[pathlib.Path]:
    if reingest_files is True:
        print(f"reingesting all files")
        return set()

    con = connect_db(db_fi)
    previously_ingested_files = set(
        [
            pathlib.Path(row[0])
            for row in con.execute(
                "SELECT distinct document_fi FROM embeddings"
            ).fetchall()
        ]
    )
    print(f"not reingesting {len(previously_ingested_files)} files")
    return previously_ingested_files


def insert_chunks(
    db_fi: str,
    chunks: list[Chunk],
    embedding_model: str = defaults.embedding_model,
) -> None:
    con = connect_db(db_fi)

    to_insert: list[tuple[str, str, str]] = []
    for chunk in chunks[:10]:
        logger.debug(f"embedding {chunk}")
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
