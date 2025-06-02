import json
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, ContentType
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from src.bot.is_test_allowed import is_task_day_allowed
from src.bot.states import BalanceTestStates
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


@router.message(Command("balance"))
async def send_balance_instructions(message: Message, state: FSMContext):
    if not await is_task_day_allowed("balance"):
        await message.answer(
            '⏳ Задание "Тест на баланс" не предназначено для прохождения сегодня'
        )
        return
    await state.set_state(BalanceTestStates.waiting_balance_video)

    s3_key = "tasks-examples/balance.mp4"
    try:
        media = await s3_client.get_media_as_buffered_file(s3_key)

        await message.answer_video(
            video=media,
            caption=(
                "<b>Баланс</b>\n"
                "Задание: «Тест на баланс на одной ноге».\n\n"
                "<b>Как выполнять:</b>\n"
                "1. Встаньте прямо, ноги вместе, руки вдоль тела\n"
                "2. Поднимите одну ногу\n"
                "3. Зафиксируйте время удержания\n"
                "4. Повторите на другой ноге\n\n"
                "<b>Что оценивается:</b>\n"
                "— Длительность удержания равновесия\n"
                "— Разница между показателями ног"
            ),
            parse_mode="HTML",
        )
    except Exception as e:
        await message.answer(f"⚠️ Не удалось загрузить медиа с инструкцией: {e}")


@router.message(
    F.content_type == ContentType.VIDEO, BalanceTestStates.waiting_balance_video
)
async def handle_balance_video(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    video = message.video
    video_path = None

    try:
        # Скачиваем видео
        file = await message.bot.get_file(video.file_id)
        video_path = temp_dir / f"balance_{user_id}_{file.file_id}.mp4"

        await message.bot.download_file(file.file_path, destination=str(video_path))

        # Сохраняем в S3
        video_name = "balance.mp4"
        video_key = await s3_client.upload_file(
            file_path=str(video_path),
            username=username,
            filename=video_name,
        )
        contact_photo_key = await extract_contact_sheet_and_upload(video_path, video_name, username)

        conn = await get_db_connection()
        answers = {
            "questionnaire_type": "balance",
            "prompt_type": "balance_tests",
        }
        await save_patient_record(
            conn=conn,
            telegram_id=user_id,
            answers=json.dumps(
                answers, ensure_ascii=False
            ),  # Преобразуем в JSON строку
            gpt_response="",
            s3_links=[video_key, contact_photo_key],
            summary="Баланс",
            is_daily=False,
        )

        await message.answer(
            "✅ Видео теста на баланс сохранено\n\n"
            "Наши специалисты проанализируют:\n"
            "- Длительность удержания на каждой ноге\n"
            "- Разницу между показателями"
        )
        await send_llm_advice(message, {}, [contact_photo_key])
        await state.clear()

    except Exception as e:
        await message.answer("❌ Ошибка при сохранении видео")
        print(f"Error: {e}")
    finally:
        if video_path and video_path.exists():
            video_path.unlink()


@router.message(
    F.content_type == ContentType.VIDEO_NOTE, BalanceTestStates.waiting_balance_video
)
async def handle_balance_video_note(message: Message):
    await message.answer(
        "Пожалуйста, отправьте видео в обычном формате, а не как видео-сообщение (кружок)"
    )
