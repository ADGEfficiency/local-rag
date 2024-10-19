import pathlib
import typing

import click

import lrag
from lrag.config import ChunkExtensions, ChunkStrategies, defaults
from lrag.models import Chunk, File


def get_file_content(fi: pathlib.Path) -> str | None:
    try:
        return fi.read_text()
    except UnicodeDecodeError:
        return None


def get_content_from_files(
    folders: list[pathlib.Path],
    globs: tuple[str],
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
        # "markdown-objects": None,
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
    }

    for chunk_extension in chunk_extensions:
        chunk_extension_fn = chunk_extensions_dispatch[chunk_extension]
        for chunk in chunks:
            chunk_extension_fn(chunk)
        print(f"ran {chunk_extension} on {len(chunks)} chunks")


@click.command()
@click.argument(
    "folders",
    type=click.Path(exists=True),
    nargs=-1,
    required=True,
    callback=lambda ctx, param, value: (pathlib.Path(p) for p in value),
    # help="TODO - multiple values",
)
@click.option(
    "--log-level",
    default="INFO",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
)
@click.option(
    "--glob",
    "globs",
    type=str,
    multiple=True,
    default=["*.md"],
    help='File extension(s) to include. Should be quoted to avoid shell expansion of the wildcard.  Can supply multiple values with `--glob "*.md" --glob "*.txt"`.',
)
@click.option(
    "--db",
    "db_fi",
    type=str,
    default="db.duckdb",
    help="DuckDB database file.",
)
@click.option(
    "--embedding-model",
    default=defaults.embedding_model,
    type=str,
    help="Model to embed the query.  Should be the same model as used to embed the query.",
)
@click.option("--reingest-files/--no-reingest-files", type=bool, default=True)
@click.option(
    "--chunk-strategy",
    type=click.Choice(typing.get_args(ChunkStrategies)),
    default=defaults.chunk_strategy,
    help="TODO",
)
@click.option(
    "--chunk-size", default=4000, type=int, help="Size of the chunks to embed."
)
@click.option(
    "--overlap",
    "overlap_pct",
    default=0.15,
    type=float,
    help="Percentage overlap between chunks.",
)
@click.option(
    "--chunk-extension",
    "chunk_extensions",
    type=click.Choice(typing.get_args(ChunkExtensions)),
    default=defaults.chunk_extensions,
    multiple=True,
    help="TODO",
)
def ingest(
    folders: list[pathlib.Path],
    log_level: str,
    globs: tuple[str],
    db_fi: str,
    embedding_model: str,
    reingest_files: bool,
    chunk_strategy: ChunkStrategies,
    chunk_size: int,
    overlap_pct: float,
    chunk_extensions: tuple[ChunkExtensions, ...],
) -> None:
    # setup logging
    lrag.logger.setup_logging(log_level)

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
    append_chunk_extensions(chunks, chunk_extensions)

    # insert into database
    lrag.db.insert_chunks(db_fi, chunks, embedding_model)
