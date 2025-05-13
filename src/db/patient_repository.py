import asyncpg


async def create_patient(
    conn, telegram_id: int, username: str = None, full_name: str = None
):
    await conn.execute(
        """
        INSERT INTO patients (telegram_id, username, full_name)
        VALUES ($1, $2, $3)
        ON CONFLICT (telegram_id) DO NOTHING
        """,
        telegram_id,
        username,
        full_name,
    )


async def save_patient_record(
    conn: asyncpg.Connection,
    telegram_id: int,
    answers: str,
    gpt_response: str,
    s3_links: list[str],
    summary: str = "",
):
    await conn.execute(
        """
        INSERT INTO patient_history (patient_id, username, answers, gpt_response, s3_files, summary)
        VALUES (
            (SELECT id FROM patients WHERE telegram_id = $1),
            (SELECT username FROM patients WHERE telegram_id = $1),
            $2, $3, $4, $5
        )
        """,
        telegram_id,
        answers,
        gpt_response,
        s3_links,
        summary,
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
