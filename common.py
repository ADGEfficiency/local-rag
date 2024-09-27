import dataclasses

import duckdb


@dataclasses.dataclass
class Defaults:
    embedding_model: str = "snowflake-arctic-embed:335m"
    embedding_dim: int = 1024
    llm_model: str = "llama3.1:8b"
    max_tokens: int = 3000
    temperature: float = 0.0


def connect_db(db_fi: str, embedding_dim: int) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(db_fi)
    con.execute("install vss; load vss;")
    con.execute("SET hnsw_enable_experimental_persistence=true;")
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
    return con


defaults = Defaults()

__all__ = ["connect_db", "defaults"]
