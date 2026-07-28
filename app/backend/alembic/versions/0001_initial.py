"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-06-01

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "students",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("color", sa.String(length=16), nullable=False, server_default="#4C7DFF"),
        sa.Column("hourly_rate", sa.Float(), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("archived", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "schedule_templates",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "student_id",
            sa.Integer(),
            sa.ForeignKey("students.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.String(length=5), nullable=False),
        sa.Column("duration_hours", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_schedule_templates_student_id", "schedule_templates", ["student_id"])

    op.create_table(
        "lessons",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "student_id",
            sa.Integer(),
            sa.ForeignKey("students.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "template_id",
            sa.Integer(),
            sa.ForeignKey("schedule_templates.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.String(length=5), nullable=False),
        sa.Column("duration_hours", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=8), nullable=False, server_default="待上"),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "rescheduled_from_id",
            sa.Integer(),
            sa.ForeignKey("lessons.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "rescheduled_to_id",
            sa.Integer(),
            sa.ForeignKey("lessons.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_lessons_date", "lessons", ["date"])
    op.create_index("ix_lessons_student_date", "lessons", ["student_id", "date"])
    op.create_index("ix_lessons_status", "lessons", ["status"])

    op.create_table(
        "settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("timezone", sa.String(length=32), server_default="Asia/Shanghai"),
        sa.Column("week_start", sa.Integer(), server_default="1"),
        sa.Column("currency_symbol", sa.String(length=4), server_default="¥"),
        sa.Column("generate_weeks_ahead", sa.Integer(), server_default="12"),
        sa.Column("default_duration_hours", sa.Float(), server_default="1.0"),
        sa.Column("visible_time_start", sa.String(length=5), server_default="07:00"),
        sa.Column("visible_time_end", sa.String(length=5), server_default="22:00"),
        sa.Column("theme", sa.String(length=8), server_default="auto"),
    )

    op.create_table(
        "user_profile",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("display_name", sa.String(length=64), server_default=""),
        sa.Column("avatar_color", sa.String(length=16), server_default="#4C7DFF"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # 初始化单行设置和 profile
    op.execute(
        "INSERT INTO settings (id, timezone, week_start, currency_symbol, "
        "generate_weeks_ahead, default_duration_hours, visible_time_start, "
        "visible_time_end, theme) VALUES "
        "(1, 'Asia/Shanghai', 1, '¥', 12, 1.0, '07:00', '22:00', 'auto')"
    )
    op.execute(
        "INSERT INTO user_profile (id, display_name, avatar_color, created_at) VALUES "
        "(1, '老师', '#4C7DFF', CURRENT_TIMESTAMP)"
    )


def downgrade() -> None:
    op.drop_table("user_profile")
    op.drop_table("settings")
    op.drop_index("ix_lessons_status", table_name="lessons")
    op.drop_index("ix_lessons_student_date", table_name="lessons")
    op.drop_index("ix_lessons_date", table_name="lessons")
    op.drop_table("lessons")
    op.drop_index("ix_schedule_templates_student_id", table_name="schedule_templates")
    op.drop_table("schedule_templates")
    op.drop_table("students")
