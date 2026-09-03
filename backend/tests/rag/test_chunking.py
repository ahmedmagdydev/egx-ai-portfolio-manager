from app.rag.chunking import chunk_text


def test_chunk_text_splits_short_text() -> None:
    chunks = chunk_text("word " * 50, chunk_size=20, overlap=5)
    assert len(chunks) > 1
    assert all(chunk.token_count <= 20 for chunk in chunks)


def test_chunk_text_preserves_heading() -> None:
    text = "# Executive Summary\n" + "word " * 30
    chunks = chunk_text(text, chunk_size=20, overlap=5)
    assert chunks[0].section_title == "Executive Summary"
    assert "Executive Summary" in chunks[0].content


def test_chunk_text_keeps_table_atomic() -> None:
    text = "| A | B |\n| 1 | 2 |\n| 3 | 4 |"
    chunks = chunk_text(text, chunk_size=5, overlap=1)
    assert len(chunks) == 1


def test_chunk_text_empty() -> None:
    assert chunk_text("") == []
    assert chunk_text("   ") == []
