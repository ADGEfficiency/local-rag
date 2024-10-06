import pathlib

import click
import ollama
from rich import print

import core
import ext


def split_into_chunks(text: str, chunk_size: int, overlap: int) -> list[str]:
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunk = text[i : i + chunk_size]
        if len(chunk) > int(chunk_size * 0.1):
            chunks.append(chunk)
    return chunks


from better_chunking import split_into_chunks


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
    append_file_path: bool = True,
) -> None:
    print(embedding_model, embedding_dim)
    con = core.connect_db(db_fi, embedding_dim)
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

    folder = pathlib.Path(folder)
    assert folder.exists()
    n_chunks = 0
    for glob in globs:
        files = list(folder.rglob(glob))
        print(f"found {len(list(files))} files for {glob}")
        for n, fi in enumerate(files):
            print(f"{n=}, {fi=}")
            try:
                fi_md = fi.read_text()
            except UnicodeDecodeError:
                print(f"failed {n_chunks} chunks for {fi} {n}/{len(files)}")
                continue

            for chunk_n, chunk_content in enumerate(
                split_into_chunks(fi_md, chunk_size, int(overlap_pct * chunk_size))
            ):
                n_chunks += 1
                chunk = ""
                if append_file_path:
                    chunk += f"file: {folder.name}/{fi.relative_to(folder)}, "

                contextual_rag = True
                if contextual_rag:
                    import textwrap

                    chunk_context_query = textwrap.dedent(
                        f"""<document>
                        {fi_md}
                        </document>
                        Here is the chunk we want to situate within the whole document:
                        <chunk>
                        {chunk_content}
                        </chunk>
                        Please give a short succint context to situate this chunk within the overall document for the
                        purposes of improving search retreival of the chunk. Answer only with the succint contexnt
                        and nothing else. If there is any Python code in the block, explain what it does.
                        Begin your answer with `This chunk contains`. Your answer should contain `This chunk contains`.
                    """
                    )
                    ollama.pull(llm_model)
                    chunk_context = ollama.generate(
                        model=llm_model, prompt=chunk_context_query
                    )["response"]
                    # TODO - capitalize the first letter of chunk_context
                    chunk_context = chunk_context.replace("This chunk contains ", "")

                    chunk = f"context: {chunk_context}, {chunk}"

                    # TODO - could include the chunk number in the prompt?

                print(
                    f"[yellow]{chunk_n=}, {fi=}, [green]{chunk_content=}[/], [red]{chunk_context=}[/]\n"
                )

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
