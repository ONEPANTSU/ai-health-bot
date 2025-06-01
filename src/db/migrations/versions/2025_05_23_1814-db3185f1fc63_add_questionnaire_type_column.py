"""add questionnaire_type column

Revision ID: db3185f1fc63
Revises: e3600e2fc9ac
Create Date: 2025-05-23 18:14:04.958942

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "db3185f1fc63"
down_revision: Union[str, None] = "e3600e2fc9ac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Изменяем тип столбца answers с явным преобразованием
    op.execute(
        "ALTER TABLE patient_history ALTER COLUMN answers TYPE JSON USING answers::json"
    )


def downgrade():
    # Возвращаем исходный тип столбца
    op.execute(
        "ALTER TABLE patient_history ALTER COLUMN answers TYPE TEXT USING answers::text"
    )
