from datetime import datetime
from aiogram.types import BufferedInputFile
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, ContentType
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from src.bot.is_test_allowed import is_task_day_allowed
from src.bot.states import PlankStates
from src.media.s3_client import S3Client

router = Router()
s3_client = S3Client()


# Пути к примерам
current_dir = Path(__file__).parent
example_photo_path = current_dir / "examples" / "plank.jpg"
example_video_path = current_dir / "examples" / "plank.MOV"

temp_dir = current_dir / "temp"
temp_dir.mkdir(exist_ok=True)


@router.message(Command("plank"))
async def send_plank_instructions(message: Message, state: FSMContext):
    if not await is_task_day_allowed("plank"):
        await message.answer(
            '⏳ Задание "Видео в планке" не предназначено для прохождения сегодня'
        )
        return
    await state.set_state(PlankStates.waiting_plank_video)

    # Сначала отправляем фото с техникой
    if example_photo_path.exists():
        with open(example_photo_path, "rb") as f:
            photo = BufferedInputFile(f.read(), filename=example_photo_path.name)
            await message.answer_photo(
                photo=photo,
                caption="<b>Видео в планке</b>\n\n"
                "<b>Правильная техника планки:</b>\n"
                "- Плечи прямо над локтями\n"
                "- Мышцы живота напряжены\n"
                "- Касание пола: мыски ног и предплечья\n"
                "- Без прогибов в пояснице",
                parse_mode="HTML",
            )
    else:
        await message.answer("⚠️ Пример техники временно недоступен")


@router.message(F.content_type == ContentType.VIDEO, PlankStates.waiting_plank_video)
async def handle_plank_video(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    video = message.video
    video_path = None

    try:
        # Скачиваем видео
        file = await message.bot.get_file(video.file_id)
        video_path = temp_dir / f"plank_{user_id}_{file.file_id}.mp4"

        await message.bot.download_file(file.file_path, destination=str(video_path))

        # Сохраняем в S3
        s3_url = await s3_client.upload_file(
            file_path=str(video_path),
            username=username,
            filename=f"plank_{user_id}_{int(datetime.now().timestamp())}.mp4",
        )

        await message.answer("✅ Видео планки получено")

    except Exception as e:
        await message.answer("❌ Ошибка при сохранении видео")
        print(f"Error: {e}")
    finally:
        if video_path and video_path.exists():
            video_path.unlink()


@router.message(
    F.content_type == ContentType.VIDEO_NOTE, PlankStates.waiting_plank_video
)
async def handle_plank_video_note(message: Message):
    await message.answer(
        "Пожалуйста, отправьте видео в обычном формате, а не как видео-сообщение"
    )
