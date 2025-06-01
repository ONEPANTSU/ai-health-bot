import html
import json
import re
from langchain.chat_models import ChatOpenAI
from langchain_core.messages import HumanMessage

from src.db.connection import get_db_connection
from src.db.patient_repository import get_all_records_by_user
from src.db.patient_repository import save_llm_response_separately
from src import config

llm = ChatOpenAI(
    model="gpt-4o",
    openai_api_key=config.OPENAI_API_KEY,
    temperature=0.2,
    max_tokens=2048,
)


def convert_json_to_readable_text(record: dict) -> str:
    q_type = record.get("questionnaire_type")
    if not q_type or q_type not in config.QUESTION_TEXT_MAP:
        return f"[⚠️ Неизвестный тип анкеты: {q_type}]"

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
    return [convert_json_to_readable_text(r) for r in records]


def build_message_chain(
    history_blocks: list[str], prompt: str, media_urls: list[str]
) -> list[HumanMessage]:
    messages = []
    for block in history_blocks:
        messages.append(HumanMessage(content=[{"type": "text", "text": block}]))

    final_content = [{"type": "text", "text": prompt}]
    for url in media_urls or []:
        if url.startswith("http"):
            final_content.append({"type": "image_url", "image_url": {"url": url}})
        else:
            final_content.append(
                {"type": "text", "text": f"[⚠️ Некорректный URL изображения: {url}]"}
            )

    messages.append(HumanMessage(content=final_content))
    return messages


async def analyze_patient(
    prompt: str, media_urls: list[str], history_blocks: list[str]
) -> str:
    try:
        messages = build_message_chain(history_blocks, prompt, media_urls)
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
    history_blocks = await build_history_blocks(telegram_id)

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
        prompt=prompt, media_urls=media_urls, history_blocks=history_blocks
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
        prompt=prompt, media_urls=media_urls, history_blocks=[]
    )

    if resp:
        conn = await get_db_connection()
        await save_llm_response_separately(conn, telegram_id, prompt, resp)
        return markdown_to_html(resp)
    return "Не удалось получить недельный ответ от AI."
