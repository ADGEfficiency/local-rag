import pathlib
import typing

import click
import core
import duckdb
import ollama
from rich import print

from chunking import get_chunk_context
from markdown_chunking import split_into_chunks as chunk_markdown


def split_into_chunks(text: str, chunk_size: int, overlap: int) -> list[str]:
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunk = text[i : i + chunk_size]
        if len(chunk) > int(chunk_size * 0.1):
            chunks.append(chunk)
    return chunks


def is_document_in_db(con: duckdb.DuckDBPyConnection, document_fi: str) -> bool:
    result = con.execute(
        "SELECT COUNT(*) FROM embeddings WHERE document_fi = ?", (document_fi,)
    ).fetchone()
    assert result is not None
    return bool(result[0] > 0)


def get_file_content(fi: pathlib.Path) -> str | None:
    try:
        return fi.read_text()
    except UnicodeDecodeError:
        return None


def process_files(
    folder: str | pathlib.Path,
    chunk_size: int,
    overlap_pct: float,
    db_fi: str,
    globs: list[str],
    embedding_model: str,
    embedding_dim: int,
    llm_model: str,
    # TODO - needs a rethink - how to make extensible?
    chunk_fn: typing.Literal[
        "split_into_chunks", "chunk_markdown"
    ] = "split_into_chunks",
    skip_ingested_files: bool = True,
    append_file_path: bool = False,
    contextual_rag: bool = False,
) -> None:
    print(embedding_model, embedding_dim)

    folder = pathlib.Path(folder)
    assert folder.exists()
    n_chunks = 0
    for glob in globs:
        files = list(folder.rglob(glob))
        print(f"found {len(list(files))} files for {glob}")
        for n, fi in enumerate(files):
            if skip_ingested_files and is_document_in_db(con, str(fi)):
                print(f"skipping {fi} as already processed {n}/{len(files)}")
                continue

            print(f"{n=}, {fi=}")

            fi_md = get_file_content(fi)

            if not fi_md:
                print(f"failed {n_chunks} chunks for {fi} {n}/{len(files)}")
                continue

            chunker = split_into_chunks
            if chunk_fn == "chunk_markdown":
                chunker = chunk_markdown

            for chunk_n, chunk_content in enumerate(
                chunker(fi_md, chunk_size, int(overlap_pct * chunk_size))
            ):
                n_chunks += 1
                chunk = ""
                chunk_log = f"[yellow]{chunk_n=}, {fi=}[/], [green]{chunk_content=}[/]"

                if append_file_path:
                    chunk += f"file: {folder.name}/{fi.relative_to(folder)}, "

                if contextual_rag:
                    chunk_context = get_chunk_context(fi_md, chunk_content, llm_model)
                    chunk = chunk_context + ", " + chunk
                    chunk_log += f", [red]{chunk_context=}[/]\n"

                print(chunk_log)
                chunk += f" chunk: {chunk_content}"

                con.execute(
                    """
                    INSERT OR REPLACE INTO embeddings (document_fi, chunk, vector)
                    VALUES (?, ?, ?);
                    """,
                    (
                        str(fi),
                        chunk,
                        ollama.embeddings(model=embedding_model, prompt=chunk)[
                            "embedding"
                        ],
                    ),
                )
            print(f"created {n_chunks} chunks before {fi} {n}/{len(files)}")

    con.close()


@click.command()
@click.argument(
    "folders",
    type=click.Path(exists=True),
    nargs=-1,
)
@click.option(
    "--chunk-size", default=4000, type=int, help="Size of the chunks to embed."
)
@click.option(
    "--overlap", default=0.15, type=float, help="Percentage overlap between chunks."
)
@click.option(
    "--db",
    default="db.duckdb",
    help="DuckDB database file.",
)
@click.option(
    "--glob",
    multiple=True,
    default=["*.md"],
    help='File extension(s) to include. Should be quoted to avoid shell expansion of the wildcard.  Usage `--glob "*.md" --glob "*.txt"`.',
)
@click.option(
    "--embedding-model",
    default=core.defaults.embedding_model,
    type=str,
    help="Model to embed the query.  Should be the same model as used to embed the query.",
)
@click.option(
    "--embedding-dim",
    default=1024,
    type=int,
    help="Dimension of the embeddings.  Should match the embedding model.",
)
@click.option(
    "--llm",
    default=core.defaults.llm_model,
    type=str,
    help="The LLM model. Only used for propsitional chunking of topics.",
)
def main(
    folders: str,
    chunk_size: int,
    overlap: float,
    db: str,
    glob: list[str],
    embedding_model: str,
    embedding_dim: int,
    llm: str,
) -> None:
    ollama.pull(embedding_model)
    for folder in folders:
        process_files(
            folder, chunk_size, overlap, db, glob, embedding_model, embedding_dim, llm
        )


if __name__ == "__main__":
    main()
