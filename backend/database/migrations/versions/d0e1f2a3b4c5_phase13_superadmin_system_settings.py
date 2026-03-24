"""phase13_superadmin_system_settings

- Add: system_settings table (key VARCHAR PK, value TEXT, updated_at TIMESTAMP)
- Seed: default settings (enable_registration=true, platform_announcement='')

Revision ID: d0e1f2a3b4c5
Revises: c1d2e3f4a5b6
Create Date: 2026-03-24 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d0e1f2a3b4c5"
down_revision: Union[str, None] = "c1d2e3f4a5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "system_settings",
        sa.Column("key", sa.String(128), primary_key=True),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Seed default values
    op.execute(
        sa.text("""
            INSERT INTO system_settings (key, value, updated_at)
            VALUES
                ('enable_registration', 'true', NOW()),
                ('platform_announcement', '', NOW()),
                ('default_user_role', '2', NOW())
            ON CONFLICT (key) DO NOTHING
        """)
    )


def downgrade() -> None:
    op.drop_table("system_settings")
