from lrag.models import Chunk, File


def chunk_text_by_character(
    fi: File, chunk_size: int, overlap_pct: float
) -> list[Chunk]:
    overlap = int(chunk_size * overlap_pct)

    chunks = []
    for i in range(0, len(fi.file_content), chunk_size - overlap):
        content = fi.file_content[i : i + chunk_size]
        if len(content) > int(chunk_size * 0.1):
            chunks.append(
                Chunk(
                    file=fi,
                    chunk_content=content,
                    raw_chunk_content=content,
                )
            )
    return chunks


def prepend_file_path_to_chunk(chunk: Chunk) -> None:
    chunk.chunk_content = f"file: {chunk.file.folder.name}/{chunk.file.path.relative_to(chunk.file.folder)}, chunk: {chunk.chunk_content}"
