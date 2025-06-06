import json
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, ContentType
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from src.bot.is_test_allowed import is_task_day_allowed
from src.bot.states import TonguePhotoStates
from src.bot.utils import send_llm_advice
from src.db.connection import get_db_connection
from src.db.patient_repository import save_patient_record
from src.media.s3_client import S3Client

router = Router()
s3_client = S3Client()

current_dir = Path(__file__).parent
temp_dir = current_dir / "temp"
temp_dir.mkdir(exist_ok=True)


@router.message(Command("tongue"))
async def send_tongue_instructions(message: Message, state: FSMContext):
    await state.clear()
    if not await is_task_day_allowed("tongue_photo"):
        await message.answer(
            '⏳ Задание "Фото языка утром" не предназначено для прохождения сегодня'
        )
        return
    await state.set_state(TonguePhotoStates.waiting_tongue_photo)

    try:
        text = (
            "<b>Фотография языка утром</b>\n\n"
            "<b>Как правильно сделать фото:</b>\n"
            "1. Сделайте фото сразу после пробуждения, до чистки зубов\n"
            "2. Используйте естественное освещение (у окна)\n"
            "3. Высуньте язык расслабленно, без напряжения\n"
            "4. Сфотографируйте язык целиком (от кончика до корня)\n\n"
            "<b>Требования к фото:</b>\n"
            "— Язык должен быть хорошо освещен\n"
            "— На фото должна быть видна вся поверхность языка\n"
            "— Избегайте бликов и теней\n"
            "— Фото должно быть в фокусе\n\n"
        )
        await message.answer(
            text=text,
            parse_mode="HTML",
        )
    except Exception as e:
        await message.answer(f"⚠️ Не удалось загрузить медиа с инструкцией: {e}")


@router.message(
    F.content_type == ContentType.PHOTO, TonguePhotoStates.waiting_tongue_photo
)
async def handle_tongue_photo(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    photo = message.photo[-1]
    photo_path = None

    try:
        file = await message.bot.get_file(photo.file_id)
        photo_path = temp_dir / f"tongue_{user_id}_{file.file_id}.jpg"

        await message.bot.download_file(file.file_path, destination=str(photo_path))

        s3_key = await s3_client.upload_file(
            file_path=str(photo_path),
            username=username,
            filename="tongue.jpg",
        )

        conn = await get_db_connection()
        answers = {
            "questionnaire_type": "tongue",
            "prompt_type": "photo_analysis",
        }
        await save_patient_record(
            conn=conn,
            telegram_id=user_id,
            answers=json.dumps(answers, ensure_ascii=False),
            gpt_response="",
            s3_links=[s3_key],
            summary="Фото языка утром",
            is_daily=False,
        )

        await message.answer("✅ Фото языка сохранено для анализа")
        await send_llm_advice(
            message,
            {
                "prompt_type": "photo_analysis",
            },
            [s3_key],
        )
        await state.clear()

    except Exception as e:
        await message.answer("❌ Ошибка при сохранении фото языка")
        print(f"Error processing tongue photo: {e}")
    finally:
        if photo_path and photo_path.exists():
            photo_path.unlink()
