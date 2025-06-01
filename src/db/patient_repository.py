from datetime import datetime
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

async def get_all_patients(conn) -> list[dict]:
    """
    Возвращает список всех активных пользователей.
    """
    rows = await conn.fetch(
        """
        SELECT telegram_id, username, full_name, timezone, testing_start_date
        FROM patients

        WHERE is_active = true
        """
    )
    return [dict(row) for row in rows]

async def get_all_records_by_user(telegram_id: int, conn, date_from: datetime | None = None, date_to: datetime | None = None) -> list[dict]:
    """
    Возвращает все записи пользователя за указанный день (или диапазон).
    """
    if not date_from or not date_to:
        rows = await conn.fetch(
            """
            SELECT answers, s3_files
            FROM patient_history ph
            JOIN patients p ON p.id = ph.patient_id
            WHERE p.telegram_id = $1
            ORDER BY ph.created_at ASC
            """,
            telegram_id,
        )
    else:
        rows = await conn.fetch(
            """
            SELECT answers, s3_files
            FROM patient_history ph
            JOIN patients p ON p.id = ph.patient_id
            WHERE p.telegram_id = $1
            AND ph.created_at >= $2 AND ph.created_at < $3
            ORDER BY ph.created_at ASC
            """,
            telegram_id,
            date_from,
            date_to,
        )
    result = []
    for row in rows:
        record = dict(row)
        record["answers"] = json.loads(record["answers"]) if record.get("answers") else {}
        result.append(record)
    return result


async def save_llm_response(conn, telegram_id: int, response_text: str, summary: str = None):
    """
    Сохраняет ответ от LLM в patient_history в виде новой записи.
    """
    await conn.execute(
        """
        INSERT INTO patient_history (patient_id, answers, gpt_response, summary, created_at)
        SELECT id, '{}'::jsonb, $2, $3, now()
        FROM patients
        WHERE telegram_id = $1
        """,
        telegram_id,
        response_text,
        summary or "",
    )

async def save_llm_response_separately(conn, telegram_id: int, prompt: str, response: str):
    """
    Сохраняет промпт и ответ GPT в отдельную таблицу llm_responses.
    """
    await conn.execute(
        """
        INSERT INTO llm_responses (patient_id, prompt, gpt_response)
        SELECT id, $2, $3 FROM patients WHERE telegram_id = $1
        """,
        telegram_id,
        prompt,
        response,
    )