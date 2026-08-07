"""Use Nebraska as the default document jurisdiction."""

from alembic import op
import sqlalchemy as sa

revision = "0002_nebraska_default"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("documents") as batch:
        batch.alter_column(
            "jurisdiction",
            existing_type=sa.String(length=100),
            server_default="Nebraska",
            existing_nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("documents") as batch:
        batch.alter_column(
            "jurisdiction",
            existing_type=sa.String(length=100),
            server_default=None,
            existing_nullable=False,
        )
