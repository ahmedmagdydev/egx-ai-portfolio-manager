from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from pgvector.sqlalchemy import Vector  # type: ignore[import-untyped]
from sqlalchemy import JSON, TIMESTAMP, BigInteger, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .portfolio import Stock

EMBEDDING_DIMENSION = 2560


class Document(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "documents"

    stock_id: Mapped[str | None] = mapped_column(ForeignKey("stocks.id"), nullable=True)
    symbol: Mapped[str | None] = mapped_column(String(20), nullable=True)
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    language: Mapped[str] = mapped_column(String(10), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    raw_path: Mapped[str | None] = mapped_column(String, nullable=True)
    mime_type: Mapped[str] = mapped_column(String, default="text/plain", nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)
    source_url: Mapped[str | None] = mapped_column(String, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    version: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    extraction_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    stock: Mapped[Stock | None] = relationship(back_populates="documents")
    chunks: Mapped[list[DocumentChunk]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class DocumentChunk(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "document_chunks"
    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "ordinal",
            name="uq_document_chunks_document_ordinal",
        ),
    )

    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), nullable=False)
    ordinal: Mapped[int] = mapped_column(BigInteger, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(10), nullable=False)
    token_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    page_start: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    page_end: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    section_title: Mapped[str | None] = mapped_column(String, nullable=True)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIMENSION), nullable=False)
    embedding_model: Mapped[str] = mapped_column(String, nullable=False)
    embedding_dimension: Mapped[int] = mapped_column(BigInteger, nullable=False)

    document: Mapped[Document] = relationship(back_populates="chunks")
