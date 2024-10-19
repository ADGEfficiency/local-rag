import pathlib

import typer
from typing_extensions import Annotated

import lrag
from lrag.config import ChunkExtensions, ChunkStrategies, LogLevel, defaults
from lrag.models import Chunk, File

cli = typer.Typer(rich_markup_mode=None)


def get_file_content(fi: pathlib.Path) -> str | None:
    try:
        return fi.read_text()
    except UnicodeDecodeError:
        return None


def get_content_from_files(
    folders: list[pathlib.Path],
    globs: list[str],
    previously_ingested_files: set[pathlib.Path] | None = None,
) -> list[File]:
    fis: list[File] = []
    for glob in globs:
        for folder in folders:
            fi_paths = set(folder.rglob(glob))

            if previously_ingested_files is not None:
                ignored_fis = fi_paths.intersection(previously_ingested_files)
                fi_paths = fi_paths.difference(previously_ingested_files)
                if ignored_fis:
                    print(f"ignoring {ignored_fis}")

            for fi_path in fi_paths:
                content = get_file_content(fi_path)
                if content is not None:
                    fis.append(File(folder=folder, path=fi_path, file_content=content))

            print(
                f"found {len(list(fis))} files for {glob}, {len(fis)} files processed"
            )
    return fis


def create_chunks_from_file_contents(
    fis: list[File],
    chunk_strategy: str,
    chunk_size: int,
    overlap_pct: float,
) -> list[Chunk]:
    chunk_strategy_dispatch = {
        "characters": lrag.chunking.chunk_text_by_character,
        # TODO - "markdown-objects": None,
    }

    chunks: list[Chunk] = []
    for fi in fis:
        chunk_strategy_fn = chunk_strategy_dispatch[chunk_strategy]
        chunks.extend(chunk_strategy_fn(fi, chunk_size, overlap_pct))
    print(f"created {len(chunks)} chunks from {len(fis)} files using {chunk_strategy=}")
    return chunks


def append_chunk_extensions(
    chunks: list[Chunk],
    chunk_extensions: tuple[ChunkExtensions, ...],
) -> None:
    chunk_extensions_dispatch = {
        "file_path": lrag.chunking.prepend_file_path_to_chunk,
        # TODO - contextual rag
        # TODO - inject topics
    }

    for chunk_extension in chunk_extensions:
        chunk_extension_fn = chunk_extensions_dispatch[chunk_extension]
        for chunk in chunks:
            chunk_extension_fn(chunk)
        print(f"ran {chunk_extension} on {len(chunks)} chunks")


@cli.command()
def ingest(
    folders: Annotated[
        list[pathlib.Path],
        typer.Argument(
            exists=True,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
            help="Folders to process. Multiple folders can be specified.",
        ),
    ],
    log_level: Annotated[LogLevel, typer.Option()] = LogLevel.INFO,
    globs: Annotated[
        list[str],
        typer.Option(
            "--glob",
            help="File extension(s) to include. Can supply multiple values.",
        ),
    ] = [
        "*.md",
    ],
    db_fi: Annotated[
        str, typer.Option("--db", help="DuckDB database file.")
    ] = defaults.db_fi,
    embedding_model: Annotated[
        str,
        typer.Option(
            "--embedding",
            help="Model to embed the query. Should be the same model as used to embed the query.",
        ),
    ] = defaults.embedding_model,
    reingest_files: Annotated[
        bool, typer.Option(help="Whether to reingest files.")
    ] = True,
    chunk_strategy: Annotated[
        ChunkStrategies, typer.Option(help="Strategy for chunking the text.")
    ] = defaults.chunk_strategy,
    chunk_size: Annotated[
        int, typer.Option(help="Size of the chunks to embed.")
    ] = 4000,
    overlap_pct: Annotated[
        float, typer.Option("--overlap", help="Percentage overlap between chunks.")
    ] = 0.15,
    chunk_extensions: Annotated[
        tuple[ChunkExtensions] | None,
        typer.Option(
            help="Extensions for chunking",
            callback=lambda v: tuple(v) if v is not None else (),
        ),
    ] = None,
) -> None:
    # setup logging
    lrag.logger.setup_logging(log_level.value)

    # setup the duckdb database
    lrag.db.setup_db(db_fi, embedding_model)

    # gather content from files
    fis = get_content_from_files(
        folders,
        globs,
        previously_ingested_files=lrag.db.get_previous_ingested_files(
            db_fi, reingest_files
        ),
    )

    # create chunks from file content
    chunks = create_chunks_from_file_contents(
        fis, chunk_strategy, chunk_size, overlap_pct
    )

    # add extensions to chunks - context, file path etc
    assert chunk_extensions is not None
    append_chunk_extensions(chunks, chunk_extensions)

    # insert into database
    lrag.db.insert_chunks(db_fi, chunks, embedding_model)
