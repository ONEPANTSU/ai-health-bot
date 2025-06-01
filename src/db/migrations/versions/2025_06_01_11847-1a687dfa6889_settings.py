"""llm responses

Revision ID: 1a687dfa6883
Revises: 2848507dd97d
Create Date: 2025-05-26 16:07:36.573558

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "1a687dfa6889"
down_revision: Union[str, None] = "1a687dfa6886"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
               CREATE TABLE IF NOT EXISTS system_settings (
                setting_name TEXT PRIMARY KEY,
                setting_value TEXT NOT NULL
            );
            """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS system_settings CASCADE")
