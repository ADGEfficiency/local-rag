import textwrap

import ollama


def get_topics(chunk: str, llm_model: str) -> str:
    ollama.pull(llm_model)
    topics = ollama.generate(
        model=llm_model,
        prompt=f"Plesae create a list of topics for this chunk for the purpose of improving retrival of the chunk.  Answer only with a list of topics and nothing else. <chunk>{chunk}</chunk>",
        options={"num_predict": 128},
    )["response"]
    return str(topics)


def get_chunk_context(fi_md: str, chunk_content: str, llm_model: str) -> str:
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
    return f"context: {chunk_context}"
