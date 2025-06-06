import asyncio
import json
from collections import defaultdict

from aiogram.fsm.context import FSMContext
from aiogram.types import InputMediaPhoto
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, ContentType
from aiogram.filters import Command

from src.bot.is_test_allowed import is_task_day_allowed
from src.bot.states import FacePhotoStates
from src.bot.utils import send_llm_advice
from src.db.connection import get_db_connection
from src.db.patient_repository import save_patient_record
from src.media.s3_client import S3Client


router = Router()
s3_client = S3Client()

# Пути к примерам фото
current_dir = Path(__file__).parent

temp_dir = current_dir / "temp"
temp_dir.mkdir(exist_ok=True)

pending_media_groups = defaultdict(list)


@router.message(Command("face"))
async def send_face_instructions(message: Message, state: FSMContext):
    await state.clear()
    if not await is_task_day_allowed("face_photo"):
        await message.answer(
            '⏳ Задание "Фото лица" не предназначено для прохождения сегодня'
        )
        return
    await state.set_state(FacePhotoStates.waiting_face_photo)

    s3_keys = ["tasks-examples/face.jpg", "tasks-examples/forehead.jpg"]

    media = []
    try:
        for i, s3_key in enumerate(s3_keys, 1):
            buffered_file = await s3_client.get_media_as_buffered_file(s3_key)

            media.append(
                InputMediaPhoto(
                    media=buffered_file,
                    caption=(
                        "<b>Фото лица</b>\n"
                        "Для анализа необходимо отправить ровно 2 фотографии:\n"
                        "1. Фото лица анфас\n"
                        "2. Фото лба крупным планом\n\n"
                        "<b>Отправьте оба фото как один альбом (выделите 2 фото и отправьте вместе)</b>"
                        if i == 1
                        else None
                    ),
                    parse_mode="HTML",
                )
            )

        await message.answer_media_group(media=media)

    except Exception as e:
        await message.answer(f"⚠️ Не удалось загрузить примеры фото: {e}")
        print(f"Error loading example photos: {e}")


@router.message(F.content_type == ContentType.PHOTO, FacePhotoStates.waiting_face_photo)
async def handle_face_photo(message: Message, state: FSMContext):
    if message.media_group_id:
        pending_media_groups[message.media_group_id].append(message)

        if len(pending_media_groups[message.media_group_id]) == 1:
            asyncio.create_task(
                process_face_group(message, message.media_group_id, state)
            )
        return

    # Одиночные фото не принимаем
    await message.answer(
        "❌ Необходимо отправить ровно 2 фотографии. Пожалуйста, выделите оба фото и отправьте как один альбом."
    )


async def process_face_group(message: Message, group_id: str, state: FSMContext):
    """Обработка группы из 2 фото"""
    await asyncio.sleep(3)  # Ждем все фото группы

    if group_id not in pending_media_groups:
        return

    messages = pending_media_groups.pop(group_id)

    # Проверяем количество фото
    if len(messages) != 2:
        await messages[0].answer(
            "❌ Необходимо отправить ровно 2 фотографии. Пожалуйста, попробуйте еще раз."
        )
        await state.clear()
        return

    user_id = messages[0].from_user.id
    username = messages[0].from_user.username or f"user_{user_id}"
    s3_urls = []
    conn = None

    try:
        # Определяем типы фото
        photo_types = ["face_front", "forehead"]

        for i, msg in enumerate(messages):
            photo = msg.photo[-1]
            file = await msg.bot.get_file(photo.file_id)
            photo_path = temp_dir / f"face_{user_id}_{photo_types[i]}.jpg"

            await msg.bot.download_file(file.file_path, destination=str(photo_path))

            s3_url = await s3_client.upload_file(
                file_path=str(photo_path),
                username=username,
                filename=f"face_{photo_types[i]}.jpg",
            )
            s3_urls.append(s3_url)

            if photo_path.exists():
                photo_path.unlink()

        # Сохраняем в базу
        conn = await get_db_connection()
        answers = {
            "questionnaire_type": "face",
            "prompt_type": "photo_analysis",
            "photos_received": 2,
        }
        await save_patient_record(
            conn=conn,
            telegram_id=user_id,
            answers=json.dumps(answers, ensure_ascii=False),
            gpt_response="",
            s3_links=s3_urls,
            summary="Фото лица (2 ракурса)",
            is_daily=False,
        )

        await messages[0].answer("✅ Оба фото лица сохранены для анализа")
        await send_llm_advice(message, {"prompt_type": "photo_analysis"}, s3_urls)
        await state.clear()

    except Exception as e:
        await messages[0].answer("❌ Ошибка при сохранении фото")
        print(f"Error processing face group: {e}")
    finally:
        if conn:
            await conn.close()
