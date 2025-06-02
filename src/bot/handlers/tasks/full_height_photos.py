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
from src.bot.states import FullbodyPhotoStates
from src.db.connection import get_db_connection
from src.db.patient_repository import save_patient_record
from src.media.s3_client import S3Client

router = Router()
s3_client = S3Client()

current_dir = Path(__file__).parent

temp_dir = current_dir / "temp"
temp_dir.mkdir(exist_ok=True)

pending_fullbody_groups = defaultdict(list)


@router.message(Command("full_body"))
async def send_fullbody_instructions(message: Message, state: FSMContext):
    await state.clear()
    if not await is_task_day_allowed("fullbody_photo"):
        await message.answer(
            '⏳ Задание "Фото в полный рост" не предназначено для прохождения сегодня'
        )
        return
    await state.set_state(FullbodyPhotoStates.waiting_fullbody_photo)

    # Ключи файлов в S3 для примеров
    s3_keys = [
        "tasks-examples/full_body_front.jpg",
        "tasks-examples/full_body_back.jpg",
        "tasks-examples/full_body_right.jpg",
        "tasks-examples/full_body_left.jpg",
    ]

    media = []
    try:
        for i, s3_key in enumerate(s3_keys, 1):
            buffered_file = await s3_client.get_media_as_buffered_file(s3_key)

            media.append(
                InputMediaPhoto(
                    media=buffered_file,
                    caption=(
                        "<b>Фото в полный рост</b>\n"
                        "Для выполнения задания подготовьтесь следующим образом:\n\n"
                        "1. Сделайте четыре фотографии в полный рост без обуви:\n"
                        "   - Лицом к камере\n"
                        "   - Спиной к камере\n"
                        "   - Правым плечом к камере\n"
                        "   - Левым плечом к камере\n\n"
                        "2. Убедитесь, что волосы (у девушек) не закрывают плечи и лопатки.\n\n"
                        "<b>Одежда:</b>\n"
                        "- Мужчинам: рекомендуется без футболки для четкого отображения рельефа\n"
                        "- Девушкам: подойдет топ или обтягивающая футболка\n\n"
                        "<b>Отправьте все 4 фото</b>"
                        if i == 1
                        else None
                    ),
                    parse_mode="HTML",
                )
            )

        await message.answer_media_group(media=media)

    except Exception as e:
        await message.answer(f"⚠️ Не удалось загрузить примеры фото: {e}")
        print(f"Error loading fullbody example photos: {e}")


@router.message(
    F.content_type == ContentType.PHOTO, FullbodyPhotoStates.waiting_fullbody_photo
)
async def handle_fullbody_photo(message: Message, state: FSMContext):
    # Получаем текущее состояние
    user_data = await state.get_data()
    current_photos = user_data.get("photos", [])

    # Проверяем, не превышен ли лимит
    if len(current_photos) >= 4:
        await message.answer("❌ Вы уже отправили максимальное количество фото (4).")
        return

    # Обработка медиагруппы
    if message.media_group_id:
        if message.media_group_id not in pending_fullbody_groups:
            pending_fullbody_groups[message.media_group_id] = {
                "messages": [],
                "user_id": message.from_user.id,
                "state": state,
            }
            asyncio.create_task(process_fullbody_group(message.media_group_id))

        pending_fullbody_groups[message.media_group_id]["messages"].append(message)
        return

    # Обработка одиночного фото
    await process_single_fullbody_photo(message, state)


async def process_fullbody_group(group_id: str):
    """Обработка группы из 4 фото"""
    await asyncio.sleep(3)  # Ждем все фото группы

    if group_id not in pending_fullbody_groups:
        return

    group_data = pending_fullbody_groups.pop(group_id)
    messages = group_data["messages"]
    user_id = group_data["user_id"]
    state = group_data["state"]

    # Проверяем количество фото
    if len(messages) != 4:
        await messages[0].answer(
            "❌ Необходимо отправить ровно 4 фотографии. Пожалуйста, попробуйте еще раз."
        )
        await state.set_state(FullbodyPhotoStates.waiting_fullbody_photo)
        return

    # Обрабатываем 4 фото
    username = messages[0].from_user.username or f"user_{user_id}"
    s3_urls = []
    conn = None

    try:
        # Определяем порядковые названия для файлов
        positions = ["front", "back", "right", "left"]

        for i, msg in enumerate(messages):
            photo = msg.photo[-1]
            file = await msg.bot.get_file(photo.file_id)
            photo_path = temp_dir / f"fullbody_{user_id}_{positions[i]}.jpg"

            await msg.bot.download_file(file.file_path, destination=str(photo_path))

            s3_url = await s3_client.upload_file(
                file_path=str(photo_path),
                username=username,
                filename=f"fullbody_{positions[i]}.jpg",
            )
            s3_urls.append(s3_url)

            if photo_path.exists():
                photo_path.unlink()

        # Сохраняем в базу
        conn = await get_db_connection()
        answers = {
            "questionnaire_type": "fullbody",
            "prompt_type": "photo_analysis",
            "photo_count": 4,
        }
        await save_patient_record(
            conn=conn,
            telegram_id=user_id,
            answers=json.dumps(answers, ensure_ascii=False),
            gpt_response="",
            s3_links=s3_urls,
            summary="Фото в полный рост (4 ракурса)",
            is_daily=False,
        )

        await messages[0].answer("✅ Все 4 фотографии сохранены для анализа")
        await state.clear()

    except Exception as e:
        await messages[0].answer("❌ Ошибка при сохранении фото")
        print(f"Error processing fullbody group: {e}")
    finally:
        if conn:
            await conn.close()


async def process_single_fullbody_photo(message: Message, state: FSMContext):
    """Обработка одиночного фото (будет отклонять)"""
    await message.answer(
        "❌ Необходимо отправить ровно 4 фотографии сразу. Пожалуйста, выделите все 4 фото и отправьте как один альбом."
    )
