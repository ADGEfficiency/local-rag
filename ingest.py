import pathlib

import click
import duckdb
import ollama


def split_into_chunks(text: str, chunk_size: int, overlap: int) -> list[str]:
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunk = text[i : i + chunk_size]
        if len(chunk) > 0:
            chunks.append(chunk)
    return chunks


def process_files(
    folder: str,
    chunk_size: int,
    overlap: int,
    db_fi: str,
    globs: list[str],
    embedding_model: str,
    embedding_dim: int,
) -> None:
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

    folder_path = pathlib.Path(folder)
    assert folder_path.exists()
    n_chunks = 0
    for glob in globs:
        files = list(folder_path.rglob(glob))
        print(f"found {len(list(files))} files for {glob}")
        for n, fi in enumerate(files):
            fi_md = fi.read_text()
            chunks = split_into_chunks(fi_md, chunk_size, overlap)
            for chunk in chunks:
                n_chunks += 1
                res = ollama.embeddings(
                    model=embedding_model,
                    prompt=chunk,
                )
                embedding = res["embedding"]
                con.execute(
                    """
                    INSERT OR REPLACE INTO embeddings (document_fi, chunk, vector)
                    VALUES (?, ?, ?);
                    """,
                    (str(fi), chunk, embedding),
                )
            print(f"created {n_chunks} chunks for {fi} {n}/{len(files)}")
    con.close()


@click.command()
@click.argument("folder", type=click.Path(exists=True))
@click.option("--chunk-size", default=512, type=int)
@click.option("--overlap", default=102, type=int)
@click.option("--db", default="db.duckdb", type=click.Path(exists=True))
@click.option(
    "--glob",
    multiple=True,
    default=["*.md"],
    help='File extensions to include. Should be quoted to avoid shell expansion of the wildcard.  Usage `--glob "*.md" --glob "*.txt"`.',
)
@click.option("--embedding-model", default="mxbai-embed-large", type=str)
@click.option("--embedding-dim", default=1024, type=int)
def main(
    folder: str,
    chunk_size: int,
    overlap: int,
    db: str,
    glob: list[str],
    embedding_model: str,
    embedding_dim: int,
) -> None:
    process_files(folder, chunk_size, overlap, db, glob, embedding_model, embedding_dim)


if __name__ == "__main__":
    main()
