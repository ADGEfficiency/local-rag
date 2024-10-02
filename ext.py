import re

import ollama


def get_topics(chunk: str, llm_model: str) -> str:
    ollama.pull(llm_model)
    topics = ollama.generate(
        model=llm_model,
        prompt=f"Task: Create a list of topics for this content. Expected Output: A list of less than five topics. The list should be pure json. Content: {chunk} ```json",
        options={"num_predict": 128},
    )["response"]
    match = re.search(r"\[(.*?)\]", topics)
    if match:
        return f"[{match.group(1)}]"
    return "[]"
