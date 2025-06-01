from datetime import datetime
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, ContentType
from aiogram.filters import Command

from src.bot.is_test_allowed import is_test_day_allowed
from src.bot.states import SquatsVideoStates
from src.media.s3_client import S3Client

router = Router()
s3_client = S3Client()

# Путь к примеру видео
current_dir = Path(__file__).parent
example_squats_video = current_dir / "examples" / "squats.MOV"

temp_dir = current_dir / "temp"
temp_dir.mkdir(exist_ok=True)


@router.message(Command("squats"))
async def send_squats_instructions(message: Message, state: FSMContext):
    if not is_test_day_allowed("squats"):
        await message.answer(
            '⏳ Задание "10 приседаний" не предназначено для прохождения сегодня'
        )
        return
    await state.set_state(SquatsVideoStates.waiting_squats_video)

    if not example_squats_video.exists():
        await message.answer(
            "<b>Приседания</b>\n"
            "Задание: «10 приседаний».\n\n"
            "Перед тем как начать съёмку, внимательно посмотрите видеоинструкцию. Убедитесь, что:\n"
            "— камера установлена стабильно и снимает вас в полный рост,\n"
            "— вас хорошо видно на протяжении всего выполнения упражнения,\n"
            "— вы выполняете 10 приседаний подряд без пауз и остановок,\n"
            "— приседайте в своём обычном, комфортном темпе.\n\n"
            "Старайтесь держать спину прямо, опускаясь до уровня, при котором бёдра параллельны полу. "
            "Колени не должны выходить за пределы носков.",
            parse_mode="HTML",
        )
        return

    # Отправляем видео с инструкцией
    with open(example_squats_video, "rb") as f:
        video = BufferedInputFile(f.read(), filename=example_squats_video.name)

        await message.answer_video(
            video=video,
            caption=(
                "<b>Приседания</b>\n"
                "Задание: «10 приседаний».\n\n"
                "Перед тем как начать съёмку, убедитесь, что:\n"
                "— камера установлена стабильно и снимает вас в полный рост,\n"
                "— вас хорошо видно на протяжении всего выполнения упражнения,\n"
                "— вы выполняете 10 приседаний подряд без пауз и остановок,\n"
                "— приседайте в своём обычном, комфортном темпе.\n\n"
                "Старайтесь держать спину прямо, опускаясь до уровня, при котором бёдра параллельны полу. "
                "Колени не должны выходить за пределы носков."
            ),
            parse_mode="HTML",
        )


@router.message(
    F.content_type == ContentType.VIDEO, SquatsVideoStates.waiting_squats_video
)
async def handle_squats_video(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    video = message.video
    video_path = None

    try:
        # Скачиваем видео
        file = await message.bot.get_file(video.file_id)
        video_path = temp_dir / f"squats_{user_id}_{file.file_id}.mp4"

        await message.bot.download_file(file.file_path, destination=str(video_path))

        # Сохраняем в S3
        s3_url = await s3_client.upload_file(
            file_path=str(video_path),
            username=username,
            filename=f"squats_{user_id}_{int(datetime.now().timestamp())}.mp4",
        )

        await message.answer("✅ Видео приседаний сохранено для анализа")
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
