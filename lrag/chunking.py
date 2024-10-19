import bs4
import mistune
from markdownify import markdownify

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
                    chunk_content=f"chunk: {content}",
                    raw_chunk_content=content,
                )
            )
    return chunks


def prepend_file_path_to_chunk(chunk: Chunk) -> None:
    chunk.chunk_content = f"file: {chunk.file.folder.name}/{chunk.file.path.relative_to(chunk.file.folder)}, chunk: {chunk.chunk_content}"


def chunk_markdown_by_markdown_object(
    text: str, n_elements_window: int = 1, n_paragraph_window: int = 1
) -> list[str]:
    markdown_parser = mistune.create_markdown()

    # first parse the markdown text into html
    html = str(markdown_parser(text))

    # then extract the headers that separate paragraphs
    html_parser = bs4.BeautifulSoup(html, "html.parser")
    paragraphs: list[list[str]] = [[]]
    for element in html_parser.find_all():
        if element.name in ["h1", "h2", "h3"]:
            paragraphs.append([])
        paragraphs[-1].append(markdownify(str(element)))

    # remove empty paragraphs
    paragraphs = [p for p in paragraphs if len(p) > 0]

    chunks = []
    for n, p in enumerate(paragraphs):
        chunk = []
        if n > 0:
            # here we only include the last html element from the previous paragraph
            # we do not include the entire last paragraph
            chunk.append(
                "".join(paragraphs[n - n_paragraph_window][-n_elements_window:])
            )

        chunk.append("".join(p))

        if n < len(paragraphs) - 1:
            # here we only include the first html element from the next paragraph
            # we do not include the entire next paragraph
            chunk.append(
                "".join(paragraphs[n + n_paragraph_window][:n_elements_window])
            )

        chunks.append("".join(chunk))

    # TODO - remove small chunks based on size?

    return chunks
