from datetime import datetime
from aiogram.types import BufferedInputFile, InputMediaPhoto
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, ContentType
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from src.bot.is_test_allowed import is_test_day_allowed
from src.bot.states import HandsPhotoStates
from src.s3_client import S3Client

router = Router()
s3_client = S3Client()

current_dir = Path(__file__).parent
example_photos = [
    current_dir / "examples" / "hands_1.jpg",
    current_dir / "examples" / "hands_2.jpg",
]

temp_dir = current_dir / "temp"
temp_dir.mkdir(exist_ok=True)


@router.message(Command("hands_photo_instructions"))
async def send_hands_instructions(message: Message, state: FSMContext):
    if not is_test_day_allowed("hands_photo"):
        await message.answer(
            '⏳ Задание "Фото рук" не предназначено для прохождения сегодня'
        )
        return
    await state.set_state(HandsPhotoStates.waiting_hands_photo)

    if not all(p.exists() for p in example_photos):
        await message.answer(
            "<b>Фото рук</b>\n\n"
            "Расположите кисти рук так, чтобы полностью были видны как кисть, так и пальцы.\n\n"
            "<b>Требования:</b>\n"
            "— Держите руки в нейтральном положении\n"
            "— Избегайте сгибания или скручивания\n"
            "— Обеспечьте равномерное освещение\n"
            "— Избегайте теней и бликов\n"
            "— Кожа должна быть хорошо видна\n"
            "— Без украшений и мешающих предметов",
            parse_mode="HTML",
        )
        return

    media = []
    for i, path in enumerate(example_photos, 1):
        with open(path, "rb") as f:
            media.append(
                InputMediaPhoto(
                    media=BufferedInputFile(f.read(), filename=path.name),
                    caption=(
                        "<b>Фото рук</b>\n\n"
                        "Расположите кисти рук так, чтобы полностью были видны как кисть, так и пальцы.\n\n"
                        "<b>Требования:</b>\n"
                        "— Держите руки в нейтральном положении\n"
                        "— Избегайте сгибания или скручивания\n"
                        "— Обеспечьте равномерное освещение\n"
                        "— Избегайте теней и бликов\n"
                        "— Кожа должна быть хорошо видна\n"
                        "— Без украшений и мешающих предметов"
                        if i == 1
                        else None
                    ),
                    parse_mode="HTML",
                )
            )

    await message.answer_media_group(media=media)


@router.message(
    F.content_type == ContentType.PHOTO, HandsPhotoStates.waiting_hands_photo
)
async def handle_hands_photo(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    photo = message.photo[-1]
    photo_path = None

    try:
        # Скачиваем фото
        file = await message.bot.get_file(photo.file_id)
        photo_path = temp_dir / f"hands_{user_id}_{file.file_id}.jpg"

        await message.bot.download_file(file.file_path, destination=str(photo_path))

        # Сохраняем в S3
        s3_url = await s3_client.upload_file(
            file_path=str(photo_path),
            username=username,
            filename=f"hands_{user_id}_{int(datetime.now().timestamp())}.jpg",
        )

        await message.answer("✅ Фото рук сохранено для анализа")
        await state.clear()

    except Exception as e:
        await message.answer("❌ Ошибка при сохранении фото")
        print(f"Error: {e}")
    finally:
        if photo_path and photo_path.exists():
            photo_path.unlink()
