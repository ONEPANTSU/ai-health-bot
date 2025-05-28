"""init schema

Revision ID: e3600e2fc9ac
Revises:
Create Date: 2025-05-06 19:49:19.400327

"""

from alembic import op

revision = "e3600e2fc9ac"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    with open("src/db/models.sql") as f:
        op.execute(f.read())


def downgrade():
    op.execute("DROP TABLE IF EXISTS patient_history CASCADE")
    op.execute("DROP TABLE IF EXISTS patients CASCADE")
