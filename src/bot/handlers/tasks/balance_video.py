from datetime import datetime
from aiogram.types import BufferedInputFile
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, ContentType
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from src.bot.is_test_allowed import is_test_day_allowed
from src.bot.states import BalanceTestStates
from src.media.s3_client import S3Client

router = Router()
s3_client = S3Client()


# Путь к примеру видео
current_dir = Path(__file__).parent
example_video_path = current_dir / "examples" / "balance.MOV"

temp_dir = current_dir / "temp"
temp_dir.mkdir(exist_ok=True)


@router.message(Command("balance_test_instructions"))
async def send_balance_instructions(message: Message, state: FSMContext):
    if not is_test_day_allowed("balance"):
        await message.answer(
            '⏳ Задание "Тест на баланс" не предназначено для прохождения сегодня'
        )
        return
    await state.set_state(BalanceTestStates.waiting_balance_video)

    s3_key = "tasks-examples/balance/balance.mp4"
    try:
        video = await s3_client.get_video_as_buffered_file(s3_key)

        await message.answer_video(
            video=video,
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
        await message.answer(f"⚠️ Не удалось загрузить видео с инструкцией: {e}")


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
        s3_url = await s3_client.upload_file(
            file_path=str(video_path),
            username=username,
            filename=f"balance_{user_id}_{int(datetime.now().timestamp())}.mp4",
        )

        await message.answer(
            "✅ Видео теста на баланс сохранено\n\n"
            "Наши специалисты проанализируют:\n"
            "- Длительность удержания на каждой ноге\n"
            "- Разницу между показателями"
        )
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
