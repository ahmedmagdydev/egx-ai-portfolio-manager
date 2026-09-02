"""Create deterministic portfolio core tables.

Revision ID: 0002_portfolio_core
Revises: 0001_enable_pgvector
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0002_portfolio_core"
down_revision: str | None = "0001_enable_pgvector"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    transaction_type = postgresql.ENUM(
        "BUY", "SELL", "DEPOSIT", "WITHDRAWAL", "DIVIDEND",
        name="transaction_type",
        create_type=False,
    )
    freshness = postgresql.ENUM(
        "fresh", "stale", "unavailable", name="freshness", create_type=False
    )
    transaction_type.create(bind, checkfirst=True)
    freshness.create(bind, checkfirst=True)

    op.create_table(
        "stocks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("symbol", sa.String(), nullable=False),
        sa.Column("name_en", sa.String(), nullable=False),
        sa.Column("name_ar", sa.String(), nullable=True),
        sa.Column("sector", sa.String(), nullable=True),
        sa.Column("currency", sa.String(length=3), server_default="EGP", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("symbol"),
    )
    op.create_table(
        "transactions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("stock_id", sa.UUID(), nullable=True),
        sa.Column("type", transaction_type, nullable=False),
        sa.Column("quantity", sa.Numeric(20, 4), nullable=True),
        sa.Column("price", sa.Numeric(20, 4), nullable=True),
        sa.Column("fees", sa.Numeric(20, 2), server_default="0", nullable=False),
        sa.Column("amount", sa.Numeric(20, 2), nullable=True),
        sa.Column("executed_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("sequence", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.CheckConstraint(
            "quantity IS NULL OR quantity > 0",
            name="ck_transactions_quantity_positive",
        ),
        sa.CheckConstraint("price IS NULL OR price >= 0", name="ck_transactions_price_nonnegative"),
        sa.CheckConstraint("fees >= 0", name="ck_transactions_fees_nonnegative"),
        sa.ForeignKeyConstraint(["stock_id"], ["stocks.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sequence"),
    )
    op.create_index(
        "ix_transactions_stock_executed_sequence",
        "transactions",
        ["stock_id", "executed_at", "sequence"],
    )
    op.create_table(
        "price_snapshots",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("stock_id", sa.UUID(), nullable=False),
        sa.Column("price", sa.Numeric(20, 4), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="EGP", nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("observed_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("fetched_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("freshness", freshness, nullable=False),
        sa.ForeignKeyConstraint(["stock_id"], ["stocks.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stock_id", "source", "observed_at"),
    )


def downgrade() -> None:
    op.drop_table("price_snapshots")
    op.drop_index("ix_transactions_stock_executed_sequence", table_name="transactions")
    op.drop_table("transactions")
    op.drop_table("stocks")
    bind = op.get_bind()
    sa.Enum(name="freshness").drop(bind, checkfirst=True)
    sa.Enum(name="transaction_type").drop(bind, checkfirst=True)
