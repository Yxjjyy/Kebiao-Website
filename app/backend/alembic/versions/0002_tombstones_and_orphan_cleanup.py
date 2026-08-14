"""tombstones and orphan cleanup

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-13

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "template_lesson_tombstones",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "template_id",
            sa.Integer(),
            sa.ForeignKey("schedule_templates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_tombstones_template_date",
        "template_lesson_tombstones",
        ["template_id", "date"],
    )

    # 清理现存孤儿外键（此前 SQLite 未启用外键约束，删除模板/课时可能留下悬空引用）
    op.execute(
        "UPDATE lessons SET template_id = NULL "
        "WHERE template_id IS NOT NULL AND template_id NOT IN (SELECT id FROM schedule_templates)"
    )
    op.execute(
        "UPDATE lessons SET rescheduled_from_id = NULL "
        "WHERE rescheduled_from_id IS NOT NULL "
        "AND rescheduled_from_id NOT IN (SELECT id FROM lessons)"
    )
    op.execute(
        "UPDATE lessons SET rescheduled_to_id = NULL "
        "WHERE rescheduled_to_id IS NOT NULL "
        "AND rescheduled_to_id NOT IN (SELECT id FROM lessons)"
    )


def downgrade() -> None:
    op.drop_index("ix_tombstones_template_date", table_name="template_lesson_tombstones")
    op.drop_table("template_lesson_tombstones")
