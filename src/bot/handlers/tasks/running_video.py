from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, ContentType
from aiogram.filters import Command
from datetime import datetime

from src.bot.is_test_allowed import is_test_day_allowed
from src.bot.states import RunningVideoStates
from src.media.s3_client import S3Client

router = Router()
s3_client = S3Client()

# Получаем абсолютный путь к примеру видео
current_dir = Path(__file__).parent
example_video_path = current_dir / "examples" / "running_video.MOV"


# Хэндлер для отправки примера видео бега
@router.message(Command("running"))
async def send_running_example(message: Message, state: FSMContext):
    if not is_test_day_allowed("running"):
        await message.answer(
            '⏳ Задание "Бег на дистанции 10-15 метров" не предназначено для прохождения сегодня'
        )
        return
    await state.set_state(RunningVideoStates.waiting_running_video)
    if not example_video_path.exists():
        await message.answer("Пример видео временно недоступен")
        return

    # Читаем файл и создаем BufferedInputFile
    with open(example_video_path, "rb") as f:
        video_data = f.read()

    video = BufferedInputFile(file=video_data, filename="running_example.MOV")

    # Отправляем видео
    await message.answer_video(
        video=video,
        caption="<b>Бег</b>\n\n"
        "Задание:<b> «Бег на дистанции 10-15 метров».</b>\n"
        "Просмотрите ролик перед тем, как начать съёмку. Убедитесь, что:\n"
        "— камера установлена стабильно и охватывает всю дистанцию,\n"
        "— в кадре видно ваше движение туда и обратно.\n"
        "Выполняйте бег в обычном для вас состоянии.",
        parse_mode="HTML",
    )


@router.message(
    F.content_type == ContentType.VIDEO, RunningVideoStates.waiting_running_video
)
async def handle_running_video(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"

    try:
        video_file = await message.bot.get_file(message.video.file_id)
        temp_dir = current_dir / "temp"
        temp_dir.mkdir(exist_ok=True)
        video_path = temp_dir / f"{user_id}_{message.video.file_id}.mp4"

        await message.bot.download_file(video_file.file_path, destination=video_path)

        s3_url = await s3_client.upload_file(
            file_path=str(video_path),
            username=username,
            filename=f"running_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
        )

        await message.answer("✅ Ваше видео с бегом успешно сохранено!\n")
        await state.clear()

    except Exception as e:
        await message.answer(
            "⚠️ Произошла ошибка при обработке вашего видео. "
            "Попробуйте отправить еще раз."
        )
        print(f"Error processing video: {e}")
    finally:
        if video_path.exists():
            video_path.unlink()


@router.message(F.content_type == ContentType.DOCUMENT)
async def handle_running_video_as_doc(message: Message):
    if message.document.mime_type and message.document.mime_type.startswith("video/"):
        await handle_running_video(message)
