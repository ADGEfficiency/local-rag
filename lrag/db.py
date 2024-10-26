import pathlib

import duckdb
import ollama
from loguru import logger
from rich import print

from lrag.models import Chunk


def connect_db(db_fi: str) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(db_fi)
    con.execute("install vss; load vss;")
    con.execute("SET hnsw_enable_experimental_persistence=true;")
    return con


def setup_db(db_fi: str, embedding_model: str) -> None:
    ollama.pull(embedding_model)
    embedding_dim = len(
        ollama.embeddings(model=embedding_model, prompt="a")["embedding"]
    )

    con = connect_db(db_fi)
    con.execute(
        f"""
        CREATE SEQUENCE IF NOT EXISTS seq_document_id START 1;
        CREATE TABLE IF NOT EXISTS embeddings (
            document_id INTEGER PRIMARY KEY DEFAULT nextval('seq_document_id'),
            document_fi TEXT,
            chunk TEXT,
            vector FLOAT[{embedding_dim}],
            embedding_model TEXT,
            UNIQUE(document_fi, chunk)
        )
        """
    )
    con.execute("DROP INDEX IF EXISTS hnsw;")
    con.execute("CREATE INDEX hnsw ON embeddings USING HNSW (vector);")


def get_previous_ingested_files(db_fi: str, reingest_files: bool) -> set[pathlib.Path]:
    if reingest_files is True:
        print("reingesting all files")
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


def insert_chunks(db_fi: str, chunks: list[Chunk], embedding_model: str) -> None:
    con = connect_db(db_fi)
    ollama.pull(embedding_model)
    to_delete: list[tuple[str, str]] = []
    to_insert: list[tuple[str, str, str, str]] = []
    for chunk in chunks:
        logger.debug(f"embedding {chunk}")
        to_delete.append((str(chunk.file.path), chunk.chunk_content))
        to_insert.append(
            (
                str(chunk.file.path),
                chunk.chunk_content,
                str(
                    ollama.embeddings(
                        model=embedding_model, prompt=chunk.chunk_content
                    )["embedding"]
                ),
                embedding_model,
            )
        )

    if len(to_insert) == 0:
        print("no chunks to insert")
        return

    # can't do with an ON CONFLICT UPDATE, as vector is used in an index
    # you drop HNSW index and re-create, but then you can't update the vector
    # a DELETE and INSERT will mean that documents being reingested will end up with
    # a different `document_id`, even if the vector chunk is not being changed
    # the implementation below will ignore chunks that already exist - if you reingested with a different
    # embedding model, you would get different embeddings in one database
    con.executemany(
        """
            INSERT INTO embeddings (document_fi, chunk, vector, embedding_model)
            VALUES (?, ?, ?, ?)
            ON CONFLICT DO NOTHING;
            """,
        to_insert,
    )
    print(f"inserted {len(to_insert)} chunks")


__all__ = ["setup_db", "insert_chunks"]
