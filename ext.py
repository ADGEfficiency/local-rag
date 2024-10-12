import re

import ollama


def get_topics(chunk: str, llm_model: str) -> str:
    ollama.pull(llm_model)
    topics = ollama.generate(
        model=llm_model,
        prompt=f"Plesae create a list of topics for this chunk for the purpose of improving retrival of the chunk.  Answer only with a list of topics and nothing else. <chunk>{chunk}</chunk>",
        options={"num_predict": 128},
    )["response"]
    return str(topics)
