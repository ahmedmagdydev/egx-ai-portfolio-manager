from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import Settings
from ..models import Document, DocumentChunk
from ..repositories.documents import get_embedding_provider


class RagServiceError(Exception):
    pass


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    a_vals = [float(x) for x in a]
    b_vals = [float(x) for x in b]
    dot = sum(x * y for x, y in zip(a_vals, b_vals, strict=False))
    norm_a = sum(x * x for x in a_vals) ** 0.5
    norm_b = sum(x * x for x in b_vals) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def search_documents(
    session: Session,
    settings: Settings,
    query: str,
    *,
    symbol: str | None = None,
    document_type: str | None = None,
    language: str | None = None,
    as_of: datetime | None = None,
    top_k: int = 5,
) -> list[dict]:
    provider = get_embedding_provider(settings)
    query_embedding = provider.embed([query])[0]
    stmt = (
        select(DocumentChunk, Document)
        .join(Document, DocumentChunk.document_id == Document.id)
        .where(Document.status == "indexed")
    )
    if symbol is not None:
        stmt = stmt.where(Document.symbol == symbol.upper())
    if document_type is not None:
        stmt = stmt.where(Document.document_type == document_type)
    if language is not None:
        stmt = stmt.where(Document.language == language)
    if as_of is not None:
        stmt = stmt.where(
            (Document.published_at.is_(None)) | (Document.published_at <= as_of)
        )
    stmt = (
        stmt.order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
        .limit(top_k)
    )
    results = list(session.execute(stmt))
    output: list[dict] = []
    seen_chunks: set[str] = set()
    for chunk, document in results:
        key = f"{document.id}:{chunk.ordinal}"
        if key in seen_chunks:
            continue
        seen_chunks.add(key)
        output.append(
            {
                "chunk_id": str(chunk.id),
                "ordinal": chunk.ordinal,
                "content": chunk.content,
                "language": chunk.language,
                "section_title": chunk.section_title,
                "page_start": chunk.page_start,
                "page_end": chunk.page_end,
                "score": round(_cosine_similarity(chunk.embedding, query_embedding), 6),
                "document": {
                    "id": str(document.id),
                    "symbol": document.symbol,
                    "title": document.title,
                    "document_type": document.document_type,
                    "language": document.language,
                    "source": document.source,
                    "source_url": document.source_url,
                    "published_at": (
                        document.published_at.isoformat() if document.published_at else None
                    ),
                    "checksum": document.checksum,
                    "version": document.version,
                },
            }
        )
    return output
