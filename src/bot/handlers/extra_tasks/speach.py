import json

from aiogram.fsm.context import FSMContext
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, ContentType
from aiogram.filters import Command

from src.bot.states import SpeechVideoStates
from src.bot.utils import send_llm_advice
from src.db.connection import get_db_connection
from src.db.patient_repository import save_patient_record
from src.media.s3_client import S3Client
from src.media.video_processor import extract_contact_sheet_and_upload

router = Router()
s3_client = S3Client()

# Получаем абсолютный путь к примеру видео
current_dir = Path(__file__).parent


# Хэндлер для отправки примера видео речи
@router.message(Command("speech"))
async def send_speech_task(message: Message, state: FSMContext):
    await state.clear()

    await state.set_state(SpeechVideoStates.waiting_video)

    await message.answer(
        text="Пришлите Видео речи (1 мин) - РАССКАЗ О СЕБЕ",
        parse_mode="HTML",
    )


@router.message(F.content_type == ContentType.VIDEO, SpeechVideoStates.waiting_video)
async def handle_speech_video(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    temp_dir = current_dir / "temp"
    temp_dir.mkdir(exist_ok=True)
    video_path = temp_dir / f"{user_id}_{message.video.file_id}.mp4"

    try:
        video_file = await message.bot.get_file(message.video.file_id)

        await message.bot.download_file(video_file.file_path, destination=video_path)

        video_name = "speech.mp4"
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
            "questionnaire_type": "speech",
            "prompt_type": "video_analysis",
        }
        await save_patient_record(
            conn=conn,
            telegram_id=user_id,
            answers=json.dumps(answers, ensure_ascii=False),
            gpt_response="",
            s3_links=[video_key, contact_photo_key],
            summary="Бег",
            is_daily=False,
        )
        await message.answer("✅ Ваше видео речи успешно сохранено!\n")
        await send_llm_advice(
            message, {"prompt_type": "video_analysis"}, [contact_photo_key]
        )
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


@router.message(F.content_type == ContentType.DOCUMENT, SpeechVideoStates.waiting_video)
async def handle_speach_video_as_doc(message: Message):
    if message.document.mime_type and message.document.mime_type.startswith("video/"):
        await handle_speech_video(message)
