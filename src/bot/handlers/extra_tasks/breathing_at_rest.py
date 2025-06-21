import json
import logging
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, ContentType
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from src.bot.is_test_allowed import is_task_day_allowed
from src.bot.states import RestBreathingStates
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


@router.message(Command("rest_breathing"))
async def send_rest_breathing_instructions(message: Message, state: FSMContext):
    await state.clear()
    if not await is_task_day_allowed("rest_breathing"):
        await message.answer(
            '⏳ Задание "Дыхание в покое" не предназначено для прохождения сегодня'
        )
        return
    await state.set_state(RestBreathingStates.waiting_rest_breathing_video)

    try:
        await message.answer(
            text=(
                "<b>Дыхание в покое</b>\n\n"
                "<b>Инструкция:</b>\n"
                "1. Сядьте в удобное положение или лягте\n"
                "2. Успокойтесь и дышите естественно\n"
                "3. Запишите 2-минутное видео своего дыхания\n\n"
                "<b>Требования к видео:</b>\n"
                "— Камера должна быть направлена на верхнюю часть тела\n"
                "— Грудная клетка должна быть хорошо видна\n"
                "— Минимальная длительность - 2 минуты\n\n"
                "<b>Важно:</b>\n"
                "— Не разговаривайте во время записи\n"
                "— Старайтесь не двигаться\n"
                "— Дышите естественно, не контролируйте дыхание специально"
            ),
            parse_mode="HTML",
        )
    except Exception as e:
        await message.answer(f"⚠️ Не удалось загрузить медиа с инструкцией: {e}")


@router.message(
    F.content_type == ContentType.VIDEO,
    RestBreathingStates.waiting_rest_breathing_video,
)
async def handle_rest_breathing_video(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    video = message.video
    video_path = None

    try:

        file = await message.bot.get_file(video.file_id)
        video_path = temp_dir / f"rest_breathing_{user_id}_{file.file_id}.mp4"

        await message.bot.download_file(file.file_path, destination=str(video_path))

        video_name = "rest_breathing.mp4"
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
            "questionnaire_type": "rest_breathing",
            "prompt_type": "video_analysis",
        }
        await save_patient_record(
            conn=conn,
            telegram_id=user_id,
            answers=json.dumps(answers, ensure_ascii=False),
            gpt_response="",
            s3_links=[video_key, contact_photo_key],
            summary="Дыхание в покое",
            is_daily=False,
        )

        await message.answer("✅ Видео дыхания в покое сохранено")
        await send_llm_advice(
            message,
            {
                "prompt_type": "video_analysis",
            },
            [contact_photo_key],
        )
        await state.clear()
    except Exception as e:
        if "file is too big" in str(e):
            await message.answer("""
            📏 <strong>Размер видео превышает 200 МБ.</strong>\n
            Пожалуйста, уменьшите размер файла, например, используя один из следующих онлайн-инструментов:\n
            <ul>
                <li><a href="https://www.freeconvert.com/video-compressor" target="_blank">FreeConvert</a></li>
                <li><a href="https://www.compress2go.com/compress-video" target="_blank">Compress2Go</a></li>
                <li><a href="https://www.capcut.com/tools/free-video-compressor" target="_blank">CapCut</a></li>
            </ul>
            После сжатия отправьте видео снова, и я с радостью продолжу обработку.\n
            """)
        else:
            await message.answer("❌ Ошибка при сохранении видео")
        logging.error(f"Error: {e}")
    finally:
        if video_path and video_path.exists():
            video_path.unlink()


@router.message(
    F.content_type == ContentType.VIDEO_NOTE,
    RestBreathingStates.waiting_rest_breathing_video,
)
async def handle_rest_breathing_video_note(message: Message):
    await message.answer(
        "Пожалуйста, отправьте видео в обычном формате, а не как видео-сообщение (кружок)"
    )
