"""llm responses

Revision ID: 1a687dfa6883
Revises: 2848507dd97d
Create Date: 2025-05-26 16:07:36.573558

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1a687dfa6888"
down_revision: Union[str, None] = "1a687dfa6889"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "patients", sa.Column("testing_start_date", sa.TIMESTAMP(), nullable=True)
    )


def downgrade():
    op.drop_column("patients", "testing_start_date")
