import json
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, ContentType
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from src.bot.is_test_allowed import is_task_day_allowed
from src.bot.states import EyePhotoStates
from src.bot.utils import send_llm_advice
from src.db.connection import get_db_connection
from src.db.patient_repository import save_patient_record
from src.media.s3_client import S3Client

router = Router()
s3_client = S3Client()

current_dir = Path(__file__).parent

temp_dir = current_dir / "temp"
temp_dir.mkdir(exist_ok=True)


@router.message(Command("eye"))
async def send_eye_instructions(message: Message, state: FSMContext):
    await state.clear()
    if not await is_task_day_allowed("eye_photo"):
        await message.answer(
            '⏳ Задание "Макрофото глаза" не предназначено для прохождения сегодня'
        )
        return
    await state.set_state(EyePhotoStates.waiting_eye_photo)
    s3_key = "tasks-examples/eye.jpg"
    try:
        media = await s3_client.get_media_as_buffered_file(s3_key)
        caption = (
            "<b>Макрофото глаза</b>\n\n"
            "<b>Требования к фото:</b>\n"
            "1. Сфотографируйте один глаз крупным планом\n"
            "2. Используйте хорошее освещение без бликов\n"
            "3. Фокус должен быть на радужной оболочке\n"
            "4. Избегайте теней на глазу\n"
            "5. Глаз должен быть открыт естественно\n\n"
            "<b>Советы:</b>\n"
            "- Используйте макрорежим камеры\n"
            "- Снимайте при дневном свете\n"
            "- Держите камеру устойчиво\n"
            "- Сделайте несколько снимков для выбора лучшего"
        )
        await message.answer_photo(
            photo=media,
            caption=caption,
            parse_mode="HTML",
        )
    except Exception as e:
        await message.answer(f"⚠️ Не удалось загрузить медиа с инструкцией: {e}")


@router.message(F.content_type == ContentType.PHOTO, EyePhotoStates.waiting_eye_photo)
async def handle_eye_photo(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    photo = message.photo[-1]
    photo_path = None

    try:
        # Скачиваем фото
        file = await message.bot.get_file(photo.file_id)
        photo_path = temp_dir / f"eye_{user_id}_{file.file_id}.jpg"

        await message.bot.download_file(file.file_path, destination=str(photo_path))

        # Сохраняем в S3
        s3_key = await s3_client.upload_file(
            file_path=str(photo_path),
            username=username,
            filename="eye.jpg",
        )
        conn = await get_db_connection()
        answers = {
            "questionnaire_type": "eye",
            "prompt_type": "photo_analysis",
        }
        await save_patient_record(
            conn=conn,
            telegram_id=user_id,
            answers=json.dumps(answers, ensure_ascii=False),
            gpt_response="",
            s3_links=[s3_key],
            summary="Макрофото глаза",
            is_daily=False,
        )

        await message.answer(
            "✅ Макрофото глаза сохранено"
        )
        await send_llm_advice(message, {"prompt_type": "photo_analysis"}, [s3_key])
        await state.clear()

    except Exception as e:
        await message.answer("❌ Ошибка при сохранении фото глаза")
        print(f"Error processing eye photo: {e}")
    finally:
        if photo_path and photo_path.exists():
            photo_path.unlink()
