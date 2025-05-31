from datetime import datetime
from aiogram.types import BufferedInputFile
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, ContentType
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from src.bot.is_test_allowed import is_test_day_allowed
from src.bot.states import EyePhotoStates
from src.s3_client import S3Client

router = Router()
s3_client = S3Client()

current_dir = Path(__file__).parent
example_photo_path = current_dir / "examples" / "eye.jpg"

temp_dir = current_dir / "temp"
temp_dir.mkdir(exist_ok=True)


@router.message(Command("eye_photo_instructions"))
async def send_eye_instructions(message: Message, state: FSMContext):
    if not is_test_day_allowed("eye_photo"):
        await message.answer(
            '⏳ Задание "Макрофото глаза" не предназначено для прохождения сегодня'
        )
        return
    await state.set_state(EyePhotoStates.waiting_eye_photo)

    if not example_photo_path.exists():
        await message.answer(
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
            "- Сделайте несколько снимков для выбора лучшего",
            parse_mode="HTML",
        )
        return

    # Отправляем пример фото
    with open(example_photo_path, "rb") as f:
        photo = BufferedInputFile(f.read(), filename=example_photo_path.name)

        await message.answer_photo(
            photo=photo,
            caption=(
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
            ),
            parse_mode="HTML",
        )


@router.message(F.content_type == ContentType.PHOTO, EyePhotoStates.waiting_eye_photo)
async def handle_eye_photo(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    photo = message.photo[-1]  # Берем самое качественное фото
    photo_path = None

    try:
        # Скачиваем фото
        file = await message.bot.get_file(photo.file_id)
        photo_path = temp_dir / f"eye_{user_id}_{file.file_id}.jpg"

        await message.bot.download_file(file.file_path, destination=str(photo_path))

        # Сохраняем в S3
        s3_url = await s3_client.upload_file(
            file_path=str(photo_path),
            username=username,
            filename=f"eye_{user_id}_{int(datetime.now().timestamp())}.jpg",
        )

        await message.answer(
            "✅ Макрофото глаза сохранено\n\n"
            "Фото будет проанализировано на:\n"
            "- Состояние сосудов\n"
            "- Четкость радужной оболочки\n"
            "- Наличие покраснений"
        )
        await state.clear()

    except Exception as e:
        await message.answer("❌ Ошибка при сохранении фото глаза")
        print(f"Error processing eye photo: {e}")
    finally:
        if photo_path and photo_path.exists():
            photo_path.unlink()
