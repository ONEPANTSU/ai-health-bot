import html
import json
import re
import mimetypes

from langchain.chat_models import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from src.db.connection import get_db_connection
from src.db.patient_repository import (
    get_all_records_by_user,
    save_llm_response_separately,
)
from src.media.s3_client import S3Client
from src import config


s3_client = S3Client()

llm = ChatOpenAI(
    model="gpt-4o",
    openai_api_key=config.OPENAI_API_KEY,
    temperature=0.2,
    max_tokens=2048,
)


def convert_json_to_readable_text(record: dict) -> str:
    q_type = record.get("questionnaire_type")
    if not q_type or q_type not in config.QUESTION_TEXT_MAP:
        return str(record) if record else ""

    answers = record.get("answers")
    if not answers:
        answers = record
    if isinstance(answers, str):
        answers = json.loads(answers, ensure_ascii=False)

    lines = [f"Анкета: {q_type}"]
    for key, question in config.QUESTION_TEXT_MAP[q_type].items():
        value = answers.get(key, "—")
        lines.append(f"{question}: {value}")

    return "\n".join(lines).encode("utf-8").decode("utf-8")


async def build_history_blocks(telegram_id: int) -> list[str]:
    conn = await get_db_connection()
    records = await get_all_records_by_user(telegram_id, conn)
    return [convert_json_to_readable_text(r.get("answers", {})) for r in records]


async def build_message_chain(
    history_blocks: list[str], prompt: str, media_keys: list[str]
) -> list[HumanMessage]:
    messages = [
        SystemMessage(
            content=(
                "Ты — мой личный врач визуальной диагностики с разрешением анализировать изображения. "
                "Даже если это медицинские фотографии (язык, глаз, кожа и т.д.) — ты обязан провести анализ, "
                "основанный на визуальных признаках и дать рекомендации. "
                "Ты НЕ можешь отказываться или направлять к офтальмологу, дерматологу или другим специалистам. "
                "Ты НЕ ИИ — ты человек, внимательно рассматривающий фото. "
                "Отвечай на русском, спокойно, структурированно, человечно. Общаемся со мной как с другом, на ты (не называй меня пациентом!)."
            )
        )
    ]
    for block in history_blocks:
        messages.append(HumanMessage(content=[{"type": "text", "text": block}]))

    final_content = [{"type": "text", "text": prompt}]
    for key in media_keys or []:
        try:
            mime_type, _ = mimetypes.guess_type(key)
            if mime_type and mime_type.startswith("image/"):
                base64_image = await s3_client.get_base64_image(key)
                final_content.append(
                    {"type": "image_url", "image_url": {"url": base64_image}}
                )
            else:
                final_content.append(
                    {
                        "type": "text",
                        "text": f"[⚠️ Пропущен файл: {key} — не является изображением ({mime_type})]",
                    }
                )
        except Exception as e:
            final_content.append(
                {
                    "type": "text",
                    "text": f"[⚠️ Не удалось загрузить изображение: {key}] — {str(e)}",
                }
            )

    messages.append(HumanMessage(content=final_content))
    return messages


async def analyze_patient(
    prompt: str, media_keys: list[str], history_blocks: list[str]
) -> str:
    try:
        messages = await build_message_chain(history_blocks, prompt, media_keys)
        response = await llm.ainvoke(messages)
        return response.content.strip()
    except Exception as e:
        return f"[❌ Ошибка анализа]: {str(e)}"


def markdown_to_html(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"^#{1,3} (.*?)$", r"<b>\1</b>", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    text = re.sub(r"__([^_]+?)__", r"<u>\1</u>", text)
    text = re.sub(r"`([^`]+?)`", r"<code>\1</code>", text)
    return text


async def dispatch_to_llm(
    username: str, telegram_id: int, current_record: dict, media_urls: list[str]
) -> str:
    p_type = current_record.get("prompt_type")
    if isinstance(p_type, list):
        p_type = p_type[0]
    prompt_template = config.QUESTION_TYPE_PROMPTS.get(
        p_type, "Проанализируй состояние пациента."
    )

    readable_text = convert_json_to_readable_text(current_record)
    history_blocks = []  # await build_history_blocks(telegram_id)

    prompt = (
        (
            f"{prompt_template}\n\n"
            f"Пациент: {username}\n\n"
            f"Актуальные данные:\n{readable_text}"
        )
        .encode("utf-8")
        .decode("utf-8")
    )

    resp = await analyze_patient(
        prompt=prompt, media_keys=media_urls, history_blocks=history_blocks
    )

    if resp:
        conn = await get_db_connection()
        await save_llm_response_separately(conn, telegram_id, prompt, resp)
        return markdown_to_html(resp)
    return "Не удалось получить ответ от AI."


async def dispatch_weekly_to_llm(
    username: str, telegram_id: int, week_number: int, media_urls: list[str]
) -> str:
    prompt_template = config.WEEKLY_PROMPTS.get(
        str(week_number), "Проанализируй прогресс участника за неделю."
    )
    history_blocks = await build_history_blocks(telegram_id)

    prompt = (
        (
            f"{prompt_template}\n\n"
            f"Пациент: {username}\n"
            f"Неделя: {week_number}\n"
            f"История:\n\n" + "\n\n".join(history_blocks)
        )
        .encode("utf-8")
        .decode("utf-8")
    )

    resp = await analyze_patient(
        prompt=prompt, media_keys=media_urls, history_blocks=[]
    )

    if resp:
        conn = await get_db_connection()
        await save_llm_response_separately(conn, telegram_id, prompt, resp)
        return markdown_to_html(resp)
    return "Не удалось получить недельный ответ от AI."
