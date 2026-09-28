"""course: add weekly_hours_min / weekly_hours_max

Revision ID: 0003_weekly_hours
Revises: 0002_auth_fields
Create Date: 2026-09-27

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0003_weekly_hours"
down_revision = "0002_auth_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("course", sa.Column("weekly_hours_min", sa.Integer(), nullable=True))
    op.add_column("course", sa.Column("weekly_hours_max", sa.Integer(), nullable=True))

    # backfill courses analyzed before these columns existed: the range was
    # already written into `reasoning` as "Weekly study time: 6-9 hours ..."
    op.execute(
        r"""
        UPDATE course
        SET weekly_hours_min = (regexp_match(reasoning, 'Weekly study time: (\d+)-(\d+) hours'))[1]::int,
            weekly_hours_max = (regexp_match(reasoning, 'Weekly study time: (\d+)-(\d+) hours'))[2]::int
        WHERE reasoning ~ 'Weekly study time: \d+-\d+ hours'
        """
    )


def downgrade() -> None:
    op.drop_column("course", "weekly_hours_max")
    op.drop_column("course", "weekly_hours_min")
