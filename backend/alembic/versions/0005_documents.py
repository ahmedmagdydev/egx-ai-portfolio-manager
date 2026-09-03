"""Create documents and document_chunks tables.

Revision ID: 0005_documents
Revises: 0004_financial_statements
"""
from collections.abc import Sequence

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from alembic import op

revision: str = "0005_documents"
down_revision: str | None = "0004_financial_statements"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "documents",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("stock_id", sa.UUID(), nullable=True),
        sa.Column("symbol", sa.String(length=20), nullable=True),
        sa.Column("document_type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("language", sa.String(length=10), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("raw_path", sa.String(), nullable=True),
        sa.Column("mime_type", sa.String(), server_default="text/plain", nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("source_url", sa.String(), nullable=True),
        sa.Column("published_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("fetched_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("version", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("extraction_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["stock_id"], ["stocks.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "document_chunks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("document_id", sa.UUID(), nullable=False),
        sa.Column("ordinal", sa.BigInteger(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("language", sa.String(length=10), nullable=False),
        sa.Column("token_count", sa.BigInteger(), nullable=True),
        sa.Column("page_start", sa.BigInteger(), nullable=True),
        sa.Column("page_end", sa.BigInteger(), nullable=True),
        sa.Column("section_title", sa.String(), nullable=True),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("embedding", Vector(2560), nullable=False),
        sa.Column("embedding_model", sa.String(), nullable=False),
        sa.Column("embedding_dimension", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "document_id",
            "ordinal",
            name="uq_document_chunks_document_ordinal",
        ),
    )


def downgrade() -> None:
    op.drop_table("document_chunks")
    op.drop_table("documents")
