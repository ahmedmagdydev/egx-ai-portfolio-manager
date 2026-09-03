from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import Settings
from ..models import Document, DocumentChunk, Stock
from ..providers.embeddings import FakeEmbeddingProvider
from ..providers.embeddings.ollama import OllamaEmbeddingProvider
from ..rag.chunking import chunk_text


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def get_embedding_provider(settings: Settings):
    if settings.embedding_provider == "ollama":
        return OllamaEmbeddingProvider(settings)
    return FakeEmbeddingProvider(settings.embedding_dimension)


def create_document(
    session: Session,
    settings: Settings,
    *,
    symbol: str | None,
    document_type: str,
    title: str,
    language: str,
    content: str,
    source: str,
    source_url: str | None,
    published_at: datetime | None,
    mime_type: str = "text/plain",
    extraction_metadata: dict | None = None,
) -> Document:
    content_bytes = content.encode("utf-8")
    checksum = _sha256(content_bytes)
    fetched_at = datetime.now(UTC)
    stock = None
    if symbol is not None:
        stock = session.scalar(select(Stock).where(Stock.symbol == symbol.upper()))
    document = Document(
        stock_id=stock.id if stock else None,
        symbol=symbol.upper() if symbol else None,
        document_type=document_type,
        title=title,
        language=language,
        content=content,
        mime_type=mime_type,
        checksum=checksum,
        source=source,
        source_url=source_url,
        published_at=published_at,
        fetched_at=fetched_at,
        status="processing",
        version=0,
        extraction_metadata=extraction_metadata,
    )
    session.add(document)
    session.flush()

    chunks = chunk_text(content)
    if not chunks:
        document.status = "indexed"
        return document

    provider = get_embedding_provider(settings)
    embeddings = provider.embed([chunk.content for chunk in chunks])
    for ordinal, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=False)):
        chunk_checksum = _sha256(chunk.content.encode("utf-8"))
        session.add(
            DocumentChunk(
                document_id=document.id,
                ordinal=ordinal,
                content=chunk.content,
                language=language,
                token_count=chunk.token_count,
                page_start=chunk.page_start,
                page_end=chunk.page_end,
                section_title=chunk.section_title,
                checksum=chunk_checksum,
                embedding=embedding,
                embedding_model=settings.ollama_embedding_model
                if settings.embedding_provider == "ollama"
                else "fake",
                embedding_dimension=settings.embedding_dimension,
            )
        )
    document.status = "indexed"
    session.commit()
    return document


def get_document(session: Session, document_id: str) -> Document | None:
    return session.get(Document, document_id)


def get_documents(
    session: Session,
    *,
    symbol: str | None = None,
    document_type: str | None = None,
    language: str | None = None,
    as_of: datetime | None = None,
) -> list[Document]:
    stmt = select(Document).where(Document.status == "indexed")
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
    return list(session.scalars(stmt).all())
