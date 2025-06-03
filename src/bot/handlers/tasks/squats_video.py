import json
from aiogram.fsm.context import FSMContext
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, ContentType
from aiogram.filters import Command

from src.bot.is_test_allowed import is_task_day_allowed
from src.bot.states import SquatsVideoStates
from src.bot.utils import send_llm_advice
from src.db.connection import get_db_connection
from src.db.patient_repository import save_patient_record
from src.media.s3_client import S3Client
from src.media.video_processor import extract_contact_sheet_and_upload

router = Router()
s3_client = S3Client()

# Путь к примеру видео
current_dir = Path(__file__).parent
example_squats_video = current_dir / "examples" / "squats.MOV"

temp_dir = current_dir / "temp"
temp_dir.mkdir(exist_ok=True)


@router.message(Command("squats"))
async def send_squats_instructions(message: Message, state: FSMContext):
    await state.clear()
    if not await is_task_day_allowed("squats"):
        await message.answer(
            '⏳ Задание "10 приседаний" не предназначено для прохождения сегодня'
        )
        return
    await state.set_state(SquatsVideoStates.waiting_squats_video)

    s3_key = "tasks-examples/squats.mp4"
    try:
        media = await s3_client.get_media_as_buffered_file(s3_key)

        await message.answer_video(
            video=media,
            caption=(
                "<b>Приседания</b>\n"
                "Задание: «10 приседаний».\n\n"
                "Перед тем как начать съёмку, внимательно посмотрите видеоинструкцию. Убедитесь, что:\n"
                "— камера установлена стабильно и снимает вас в полный рост,\n"
                "— вас хорошо видно на протяжении всего выполнения упражнения,\n"
                "— вы выполняете 10 приседаний подряд без пауз и остановок,\n"
                "— приседайте в своём обычном, комфортном темпе.\n\n"
                "Старайтесь держать спину прямо, опускаясь до уровня, при котором бёдра параллельны полу. "
                "Колени не должны выходить за пределы носков."
            ),
            parse_mode="HTML",
        )
    except Exception as e:
        await message.answer(f"⚠️ Не удалось загрузить медиа с инструкцией: {e}")


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

        video_name = "squats.mp4"
        video_key = await s3_client.upload_file(
            file_path=str(video_path),
            username=username,
            filename=video_name,
        )
        contact_photo_key = await extract_contact_sheet_and_upload(
            video_path, video_name, username
        )

        conn = await get_db_connection()
        answers = {
            "questionnaire_type": "squats",
            "prompt_type": "video_analysis",
        }
        await save_patient_record(
            conn=conn,
            telegram_id=user_id,
            answers=json.dumps(answers, ensure_ascii=False),
            gpt_response="",
            s3_links=[video_key, contact_photo_key],
            summary="Приседания",
            is_daily=False,
        )

        await message.answer("✅ Видео приседаний сохранено для анализа")
        await send_llm_advice(message, {}, [contact_photo_key])
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
