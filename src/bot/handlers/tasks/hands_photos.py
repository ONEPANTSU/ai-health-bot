import asyncio
import json
from collections import defaultdict
from aiogram.types import InputMediaPhoto
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, ContentType
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from src.bot.is_test_allowed import is_task_day_allowed
from src.bot.states import HandsPhotoStates
from src.bot.utils import send_llm_advice
from src.db.connection import get_db_connection
from src.db.patient_repository import save_patient_record
from src.media.s3_client import S3Client

router = Router()
s3_client = S3Client()

current_dir = Path(__file__).parent
example_photos = [
    current_dir / "examples" / "hands_1.jpg",
    current_dir / "examples" / "hands_2.jpg",
]

temp_dir = current_dir / "temp"
temp_dir.mkdir(exist_ok=True)

pending_hands_groups = defaultdict(list)


@router.message(Command("hands"))
async def send_hands_instructions(message: Message, state: FSMContext):
    await state.clear()
    if not await is_task_day_allowed("hands_photo"):
        await message.answer(
            '⏳ Задание "Фото рук" не предназначено для прохождения сегодня'
        )
        return

    await state.set_state(HandsPhotoStates.waiting_hands_photo)
    await state.update_data(photos=[])  # Инициализируем список для фото

    s3_keys = ["tasks-examples/palms_back.jpg", "tasks-examples/palms_front.jpg"]
    media = []

    try:
        for i, s3_key in enumerate(s3_keys, 1):
            buffered_file = await s3_client.get_media_as_buffered_file(s3_key)

            media.append(
                InputMediaPhoto(
                    media=buffered_file,
                    caption=(
                        "<b>Фото рук</b>\n\n"
                        "Необходимо отправить ровно 2 фотографии:\n"
                        "1. Фото ладоней\n"
                        "2. Фото тыльной стороны кистей\n\n"
                        "<b>Требования:</b>\n"
                        "- Четко видны все пальцы и кисти\n"
                        "- Равномерное освещение\n"
                        "- Без украшений\n\n"
                        if i == 1
                        else None
                    ),
                    parse_mode="HTML",
                )
            )

        await message.answer_media_group(media=media)

    except Exception as e:
        await message.answer(f"⚠️ Не удалось загрузить примеры фото: {e}")


@router.message(
    F.content_type == ContentType.PHOTO, HandsPhotoStates.waiting_hands_photo
)
async def handle_hands_photo(message: Message, state: FSMContext):
    if message.media_group_id:
        if message.media_group_id not in pending_hands_groups:
            pending_hands_groups[message.media_group_id] = {
                "messages": [],
                "user_id": message.from_user.id,
                "state": state,
            }
            asyncio.create_task(process_hands_group(message, message.media_group_id))

        pending_hands_groups[message.media_group_id]["messages"].append(message)
        return

    # Одиночные фото не принимаем
    await message.answer(
        "❌ Необходимо отправить ровно 2 фотографии. Пожалуйста, выделите оба фото и отправьте как один альбом."
    )


async def process_hands_group(message, group_id: str):
    """Обработка группы из 2 фото рук"""
    await asyncio.sleep(3)  # Ждем все фото группы

    if group_id not in pending_hands_groups:
        return

    group_data = pending_hands_groups.pop(group_id)
    messages = group_data["messages"]
    user_id = group_data["user_id"]
    state = group_data["state"]

    # Проверяем количество фото
    if len(messages) != 2:
        await messages[0].answer(
            "❌ Необходимо отправить ровно 2 фотографии. Пожалуйста, попробуйте еще раз."
        )
        await state.clear()
        return

    username = messages[0].from_user.username or f"user_{user_id}"
    s3_urls = []
    conn = None

    try:
        photo_types = ["palms", "backs"]  # Типы фото

        for i, msg in enumerate(messages):
            photo = msg.photo[-1]
            file = await msg.bot.get_file(photo.file_id)
            photo_path = temp_dir / f"hands_{user_id}_{photo_types[i]}.jpg"

            await msg.bot.download_file(file.file_path, destination=str(photo_path))

            s3_url = await s3_client.upload_file(
                file_path=str(photo_path),
                username=username,
                filename=f"hands_{photo_types[i]}.jpg",
            )
            s3_urls.append(s3_url)

            if photo_path.exists():
                photo_path.unlink()

        # Сохраняем в базу
        conn = await get_db_connection()
        answers = {
            "questionnaire_type": "hands",
            "prompt_type": "photo_analysis",
            "photos_count": 2,
        }
        await save_patient_record(
            conn=conn,
            telegram_id=user_id,
            answers=json.dumps(answers, ensure_ascii=False),
            gpt_response="",
            s3_links=s3_urls,
            summary="Фото рук (2 ракурса)",
            is_daily=False,
        )

        await messages[0].answer("✅ Оба фото рук сохранены для анализа")
        await send_llm_advice(message, {"prompt_type": "photo_analysis"}, s3_urls)
        await state.clear()

    except Exception as e:
        await messages[0].answer("❌ Ошибка при сохранении фото")
        print(f"Error processing hands group: {e}")
    finally:
        if conn:
            await conn.close()
