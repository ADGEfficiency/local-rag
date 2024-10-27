import textwrap

import ollama

from lrag.config import defaults
from lrag.models import Chunk


def prepend_file_path_to_chunk(chunk: Chunk) -> None:
    chunk.chunk_content = f"file: {chunk.file.folder.name}/{chunk.file.path.relative_to(chunk.file.folder)}, chunk: {chunk.chunk_content}"


def prepend_context_to_chunk(
    chunk: Chunk,
) -> None:
    chunk_content = chunk.raw_chunk_content
    llm_model = defaults.llm_model
    chunk_context_query = textwrap.dedent(
        f"""<document>
        {chunk.file.file_content}
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
    chunk_context = chunk_context.replace("This chunk contains ", "")
    chunk.chunk_content = f"context: {chunk_context}, {chunk.chunk_content}"


def prepend_queries_to_chunk(chunk: Chunk) -> None:
    chunk_context_query = textwrap.dedent(
        f"""
        Please write 5 RAG queries that would be used to find this a chunk in a document.
        <document>
        {chunk.file.file_content}
        </document>
        <chunk>
        {chunk.chunk_content}
        </chunk>
    """
    )
    ollama.pull(defaults.llm_model)
    queries = ollama.generate(model=defaults.llm_model, prompt=chunk_context_query)[
        "response"
    ]
    chunk.chunk_content = f"queries: {queries}, {chunk.chunk_content}"
