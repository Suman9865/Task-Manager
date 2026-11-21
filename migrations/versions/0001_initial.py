"""Create the original task manager tables if they do not exist.

Revision ID: 0001_initial
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("users"):
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("username", sa.String(), nullable=False),
            sa.Column("email", sa.String(), nullable=False),
            sa.Column("hashed_password", sa.String(), nullable=False),
            sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
            sa.UniqueConstraint("email"),
        )
        op.create_index("ix_users_email", "users", ["email"], unique=True)

    inspector = sa.inspect(bind)
    if not inspector.has_table("tasks"):
        op.create_table(
            "tasks",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("title", sa.String(), nullable=False, unique=True),
            sa.Column("description", sa.String(), nullable=True),
            sa.Column("status", sa.String(), nullable=True, server_default="pending"),
            sa.Column("due_date", sa.Date(), nullable=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.CheckConstraint(
                "status IN ('pending', 'in_progress', 'done')",
                name="check_task_status",
            ),
        )
        op.create_index("ix_tasks_status_due_date", "tasks", ["status", "due_date"])
        op.create_index("ix_tasks_user_id", "tasks", ["user_id"])


def downgrade() -> None:
    raise RuntimeError("The baseline migration is intentionally non-destructive.")
