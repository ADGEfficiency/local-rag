import lrag


def test_split_markdown_into_chunks() -> None:
    md = """
Some initial content

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

    chunks = lrag.chunking.split_markdown_into_chunks(md, 100, 0)
    assert len(chunks) == 5
