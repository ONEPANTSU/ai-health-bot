import json
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, ContentType
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from src.bot.is_test_allowed import is_task_day_allowed
from src.bot.states import PickUpObjectStates
from src.bot.utils import send_llm_advice
from src.db.connection import get_db_connection
from src.db.patient_repository import save_patient_record
from src.media.s3_client import S3Client
from src.media.video_processor import extract_contact_sheet_and_upload

router = Router()
s3_client = S3Client()


# Путь к примеру видео
current_dir = Path(__file__).parent
example_video_path = current_dir / "examples" / "picking_up_the_object.MOV"

temp_dir = current_dir / "temp"
temp_dir.mkdir(exist_ok=True)


@router.message(Command("picking_up"))
async def send_pickup_instructions(message: Message, state: FSMContext):
    await state.clear()
    if not await is_task_day_allowed("pickup_object"):
        await message.answer(
            '⏳ Задание "Подъем с пола" не предназначено для прохождения сегодня'
        )
        return
    await state.set_state(PickUpObjectStates.waiting_pickup_video)

    s3_key = "tasks-examples/picking_up.mp4"
    try:
        media = await s3_client.get_media_as_buffered_file(s3_key)

        await message.answer_video(
            video=media,
            caption=(
                "<b>Подъем с пола</b>\n"
                "Задание: «Подъём предмета с пола (например, телефона)».\n\n"
                "<b>Инструкции:</b>\n"
                "1. Установите камеру так, чтобы в кадре было видно всё тело\n"
                "2. Положите предмет перед собой на пол\n"
                "3. Наклонитесь и поднимите предмет\n"
                "4. Встаньте обратно\n"
                "5. Выполните задание один раз\n\n"
                "<b>Обратите внимание:</b>\n"
                "— Двигайтесь в привычном темпе\n"
                "— Не торопитесь, чтобы движения были видны\n"
                "— Можно использовать любую технику (наклон или приседание)\n"
                "— Убедитесь, что вы всегда в кадре"
            ),
            parse_mode="HTML",
        )
    except Exception as e:
        await message.answer(f"⚠️ Не удалось загрузить медиа с инструкцией: {e}")


@router.message(
    F.content_type == ContentType.VIDEO, PickUpObjectStates.waiting_pickup_video
)
async def handle_pickup_video(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    video = message.video
    video_path = None

    try:
        # Скачиваем видео
        file = await message.bot.get_file(video.file_id)
        video_path = temp_dir / f"pickup_{user_id}_{file.file_id}.mp4"

        await message.bot.download_file(file.file_path, destination=str(video_path))

        video_name = "picking_up.mp4"
        video_key = await s3_client.upload_file(
            file_path=str(video_path),
            username=username,
            filename=video_name,
        )
        contact_photo_key = await extract_contact_sheet_and_upload(
            video_path, video_key, username
        )

        conn = await get_db_connection()
        answers = {
            "questionnaire_type": "picking_up",
            "prompt_type": "video_analysis",
        }
        await save_patient_record(
            conn=conn,
            telegram_id=user_id,
            answers=json.dumps(answers, ensure_ascii=False),
            gpt_response="",
            s3_links=[video_key, contact_photo_key],
            summary="Поднятие объекта",
            is_daily=False,
        )

        await message.answer("✅ Видео подъема предмета сохранено для анализа")
        await send_llm_advice(
            message, {"prompt_type": "video_analysis"}, [contact_photo_key]
        )
        await state.clear()

    except Exception as e:
        await message.answer("❌ Ошибка при сохранении видео")
        print(f"Error: {e}")
    finally:
        if video_path and video_path.exists():
            video_path.unlink()


@router.message(
    F.content_type == ContentType.VIDEO_NOTE, PickUpObjectStates.waiting_pickup_video
)
async def handle_pickup_video_note(message: Message):
    await message.answer(
        "Пожалуйста, отправьте видео в обычном формате, а не как видео-сообщение (кружок)"
    )
