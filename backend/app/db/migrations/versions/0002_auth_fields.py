"""auth: rename username -> email, add recovery_code

Revision ID: 0002_auth_fields
Revises: 0001_initial
Create Date: 2026-09-26

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0002_auth_fields"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("users", "username", new_column_name="email")
    op.add_column("users", sa.Column("recovery_code", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "recovery_code")
    op.alter_column("users", "email", new_column_name="username")
