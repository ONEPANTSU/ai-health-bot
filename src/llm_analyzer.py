from langchain.chat_models import ChatOpenAI
from langchain_core.messages import HumanMessage

import config

llm = ChatOpenAI(
    model="gpt-4-vision-preview",
    openai_api_key=config.OPENAI_API_KEY,
    temperature=0.2,
    max_tokens=2048,
)


async def analyze_patient(
    username: str, answers: str, media_urls: list[str], history_blocks: list[str] = None
) -> str:
    """
    Отправляет текст анкеты + изображения + историю пациента в GPT-4-Vision
    и возвращает рекомендации.
    """
    history_text = "\n---\n".join(history_blocks or []) or "История не найдена."

    prompt_text = (
        f"Пациент: {username}\n\n"
        f"История пациента:\n{history_text}\n\n"
        f"Актуальные анкетные данные:\n{answers}\n\n"
        f"Проанализируй визуальные признаки на изображениях ниже и сформируй "
        f"рекомендации по состоянию пациента, возможные риски и что нужно уточнить у врача."
    )

    content = [{"type": "text", "text": prompt_text}]
    for url in media_urls:
        content.append({"type": "image_url", "image_url": {"url": url}})

    response = await llm.ainvoke([HumanMessage(content=content)])

    return response.content
