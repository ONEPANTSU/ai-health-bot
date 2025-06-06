import json
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, ContentType
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from src.bot.is_test_allowed import is_task_day_allowed
from src.bot.states import LaughterVideoStates
from src.bot.utils import send_llm_advice
from src.db.connection import get_db_connection
from src.db.patient_repository import save_patient_record
from src.media.s3_client import S3Client
from src.media.video_processor import extract_contact_sheet_and_upload

router = Router()
s3_client = S3Client()

current_dir = Path(__file__).parent
temp_dir = current_dir / "temp"
temp_dir.mkdir(exist_ok=True)


@router.message(Command("laughter"))
async def send_laughter_instructions(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(None)

    if not await is_task_day_allowed("laughter_video"):
        await message.answer(
            '⏳ Задание "Видео смеха/улыбки" не предназначено для прохождения сегодня'
        )
        return
    await state.set_state(LaughterVideoStates.waiting_laughter_video)

    try:
        await message.answer(
            text=(
                "<b>Видео естественного смеха/улыбки</b>\n\n"
                "<b>Инструкция:</b>\n"
                "1. Снимите 15-секундное видео своего естественного смеха или улыбки\n"
                "2. Можно вспомнить что-то смешное или посмотреть веселый ролик\n"
                "3. Важно сохранять естественное выражение лица\n\n"
                "<b>Требования к видео:</b>\n"
                "— Минимальная длительность 15 секунд\n"
                "— Лицо должно быть хорошо видно\n"
                "— Естественное освещение без резких теней\n"
                "— Камера на уровне лица\n\n"
            ),
            parse_mode="HTML",
        )
    except Exception as e:
        await message.answer(f"⚠️ Не удалось загрузить медиа с инструкцией: {e}")


@router.message(
    F.content_type == ContentType.VIDEO, LaughterVideoStates.waiting_laughter_video
)
async def handle_laughter_video(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    video = message.video
    video_path = None

    try:
        file = await message.bot.get_file(video.file_id)
        video_path = temp_dir / f"laughter_{user_id}_{file.file_id}.mp4"

        await message.bot.download_file(file.file_path, destination=str(video_path))

        video_name = "laughter.mp4"
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
            "questionnaire_type": "smile/laughter",
            "prompt_type": "video_analysis",
        }
        await save_patient_record(
            conn=conn,
            telegram_id=user_id,
            answers=json.dumps(answers, ensure_ascii=False),
            gpt_response="",
            s3_links=[video_key, contact_photo_key],
            summary="Видео смеха/улыбки",
            is_daily=False,
        )

        await message.answer("✅ Видео смеха/улыбки сохранено для анализа")
        await send_llm_advice(
            message,
            {
                "prompt_type": "video_analysis",
            },
            [contact_photo_key],
        )
        await state.clear()

    except Exception as e:
        await message.answer("❌ Ошибка при сохранении видео")
        print(f"Error processing laughter video: {e}")
    finally:
        if video_path and video_path.exists():
            video_path.unlink()


@router.message(
    F.content_type == ContentType.VIDEO_NOTE, LaughterVideoStates.waiting_laughter_video
)
async def handle_laughter_video_note(message: Message):
    await message.answer(
        "Пожалуйста, отправьте видео в обычном формате, а не как видео-сообщение (кружок)"
    )
