from datetime import datetime

from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, InputMediaPhoto
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, ContentType
from aiogram.filters import Command

from src.bot.is_test_allowed import is_task_day_allowed
from src.bot.states import FacePhotoStates
from src.media.s3_client import S3Client


router = Router()
s3_client = S3Client()

# Пути к примерам фото
current_dir = Path(__file__).parent
example_photos = [
    current_dir / "examples" / "forehead.jpg",
    current_dir / "examples" / "side_from_side.jpg",
]

temp_dir = current_dir / "temp"
temp_dir.mkdir(exist_ok=True)


@router.message(Command("face"))
async def send_face_instructions(message: Message, state: FSMContext):
    if not await is_task_day_allowed("face_photo"):
        await message.answer(
            '⏳ Задание "Фото лица" не предназначено для прохождения сегодня'
        )
        return
    await state.set_state(FacePhotoStates.waiting_face_photo)

    if not all(p.exists() for p in example_photos):
        await message.answer("Примеры фото временно недоступны")
        return

    # Создаем альбом с первым фото, содержащим описание
    media = []
    for i, path in enumerate(example_photos, 1):
        with open(path, "rb") as f:
            media.append(
                InputMediaPhoto(
                    media=BufferedInputFile(f.read(), filename=path.name),
                    caption=(
                        "<b>Фото лица</b>\n"
                        "Для получения качественного макрофото лица рекомендуется выполнить следующие условия:\n"
                        "1. Сделайте снимок без использования косметики, чтобы максимально точно отобразить естественное состояние кожи.\n"
                        "2. Обеспечьте хорошее освещение, равномерно освещая лицо, чтобы подчеркнуть текстуру и особенности кожи.\n"
                        "3. Постарайтесь избегать бликов и теней, которые могут скрывать детали.\n"
                        "4. Расположите камеру так, чтобы объектив был близко к лицу, фокусируясь на деталях кожи — поры, морщинки, неровности.\n"
                        "5. Удерживайте лицо в спокойном положении, избегая движений и мимики.\n"
                        if i == 1
                        else None
                    ),
                    parse_mode="HTML",
                )
            )

    await message.answer_media_group(media=media)


@router.message(F.content_type == ContentType.PHOTO, FacePhotoStates.waiting_face_photo)
async def handle_face_photo(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    photo = message.photo[-1]
    photo_path = None  # Инициализируем переменную

    try:
        # Скачиваем фото
        file = await message.bot.get_file(photo.file_id)
        photo_path = temp_dir / f"face_{user_id}_{file.file_id}.jpg"

        await message.bot.download_file(file.file_path, destination=str(photo_path))

        # Сохраняем в S3
        s3_url = await s3_client.upload_file(
            file_path=str(photo_path),
            username=username,
            filename=f"face_{user_id}_{int(datetime.now().timestamp())}.jpg",
        )

        await message.answer("✅ Фото сохранено для анализа")
        await state.clear()

    except Exception as e:
        await message.answer("❌ Ошибка при сохранении фото")
        print(f"Error: {e}")
    finally:
        if photo_path and photo_path.exists():
            photo_path.unlink()
