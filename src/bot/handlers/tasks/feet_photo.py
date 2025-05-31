from datetime import datetime
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, ContentType
from aiogram.filters import Command

from src.bot.is_test_allowed import is_test_day_allowed
from src.bot.states import FeetPhotoStates
from src.s3_client import S3Client

router = Router()
s3_client = S3Client()

# Путь к примеру фото стоп
current_dir = Path(__file__).parent
example_feet_photo = current_dir / "examples" / "feet.jpg"

temp_dir = current_dir / "temp"
temp_dir.mkdir(exist_ok=True)


@router.message(Command("feet_photo_instructions"))
async def send_feet_instructions(message: Message, state: FSMContext):
    if not is_test_day_allowed("feet_photo"):
        await message.answer(
            '⏳ Задание "Фото стоп" не предназначено для прохождения сегодня'
        )
        return
    await state.set_state(FeetPhotoStates.waiting_feet_photo)

    if not example_feet_photo.exists():
        await message.answer(
            "<b>Фото стоп (анфас и спереди)</b>\n\n"
            "Три фотографии:\n"
            "1. Стопы вместе видно лицевую сторону стопы, пальцы, фото спереди.\n"
            "2. Стопы вместе, пятки рядом друг с другом, фото сзади.\n"
            "3. Фото подошвы ступни.",
            parse_mode="HTML",
        )
        return

    # Отправляем фото с инструкцией
    with open(example_feet_photo, "rb") as f:
        photo = BufferedInputFile(f.read(), filename=example_feet_photo.name)

        await message.answer_photo(
            photo=photo,
            caption=(
                "<b>Фото стоп (анфас и спереди)</b>\n\n"
                "Три фотографии:\n"
                "1. Стопы вместе видно лицевую сторону стопы, пальцы, фото спереди.\n"
                "2. Стопы вместе, пятки рядом друг с другом, фото сзади.\n"
                "3. Фото подошвы ступни."
            ),
            parse_mode="HTML",
        )


@router.message(F.content_type == ContentType.PHOTO, FeetPhotoStates.waiting_feet_photo)
async def handle_feet_photo(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    photo = message.photo[-1]
    photo_path = None

    try:
        # Скачиваем фото
        file = await message.bot.get_file(photo.file_id)
        photo_path = temp_dir / f"feet_{user_id}_{file.file_id}.jpg"

        await message.bot.download_file(file.file_path, destination=str(photo_path))

        # Сохраняем в S3
        s3_url = await s3_client.upload_file(
            file_path=str(photo_path),
            username=username,
            filename=f"feet_{user_id}_{int(datetime.now().timestamp())}.jpg",
        )

        await message.answer("✅ Фото стоп сохранено для анализа")
        await state.clear()

    except Exception as e:
        await message.answer("❌ Ошибка при сохранении фото")
        print(f"Error: {e}")
    finally:
        if photo_path and photo_path.exists():
            photo_path.unlink()
