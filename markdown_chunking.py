import bs4
import mistune

test_markdown = """
# Introduction
This is the introduction section with some details.

## Background
Background information goes here.

```python
def func():
    pass
```

### Detailed Explanation
More detailed explanation with subpoints.

# Conclusion
Final thoughts and conclusion.
"""

markdown_parser = mistune.create_markdown()
from markdownify import markdownify


def split_into_chunks(text: str, chunk_size: int, overlap: int = 1) -> list[str]:
    soup = bs4.BeautifulSoup(str(markdown_parser(text)), "html.parser")

    paragraphs: list[list[str]] = [[]]

    for element in soup.find_all():
        if element.name in ["h1", "h2", "h3"]:
            paragraphs.append([])

        paragraphs[-1].append(markdownify(str(element)))

    paragraphs = [p for p in paragraphs if len(p) > 0]
    chunks = []
    for n, p in enumerate(paragraphs):
        chunk = []
        if overlap:
            if n > 0:
                # here we only include the last html element from the previous paragraph
                # we do not include the entire last paragraph
                chunk.append("".join(paragraphs[n - 1][-1:]))

            chunk.append("".join(p))

            if n < len(paragraphs) - 1:
                # here we only include the first html element from the next paragraph
                # we do not include the entire next paragraph
                chunk.append("".join(paragraphs[n + 1][:1]))

        chunks.append("".join(chunk))

    """
    refactor

    rewrite into a more general chunking process
    - split into units (str -> characters: list[str], str -> markdown_elements: list[str])
    - for unit in units

    extend
    - could iterate over overlap to find a number of chunks that gives text closest matching an integer for len(chunk:str)


    test
    - num chunks
    - where / what overlap should be
    """
    return chunks


chunks = split_into_chunks(test_markdown, None, 1)
for chunk in chunks:
    print(chunk)
    print("")
