"""add questionnaire_type column

Revision ID: db3185f1fc63
Revises: e3600e2fc9ac
Create Date: 2025-05-23 18:14:04.958942

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "db3185f1fc63"
down_revision: Union[str, None] = "e3600e2fc9ac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Добавляем новый столбец
    op.add_column(
        "patient_history", sa.Column("questionnaire_type", sa.String(), nullable=True)
    )

    # Изменяем тип столбца answers с явным преобразованием
    op.execute(
        "ALTER TABLE patient_history ALTER COLUMN answers TYPE JSON USING answers::json"
    )

    # Если нужно обновить существующие данные
    op.execute("""
        UPDATE patient_history 
        SET questionnaire_type = 
            CASE 
                WHEN answers::text LIKE '%"questionnaire_type":"daily"%' THEN 'daily'
                WHEN answers::text LIKE '%"questionnaire_type":"greeting"%' THEN 'greeting'
                ELSE 'unknown'
            END
    """)


def downgrade():
    # Возвращаем исходный тип столбца
    op.execute(
        "ALTER TABLE patient_history ALTER COLUMN answers TYPE TEXT USING answers::text"
    )

    # Удаляем добавленный столбец
    op.drop_column("patient_history", "questionnaire_type")
