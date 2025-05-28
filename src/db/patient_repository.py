import json

import asyncpg


async def create_patient(
    conn,
    telegram_id: int,
    username: str = None,
    full_name: str = None,
    timezone: str = None,
):
    # Если часовой пояс не указан, используем UTC
    tz = timezone if timezone else "UTC"

    await conn.execute(
        """
        INSERT INTO patients (telegram_id, username, full_name, timezone)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (telegram_id) DO UPDATE SET
            username = EXCLUDED.username,
            full_name = EXCLUDED.full_name,
            timezone = EXCLUDED.timezone
        """,
        telegram_id,
        username,
        full_name,
        tz,
    )


async def get_recent_history(
    username: str, conn: asyncpg.Connection, limit: int = 3
) -> list[str]:
    rows = await conn.fetch(
        """
        SELECT created_at, answers, gpt_response
        FROM patient_history
        WHERE username = $1
        ORDER BY created_at DESC
        LIMIT $2
        """,
        username,
        limit,
    )

    history_blocks = []
    for row in reversed(rows):
        text = (
            f"Дата: {row['created_at'].strftime('%Y-%m-%d')}\n"
            f"Ответы: {row['answers']}\n"
            f"Рекомендации GPT: {row['gpt_response']}\n"
        )
        history_blocks.append(text)

    return history_blocks


async def get_all_records_by_user(telegram_id: int, conn: asyncpg.Connection, limit: int = 100) -> list[dict]:
    """
    Возвращает все анкеты пользователя по telegram_id, отсортированные по убыванию даты.
    Гарантирует, что answers — это dict.
    """
    rows = await conn.fetch(
        """
        SELECT ph.created_at, ph.answers, ph.gpt_response
        FROM patient_history ph
        JOIN patients p ON ph.patient_id = p.id
        WHERE p.telegram_id = $1
        ORDER BY ph.created_at DESC
        LIMIT $2
        """,
        telegram_id,
        limit,
    )

    result = []
    for row in rows:
        raw_answers = row["answers"]
        if isinstance(raw_answers, str):
            try:
                answers = json.loads(raw_answers)
            except json.JSONDecodeError:
                answers = {}
        else:
            answers = raw_answers  # уже dict

        result.append({
            "created_at": row["created_at"],
            "answers": answers,
            "gpt_response": row["gpt_response"],
            "questionnaire_type": answers.get("questionnaire_type", "unknown")
        })

    return result

async def save_patient_record(
    conn: asyncpg.Connection,
    telegram_id: int,
    answers: str,
    gpt_response: str,
    s3_links: list[str],
    summary: str = "",
    is_daily: bool = False,
):
    try:
        answers_data = json.loads(answers)
        questionnaire_type = answers_data.get("questionnaire_type")

        if not questionnaire_type:
            raise ValueError("questionnaire_type не указан в answers")

        async with conn.transaction():
            if is_daily:
                # Удаляем только анкету, если она уже была заполнена сегодня
                await conn.execute(
                    """
                    DELETE FROM patient_history
                    WHERE patient_id = (SELECT id FROM patients WHERE telegram_id = $1)
                    AND DATE(created_at) = CURRENT_DATE
                    AND answers->>'questionnaire_type' = $2
                    """,
                    telegram_id,
                    questionnaire_type,
                )
            else:
                # Удаляем все предыдущие записи с этим типом анкеты
                await conn.execute(
                    """
                    DELETE FROM patient_history
                    WHERE patient_id = (SELECT id FROM patients WHERE telegram_id = $1)
                    AND answers->>'questionnaire_type' = $2
                    """,
                    telegram_id,
                    questionnaire_type,
                )

            await conn.execute(
                """
                INSERT INTO patient_history (
                    patient_id, answers, gpt_response, s3_files, summary
                ) VALUES (
                    (SELECT id FROM patients WHERE telegram_id = $1),
                    $2, $3, $4, $5
                )
                """,
                telegram_id,
                answers,
                gpt_response,
                s3_links,
                summary,
            )

    except Exception as e:
        print(f"Ошибка сохранения: {e}")
        raise
