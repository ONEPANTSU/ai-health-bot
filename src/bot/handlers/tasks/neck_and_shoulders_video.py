from datetime import datetime
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, ContentType
from aiogram.filters import Command

from src.bot.is_test_allowed import is_test_day_allowed
from src.bot.states import NeckVideoStates
from src.media.s3_client import S3Client

router = Router()
s3_client = S3Client()

# Путь к примеру видео
current_dir = Path(__file__).parent
example_neck_video = current_dir / "examples" / "neck_and_shoulders.MOV"

temp_dir = current_dir / "temp"
temp_dir.mkdir(exist_ok=True)


@router.message(Command("neck_exercise_instructions"))
async def send_neck_instructions(message: Message, state: FSMContext):
    if not is_test_day_allowed("neck_exercise"):
        await message.answer(
            '⏳ Задание "Повороты головы и круговые движения шеи" не предназначено для прохождения сегодня'
        )
        return
    await state.set_state(NeckVideoStates.waiting_neck_video)
    if not example_neck_video.exists():
        await message.answer(
            "<b>Шейно-воротниковый отдел</b>\n\n"
            "Задание: «Повороты головы и круговые движения шеи», записать это на видео. Пожалуйста, следуйте инструкциям:\n\n"
            "1. Встаньте прямо. Спина ровная, плечи расслаблены.\n"
            "2. Установите камеру так, чтобы ваше лицо и верхняя часть туловища хорошо были видны в кадре.\n"
            "3. Сначала выполните поворот головы в каждую сторону — вправо и влево.\n"
            "4. Затем выполните круговые движения в обе стороны.\n"
            "5. Дышите ровно. Не напрягайте шею и плечи.\n\n"
            "Пожалуйста, убедитесь, что вы всё время остаетесь в кадре, а движения хорошо видны.",
            parse_mode="HTML",
        )
        return

    with open(example_neck_video, "rb") as f:
        video = BufferedInputFile(f.read(), filename=example_neck_video.name)

        await message.answer_video(
            video=video,
            caption=(
                "<b>Шейно-воротниковый отдел</b>\n\n"
                "Задание: «Повороты головы и круговые движения шеи», записать это на видео. Пожалуйста, следуйте инструкциям:\n\n"
                "1. Встаньте прямо. Спина ровная, плечи расслаблены.\n"
                "2. Установите камеру так, чтобы ваше лицо и верхняя часть туловища хорошо были видны в кадре.\n"
                "3. Сначала выполните поворот головы в каждую сторону — вправо и влево.\n"
                "4. Затем выполните круговые движения в обе стороны.\n"
                "5. Дышите ровно. Не напрягайте шею и плечи.\n\n"
                "Пожалуйста, убедитесь, что вы всё время остаетесь в кадре, а движения хорошо видны."
            ),
            parse_mode="HTML",
        )


@router.message(F.content_type == ContentType.VIDEO, NeckVideoStates.waiting_neck_video)
async def handle_neck_video(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    video = message.video
    video_path = None

    try:
        # Скачиваем видео
        file = await message.bot.get_file(video.file_id)
        video_path = temp_dir / f"neck_{user_id}_{file.file_id}.mp4"

        await message.bot.download_file(file.file_path, destination=str(video_path))

        # Сохраняем в S3
        s3_url = await s3_client.upload_file(
            file_path=str(video_path),
            username=username,
            filename=f"neck_{user_id}_{int(datetime.now().timestamp())}.mp4",
        )

        await message.answer("✅ Видео упражнений для шеи сохранено для анализа")
        await state.clear()

    except Exception as e:
        await message.answer("❌ Ошибка при сохранении видео")
        print(f"Error: {e}")
    finally:
        if video_path and video_path.exists():
            video_path.unlink()


@router.message(F.content_type == ContentType.VIDEO_NOTE)
async def handle_video_note(message: Message):
    await message.answer(
        "Пожалуйста, отправьте видео в обычном формате, а не как видео-сообщение (кружок)"
    )
