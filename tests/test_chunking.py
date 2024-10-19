import lrag


def test_split_markdown_into_chunks() -> None:
    md = """
Initial content

# First Header

First paragraph, first sentence.

First paragraph, second sentence.

# Second Header

Second paragraph, first sentence.

Second paragraph, second sentence.

# Third Header

Third paragraph, first sentence.

Third paragraph, second sentence.
    """

    # test when we don't want to include any elements from previous paragraphs
    chunks = lrag.chunking.chunk_markdown_by_markdown_object(
        md, n_elements_window=0, n_paragraph_window=0
    )
    assert len(chunks) == 4

    assert "Initial content" in chunks[0]
    assert "First Header" not in chunks[0]

    assert "Initial content" not in chunks[1]
    assert "First Header" in chunks[1]
    assert "Second Header" not in chunks[1]

    assert "First paragraph, first sentence." not in chunks[2]
    assert "Second Header" in chunks[2]
    assert "Third Header" not in chunks[2]

    assert "Second Header" not in chunks[3]
    assert "Third Header" in chunks[3]

    # assert "First paragraph, first sentence." not in chunks[0]
    # assert "Second paragraph, first sentence." not in chunks[1]
    # assert "Initial content" not in chunks[1]
    # print(chunks[1])
    # print("BREAK")

    # chunks = lrag.chunking.chunk_markdown_by_markdown_object(md, n_elements_window=2)
    # assert len(chunks) == 4
    # assert "First paragraph, first sentence." in chunks[0]
    # assert "Second paragraph, first sentence." in chunks[1]
    # print(chunks[1])
