from datetime import datetime
from aiogram.types import BufferedInputFile
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, ContentType
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from src.bot.is_test_allowed import is_test_day_allowed
from src.bot.states import PickUpObjectStates
from src.s3_client import S3Client

router = Router()
s3_client = S3Client()


# Путь к примеру видео
current_dir = Path(__file__).parent
example_video_path = current_dir / "examples" / "picking_up_the_object.MOV"

temp_dir = current_dir / "temp"
temp_dir.mkdir(exist_ok=True)


@router.message(Command("pickup_object_instructions"))
async def send_pickup_instructions(message: Message, state: FSMContext):
    if not is_test_day_allowed("pickup_object"):
        await message.answer(
            '⏳ Задание "Подъем с пола" не предназначено для прохождения сегодня'
        )
        return
    await state.set_state(PickUpObjectStates.waiting_pickup_video)

    if not example_video_path.exists():
        await message.answer(
            "<b>Подъем с пола</b>\n"
            "Задание: «Подъём предмета с пола (например, телефона)».\n\n"
            "В этом задании вам нужно записать, как вы поднимаете предмет с пола.\n\n"
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
            "— Убедитесь, что вы всегда в кадре",
            parse_mode="HTML",
        )
        return

    # Отправляем видео с инструкцией
    with open(example_video_path, "rb") as f:
        video = BufferedInputFile(f.read(), filename=example_video_path.name)

        await message.answer_video(
            video=video,
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

        # Сохраняем в S3
        s3_url = await s3_client.upload_file(
            file_path=str(video_path),
            username=username,
            filename=f"pickup_{user_id}_{int(datetime.now().timestamp())}.mp4",
        )

        await message.answer(
            "✅ Видео подъема предмета сохранено для анализа\n\n"
            "Наши специалисты изучат ваши движения и дадут рекомендации."
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
