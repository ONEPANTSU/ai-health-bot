from datetime import datetime

from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, InputMediaPhoto
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, ContentType
from aiogram.filters import Command

from src.bot.is_test_allowed import is_test_day_allowed
from src.bot.states import FullbodyPhotoStates
from src.s3_client import S3Client

router = Router()
s3_client = S3Client()

current_dir = Path(__file__).parent
example_fullbody_photos = [
    current_dir / "examples" / "face.jpg",
    current_dir / "examples" / "back.jpg",
    current_dir / "examples" / "side.jpg",
    current_dir / "examples" / "other_side.jpg",
]

temp_dir = current_dir / "temp"
temp_dir.mkdir(exist_ok=True)


@router.message(Command("fullbody_photo_instructions"))
async def send_fullbody_instructions(message: Message, state: FSMContext):
    if not is_test_day_allowed("fullbody_photo"):
        await message.answer(
            '⏳ Задание "Фото в полный рост" не предназначено для прохождения сегодня'
        )
        return
    await state.set_state(FullbodyPhotoStates.waiting_fullbody_photo)

    if not all(p.exists() for p in example_fullbody_photos):
        await message.answer("Примеры фото временно недоступны")
        return

    media = []
    for i, path in enumerate(example_fullbody_photos, 1):
        with open(path, "rb") as f:
            media.append(
                InputMediaPhoto(
                    media=BufferedInputFile(f.read(), filename=path.name),
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
                        "Постарайтесь держать тело прямо и расслабленно."
                        if i == 1
                        else None
                    ),
                    parse_mode="HTML",
                )
            )

    await message.answer_media_group(media=media)


@router.message(
    F.content_type == ContentType.PHOTO, FullbodyPhotoStates.waiting_fullbody_photo
)
async def handle_fullbody_photo(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    photo = message.photo[-1]
    photo_path = None

    try:
        file = await message.bot.get_file(photo.file_id)
        photo_path = temp_dir / f"fullbody_{user_id}_{file.file_id}.jpg"

        await message.bot.download_file(file.file_path, destination=str(photo_path))

        s3_url = await s3_client.upload_file(
            file_path=str(photo_path),
            username=username,
            filename=f"fullbody_{user_id}_{int(datetime.now().timestamp())}.jpg",
        )

        await message.answer("✅ Фото в полный рост сохранено для анализа")
        await state.clear()

    except Exception as e:
        await message.answer("❌ Ошибка при сохранении фото")
        print(f"Error: {e}")
    finally:
        if photo_path and photo_path.exists():
            photo_path.unlink()
