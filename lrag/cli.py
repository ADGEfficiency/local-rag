import pathlib

import lrag
from lrag.models import Chunk, File


def get_file_content(fi: pathlib.Path) -> str | None:
    try:
        return fi.read_text()
    except UnicodeDecodeError:
        return None


def gather_content_from_files(
    folder: pathlib.Path,
    globs: list[str],
    previously_ingested_files: set[pathlib.Path] | None = None,
) -> list[File]:
    fis: list[File] = []
    for glob in globs:
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

        print(f"found {len(list(fis))} files for {glob}, {len(fis)} files processed")
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


def ingest() -> None:
    # CLI arguments
    db_fi = "temp.db"
    embedding_dim = 1024
    folder = pathlib.Path.home() / ("programming-resources")
    globs = ["*.md", "*.py"]
    chunk_strategy = "characters"
    chunk_size = 2000
    overlap = 0.1
    chunk_extensions = ["file_path"]

    # setup the duckdb database
    lrag.db.setup_db(db_fi, embedding_dim)

    # gather content from files
    fis = gather_content_from_files(
        folder,
        globs,
        previously_ingested_files={
            pathlib.Path(
                "/Users/adamgreen/programming-resources/bash-and-unix/useful-tools.md"
            )
        },
    )

    # create chunks from file content
    chunks = create_chunks_from_file_contents(fis, chunk_strategy, chunk_size, overlap)

    def append_chunk_extensions(
        chunks: list[Chunk], chunk_extensions: list[str], **kwargs
    ) -> list[Chunk]:
        chunk_extensions_dispatch = {
            "file_path": lrag.chunking.prepend_file_path_to_chunk,
        }

        for chunk_extension in chunk_extensions:
            chunk_extension_fn = chunk_extensions_dispatch[chunk_extension]
            for chunk in chunks:
                chunk = chunk_extension_fn(chunk)

    # add extensions to chunks - context, file path etc
    append_chunk_extensions(chunks, chunk_extensions)

    # # insert into database
    lrag.db.insert_chunks(db_fi, chunks)
