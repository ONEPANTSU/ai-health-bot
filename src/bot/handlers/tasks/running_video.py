import json

from aiogram.fsm.context import FSMContext
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, ContentType
from aiogram.filters import Command

from src.bot.is_test_allowed import is_task_day_allowed
from src.bot.states import RunningVideoStates
from src.db.connection import get_db_connection
from src.db.patient_repository import save_patient_record
from src.media.s3_client import S3Client

router = Router()
s3_client = S3Client()

# Получаем абсолютный путь к примеру видео
current_dir = Path(__file__).parent
example_video_path = current_dir / "examples" / "running_video.MOV"


# Хэндлер для отправки примера видео бега
@router.message(Command("running"))
async def send_running_example(message: Message, state: FSMContext):
    if not await is_task_day_allowed("running"):
        await message.answer(
            '⏳ Задание "Бег на дистанции 10-15 метров" не предназначено для прохождения сегодня'
        )
        return
    await state.set_state(RunningVideoStates.waiting_running_video)

    s3_key = "tasks-examples/running.mp4"
    try:
        media = await s3_client.get_media_as_buffered_file(s3_key)

        await message.answer_video(
            video=media,
            caption="<b>Бег</b>\n\n"
            "Задание:<b> «Бег на дистанции 10-15 метров».</b>\n"
            "Просмотрите ролик перед тем, как начать съёмку. Убедитесь, что:\n"
            "— камера установлена стабильно и охватывает всю дистанцию,\n"
            "— в кадре видно ваше движение туда и обратно.\n"
            "Выполняйте бег в обычном для вас состоянии.",
            parse_mode="HTML",
        )
    except Exception as e:
        await message.answer(f"⚠️ Не удалось загрузить медиа с инструкцией: {e}")


@router.message(
    F.content_type == ContentType.VIDEO, RunningVideoStates.waiting_running_video
)
async def handle_running_video(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    temp_dir = current_dir / "temp"
    temp_dir.mkdir(exist_ok=True)
    video_path = temp_dir / f"{user_id}_{message.video.file_id}.mp4"

    try:
        video_file = await message.bot.get_file(message.video.file_id)

        await message.bot.download_file(video_file.file_path, destination=video_path)

        s3_url = await s3_client.upload_file(
            file_path=str(video_path),
            username=username,
            filename="running.mp4",
        )
        conn = await get_db_connection()
        answers = {
            "questionnaire_type": "running",
            "prompt_type": "video_analysis",
        }
        await save_patient_record(
            conn=conn,
            telegram_id=user_id,
            answers=json.dumps(answers, ensure_ascii=False),
            gpt_response="",
            s3_links=[s3_url],
            summary="Бег",
            is_daily=False,
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
