import json
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, ContentType
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from src.bot.handlers.utils import handle_video_exception
from src.bot.is_test_allowed import is_task_day_allowed
from src.bot.states import PlankStates
from src.bot.utils import send_llm_advice
from src.db.connection import get_db_connection
from src.db.patient_repository import save_patient_record
from src.media.s3_client import S3Client
from src.media.video_processor import extract_contact_sheet_and_upload

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
    await state.clear()
    if not await is_task_day_allowed("plank"):
        await message.answer(
            '⏳ Задание "Видео в планке" не предназначено для прохождения сегодня'
        )
        return
    await state.set_state(PlankStates.waiting_plank_video)
    s3_key = "tasks-examples/plank.jpg"
    try:
        media = await s3_client.get_media_as_buffered_file(s3_key)

        await message.answer_photo(
            photo=media,
            caption="<b>Видео в планке</b>\n\n"
            "<b>Правильная техника планки:</b>\n"
            "- Плечи прямо над локтями\n"
            "- Мышцы живота напряжены\n"
            "- Касание пола: мыски ног и предплечья\n"
            "- Без прогибов в пояснице",
            parse_mode="HTML",
        )
    except Exception as e:
        await message.answer(f"⚠️ Не удалось загрузить медиа с инструкцией: {e}")


@router.message(F.content_type == ContentType.VIDEO, PlankStates.waiting_plank_video)
async def handle_plank_video(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    video = message.video
    video_path = None

    try:
        file = await message.bot.get_file(video.file_id)
        video_path = temp_dir / f"plank_{user_id}_{file.file_id}.mp4"

        await message.bot.download_file(file.file_path, destination=str(video_path))

        video_name = "plank.mp4"
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
            "questionnaire_type": "plank",
            "prompt_type": "video_analysis",
        }
        await save_patient_record(
            conn=conn,
            telegram_id=user_id,
            answers=json.dumps(answers, ensure_ascii=False),
            gpt_response="",
            s3_links=[video_key, contact_photo_key],
            summary="Планка",
            is_daily=False,
        )

        await message.answer("✅ Видео планки получено")
        await send_llm_advice(
            message, {"prompt_type": "video_analysis"}, [contact_photo_key]
        )
        await state.clear()

    except Exception as e:
        await handle_video_exception(e, message)
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
