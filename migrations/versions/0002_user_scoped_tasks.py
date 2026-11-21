"""Require task owners and make task titles unique per owner.

Revision ID: 0002_user_scoped_tasks
Revises: 0001_initial
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_user_scoped_tasks"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("tasks"):
        raise RuntimeError("tasks table is missing; run the baseline migration first")

    columns = {column["name"] for column in inspector.get_columns("tasks")}
    if "user_id" not in columns:
        raise RuntimeError(
            "Legacy tasks table is missing the required 'user_id' column. "
            "Back up the database first. Create or identify the users table, add a "
            "nullable tasks.user_id foreign key, map every existing task to its rightful "
            "user, verify that no task has a NULL/invalid user_id, then rerun "
            "'alembic upgrade head'. Do not assign a default owner unless that ownership "
            "is explicitly correct. This migration will not guess or discard data."
        )

    orphan_count = bind.execute(
        sa.text("SELECT COUNT(*) FROM tasks WHERE user_id IS NULL")
    ).scalar_one()
    if orphan_count:
        raise RuntimeError(
            f"Cannot enforce task ownership: {orphan_count} task(s) have no user_id. "
            "Back up the database, assign every task to its rightful user, and rerun "
            "'alembic upgrade head'. The migration will not guess ownership or delete data."
        )

    unique_constraints = inspector.get_unique_constraints("tasks")
    title_constraint = next(
        (item for item in unique_constraints if item.get("column_names") == ["title"]), None
    )
    has_owner_constraint = any(
        item.get("column_names") == ["user_id", "title"] for item in unique_constraints
    )
    if bind.dialect.name == "sqlite":
        naming_convention = {"uq": "uq_%(table_name)s_%(column_0_name)s"}
        with op.batch_alter_table("tasks", naming_convention=naming_convention) as batch:
            if title_constraint and not has_owner_constraint:
                batch.drop_constraint(title_constraint.get("name") or "uq_tasks_title", type_="unique")
            batch.alter_column("user_id", existing_type=sa.Integer(), nullable=False)
            if not has_owner_constraint:
                batch.create_unique_constraint("uq_tasks_user_title", ["user_id", "title"])
    else:
        if title_constraint:
            if not title_constraint.get("name"):
                raise RuntimeError("Cannot identify existing task-title unique constraint")
            op.drop_constraint(title_constraint["name"], "tasks", type_="unique")
        op.alter_column("tasks", "user_id", existing_type=sa.Integer(), nullable=False)
        if not has_owner_constraint:
            op.create_unique_constraint("uq_tasks_user_title", "tasks", ["user_id", "title"])

    inspector = sa.inspect(bind)
    indexes = {item["name"] for item in inspector.get_indexes("tasks")}
    if "ix_tasks_status_due_date" in indexes:
        op.drop_index("ix_tasks_status_due_date", table_name="tasks")
    if "ix_tasks_user_status_due_date" not in indexes:
        op.create_index("ix_tasks_user_status_due_date", "tasks", ["user_id", "status", "due_date"])

def downgrade() -> None:
    raise RuntimeError(
        "No automatic downgrade is provided because task titles may now repeat "
        "across users. Restore a verified database backup instead."
    )
