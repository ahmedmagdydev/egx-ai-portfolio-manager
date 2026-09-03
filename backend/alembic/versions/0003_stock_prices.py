"""Create stock_prices table for OHLCV history.

Revision ID: 0003_stock_prices
Revises: 0002_portfolio_core
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_stock_prices"
down_revision: str | None = "0002_portfolio_core"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "stock_prices",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("stock_id", sa.UUID(), nullable=False),
        sa.Column("timestamp", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("open", sa.Numeric(20, 4), nullable=False),
        sa.Column("high", sa.Numeric(20, 4), nullable=False),
        sa.Column("low", sa.Numeric(20, 4), nullable=False),
        sa.Column("close", sa.Numeric(20, 4), nullable=False),
        sa.Column("volume", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="EGP", nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("source_url", sa.String(), nullable=True),
        sa.Column("fetched_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["stock_id"], ["stocks.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stock_id", "source", "timestamp"),
    )


def downgrade() -> None:
    op.drop_table("stock_prices")
