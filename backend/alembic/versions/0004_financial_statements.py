"""Create financial_statements table.

Revision ID: 0004_financial_statements
Revises: 0003_stock_prices
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004_financial_statements"
down_revision: str | None = "0003_stock_prices"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "financial_statements",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("stock_id", sa.UUID(), nullable=False),
        sa.Column("period_start", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("period_end", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("period_type", sa.String(length=20), nullable=False),
        sa.Column("scope", sa.String(length=20), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="EGP", nullable=False),
        sa.Column("unit_scale", sa.String(length=20), server_default="units", nullable=False),
        sa.Column("revenue", sa.Numeric(20, 4), nullable=True),
        sa.Column("gross_profit", sa.Numeric(20, 4), nullable=True),
        sa.Column("operating_profit", sa.Numeric(20, 4), nullable=True),
        sa.Column("net_income", sa.Numeric(20, 4), nullable=True),
        sa.Column("eps", sa.Numeric(20, 4), nullable=True),
        sa.Column("assets", sa.Numeric(20, 4), nullable=True),
        sa.Column("liabilities", sa.Numeric(20, 4), nullable=True),
        sa.Column("equity", sa.Numeric(20, 4), nullable=True),
        sa.Column("cash", sa.Numeric(20, 4), nullable=True),
        sa.Column("operating_cash_flow", sa.Numeric(20, 4), nullable=True),
        sa.Column("investing_cash_flow", sa.Numeric(20, 4), nullable=True),
        sa.Column("financing_cash_flow", sa.Numeric(20, 4), nullable=True),
        sa.Column("shares_outstanding", sa.Numeric(20, 4), nullable=True),
        sa.Column("dividends_per_share", sa.Numeric(20, 4), nullable=True),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("source_url", sa.String(), nullable=True),
        sa.Column("published_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("fetched_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("version", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["stock_id"], ["stocks.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "stock_id",
            "period_end",
            "period_type",
            "scope",
            "source",
            "version",
            name="uq_financial_statements_stock_period_scope_source_version",
        ),
    )


def downgrade() -> None:
    op.drop_table("financial_statements")
