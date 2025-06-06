import asyncio
import json
from collections import defaultdict
from aiogram.fsm.context import FSMContext
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, ContentType
from aiogram.filters import Command

from src.bot.is_test_allowed import is_task_day_allowed
from src.bot.states import FeetPhotoStates
from src.bot.utils import send_llm_advice
from src.db.connection import get_db_connection
from src.db.patient_repository import save_patient_record
from src.media.s3_client import S3Client

router = Router()
s3_client = S3Client()

# Путь к примеру фото стоп
current_dir = Path(__file__).parent

temp_dir = current_dir / "temp"
temp_dir.mkdir(exist_ok=True)

pending_feet_groups = defaultdict(list)


@router.message(Command("feet"))
async def send_feet_instructions(message: Message, state: FSMContext):
    await state.clear()
    if not await is_task_day_allowed("feet_photo"):
        await message.answer(
            '⏳ Задание "Фото стоп" не предназначено для прохождения сегодня'
        )
        return
    await state.set_state(FeetPhotoStates.waiting_feet_photo)
    s3_key = "tasks-examples/feet.jpg"
    try:
        media = await s3_client.get_media_as_buffered_file(s3_key)

        await message.answer_photo(
            photo=media,
            caption=(
                "<b>Фото стоп (анфас и спереди)</b>\n\n"
                "Три фотографии:\n"
                "1. Стопы вместе видно лицевую сторону стопы, пальцы, фото спереди.\n"
                "2. Стопы вместе, пятки рядом друг с другом, фото сзади.\n"
                "3. Фото подошвы ступни."
            ),
            parse_mode="HTML",
        )
    except Exception as e:
        await message.answer(f"⚠️ Не удалось загрузить медиа с инструкцией: {e}")


@router.message(F.content_type == ContentType.PHOTO, FeetPhotoStates.waiting_feet_photo)
async def handle_feet_photo(message: Message, state: FSMContext):
    if message.media_group_id:
        pending_feet_groups[message.media_group_id].append(message)

        if len(pending_feet_groups[message.media_group_id]) == 1:
            asyncio.create_task(process_feet_group(message, message.media_group_id, state))
        return

    # Обработка одиночного фото
    await process_single_feet_photo(message, state)


async def process_single_feet_photo(message: Message, state: FSMContext):
    """Обработка одиночного фото стопы"""
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    photo = message.photo[-1]
    photo_path = None

    try:
        file = await message.bot.get_file(photo.file_id)
        photo_path = temp_dir / f"feet_{user_id}_{file.file_id}.jpg"

        await message.bot.download_file(file.file_path, destination=str(photo_path))

        s3_url = await s3_client.upload_file(
            file_path=str(photo_path),
            username=username,
            filename=f"feet_{file.file_id}.jpg",
        )

        conn = await get_db_connection()
        answers = {
            "questionnaire_type": "feet",
            "prompt_type": "photo_analysis",
        }
        await save_patient_record(
            conn=conn,
            telegram_id=user_id,
            answers=json.dumps(answers, ensure_ascii=False),
            gpt_response="",
            s3_links=[s3_url],
            summary="Фото стоп (одиночное)",
            is_daily=False,
        )

        await message.answer("✅ Фото стоп сохранено для анализа")
        await send_llm_advice(message, {"prompt_type": "photo_analysis"}, [s3_url])
        await state.clear()

    except Exception as e:
        await message.answer("❌ Ошибка при сохранении фото")
        print(f"Error processing feet photo: {e}")
    finally:
        if photo_path and photo_path.exists():
            photo_path.unlink()


async def process_feet_group(message: Message, group_id: str, state: FSMContext):
    """Обработка группы фото стоп"""
    await asyncio.sleep(3)

    messages = pending_feet_groups.pop(group_id, [])
    if not messages:
        return

    user_id = messages[0].from_user.id
    username = messages[0].from_user.username or f"user_{user_id}"
    s3_urls = []
    conn = None

    try:
        for i, msg in enumerate(messages, 1):
            photo = msg.photo[-1]
            file = await msg.bot.get_file(photo.file_id)
            photo_path = temp_dir / f"feet_{user_id}_{file.file_id}_{i}.jpg"

            await msg.bot.download_file(file.file_path, destination=str(photo_path))

            s3_url = await s3_client.upload_file(
                file_path=str(photo_path),
                username=username,
                filename=f"feet_{user_id}_{i}.jpg",  # feet_123_1.jpg, feet_123_2.jpg и т.д.
            )
            s3_urls.append(s3_url)

            if photo_path.exists():
                photo_path.unlink()

        # Сохраняем все ссылки в базу
        conn = await get_db_connection()
        answers = {
            "questionnaire_type": "feet",
            "prompt_type": "photo_analysis",
            "photo_count": len(s3_urls),
        }
        await save_patient_record(
            conn=conn,
            telegram_id=user_id,
            answers=json.dumps(answers, ensure_ascii=False),
            gpt_response="",
            s3_links=s3_urls,
            summary=f"Фото стоп ({len(s3_urls)} снимков)",
            is_daily=False,
        )

        await messages[0].answer("✅ Все фото стоп сохранены для анализа")
        await send_llm_advice(message, {}, s3_urls)
        await state.clear()

    except Exception as e:
        await messages[0].answer("❌ Ошибка при сохранении группы фото")
        print(f"Error processing feet photo group: {e}")
    finally:
        if conn:
            await conn.close()
