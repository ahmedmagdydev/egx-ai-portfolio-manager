from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    content: str
    token_count: int
    section_title: str | None
    page_start: int | None = None
    page_end: int | None = None


def chunk_text(
    text: str,
    *,
    chunk_size: int = 600,
    overlap: int = 120,
    page_start: int | None = None,
) -> list[Chunk]:
    """Split text into overlapping word-based chunks.

    A simple table heuristic keeps content with many pipe/tab delimiters intact.
    Token counts are approximate word counts because a local tokenizer is not
    bundled in this phase.
    """
    if not text.strip():
        return []

    heading = None
    first_line = next((line for line in text.splitlines() if line.strip()), "")
    if first_line.startswith("#"):
        heading = first_line.lstrip("#").strip()
        text = "\n".join(
            line for line in text.splitlines()
            if line.strip() != first_line.strip()
        )

    stripped = " ".join(text.split())
    if not stripped:
        return []

    if _looks_like_table(stripped):
        content = stripped
        if heading:
            content = f"{heading}\n\n{content}"
        return [
            Chunk(
                content=content,
                token_count=len(stripped.split()),
                section_title=heading,
                page_start=page_start,
                page_end=page_start,
            )
        ]

    words = stripped.split()
    if not words:
        return []

    step = max(1, chunk_size - overlap)
    chunks: list[Chunk] = []
    for i in range(0, len(words), step):
        chunk_words = words[i : i + chunk_size]
        content = " ".join(chunk_words)
        if heading:
            content = f"{heading}\n\n{content}"
        chunks.append(
            Chunk(
                content=content,
                token_count=len(chunk_words),
                section_title=heading,
                page_start=page_start,
                page_end=page_start,
            )
        )
        if i + chunk_size >= len(words):
            break
    return chunks


def _looks_like_table(text: str) -> bool:
    lines = text.splitlines()
    if not lines:
        return False
    pipe_rows = sum(1 for line in lines if line.count("|") >= 2)
    tab_rows = sum(1 for line in lines if "\t" in line)
    return (pipe_rows + tab_rows) / len(lines) >= 0.5
