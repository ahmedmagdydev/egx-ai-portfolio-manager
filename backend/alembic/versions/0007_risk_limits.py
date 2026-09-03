"""Create risk_limits table.

Revision ID: 0007_risk_limits
Revises: 0006_ai_analysis_logs
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0007_risk_limits"
down_revision: str | None = "0006_ai_analysis_logs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "risk_limits",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("max_single_position_percent", sa.Numeric(5, 2), nullable=False),
        sa.Column("max_sector_exposure_percent", sa.Numeric(5, 2), nullable=False),
        sa.Column("min_cash_percent", sa.Numeric(5, 2), nullable=False),
        sa.Column("max_portfolio_volatility_annual", sa.Numeric(5, 2), nullable=True),
        sa.Column("max_drawdown_percent", sa.Numeric(5, 2), nullable=True),
        sa.Column("rebalancing_threshold_percent", sa.Numeric(5, 2), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("risk_limits")
