"""initial: pgvector extension, users, course

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-23

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # enables the `vector` column type for future embedding columns
    # (syllabus chunks / evidence RAG), even though no table uses it yet
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(), nullable=False, unique=True),
        sa.Column("role", sa.String(), nullable=False, server_default="student"),
        sa.Column("hash_password", sa.String(), nullable=False),
        sa.Column("salt", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "course",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("course_semester", sa.String()),
        sa.Column("course_name", sa.String()),
        sa.Column("professor_name", sa.String()),
        sa.Column("course_code", sa.String()),
        sa.Column("assessments", JSONB()),
        sa.Column("evidence", JSONB()),
        sa.Column("short_review", sa.Text()),
        sa.Column("workload", sa.Float()),
        sa.Column("conceptual_difficulty", sa.Float()),
        sa.Column("assessment_weighting", sa.Float()),
        sa.Column("continious_study_requirement", sa.Float()),
        sa.Column("student_review", sa.Float()),
        sa.Column("summary", sa.Text()),
        sa.Column("reasoning", sa.Text()),
        sa.Column("ranking", sa.String()),
        sa.Column("point", sa.Float()),
        sa.Column("confidence", sa.Float()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )

    op.create_index("ix_course_user_id", "course", ["user_id"])
    op.create_index(
        "ix_course_assessments_gin", "course", ["assessments"], postgresql_using="gin"
    )
    op.create_index(
        "ix_course_evidence_gin", "course", ["evidence"], postgresql_using="gin"
    )


def downgrade() -> None:
    op.drop_index("ix_course_evidence_gin", table_name="course")
    op.drop_index("ix_course_assessments_gin", table_name="course")
    op.drop_index("ix_course_user_id", table_name="course")
    op.drop_table("course")
    op.drop_table("users")
