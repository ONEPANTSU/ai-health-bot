import logging
from aiogram.types import ReplyKeyboardRemove

from src.llm.service import dispatch_to_llm


async def send_llm_advice(
    message: str, data: dict, media_urls: list[str] = None
):
    if not media_urls:
        media_urls = []
    try:
        llm_resp = await dispatch_to_llm(
            username=message.from_user.username,
            telegram_id=message.from_user.id,
            current_record=data,
            media_urls=media_urls,
        )
        
        await message.answer(
            llm_resp,
            reply_markup=ReplyKeyboardRemove(),
        )
    except Exception as e:
        logging.error(f"LLM error: {e}")