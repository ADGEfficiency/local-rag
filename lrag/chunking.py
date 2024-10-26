import bs4
import mistune
from markdownify import markdownify

from lrag.config import defaults
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


def prepend_file_path_to_chunk(chunk: Chunk) -> None:
    chunk.chunk_content = f"file: {chunk.file.folder.name}/{chunk.file.path.relative_to(chunk.file.folder)}, chunk: {chunk.chunk_content}"


def prepend_context_to_chunk(
    chunk: Chunk,
    # fi_md: str,
    # chunk_content: str,
    # llm_model: str
) -> None:
    import textwrap

    import ollama

    fi_md = chunk.file.file_content
    chunk_content = chunk.raw_chunk_content
    llm_model = defaults.llm_model

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
    chunk_context = ollama.generate(model=llm_model, prompt=chunk_context_query)[
        "response"
    ]
    # TODO - capitalize the first letter of chunk_context
    chunk_context = chunk_context.replace("This chunk contains ", "")
    chunk.chunk_content = f"context: {chunk_context}, {chunk.chunk_content}"
