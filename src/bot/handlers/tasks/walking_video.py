from datetime import datetime
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, ContentType
from aiogram.filters import Command

from src.bot.is_test_allowed import is_task_day_allowed
from src.bot.states import WalkingVideoStates
from src.media.s3_client import S3Client

router = Router()
s3_client = S3Client()

# Пути к примерам видео
current_dir = Path(__file__).parent
example_walking_video = current_dir / "examples" / "walking_example.MOV"

temp_dir = current_dir / "temp"
temp_dir.mkdir(exist_ok=True)


@router.message(Command("walking"))
async def send_walking_instructions(message: Message, state: FSMContext):
    if not await is_task_day_allowed("walking"):
        await message.answer(
            '⏳ Задание "Ходьба" не предназначено для прохождения сегодня'
        )
        return
    await state.set_state(WalkingVideoStates.waiting_walking_video)
    if not example_walking_video.exists():
        await message.answer(
            "<b>Ходьба</b>\n"
            "Задание: ходьба вперёд и назад на расстояние примерно 10 метров босиком\n\n"
            "Описание:\n"
            "Упражнение необходимо выполнить в помещении — дома, в коридоре, комнате или другом закрытом пространстве.\n"
            "Важно: ходьба выполняется босиком, на ровной, безопасной поверхности.\n"
            "Точное измерение 10 метров не требуется — ориентируйтесь на примерно 12–15 шагов в одну сторону.\n\n"
            "Как выполнять:\n"
            "1. Разуйтесь и встаньте в начале выбранного маршрута.\n"
            "2. Пройдите спокойным шагом вперёд примерно 10 метров (12–15 шагов).\n"
            "3. Развернитесь и вернитесь обратно тем же шагом.\n"
            "4. Двигайтесь в ровном, естественном для себя темпе.\n"
            "5. Сохраняйте обычную походку, без изменения осанки.\n"
            "6. Запишите выполнение упражнения на видео.\n\n"
            "Обязательные условия:\n"
            "— Упражнение выполняется только в помещении.\n"
            "— Поверхность должна быть ровной, сухой и безопасной для ходьбы босиком.\n"
            "— В кадре должно быть видно всё движение — туда и обратно.\n"
            "— Съёмка может быть вертикальной или горизонтальной.",
            parse_mode="HTML",
        )
        return

    # Отправляем видео с инструкцией
    with open(example_walking_video, "rb") as f:
        video = BufferedInputFile(f.read(), filename=example_walking_video.name)

        await message.answer_video(
            video=video,
            caption=(
                "<b>Ходьба</b>\n"
                "Задание: ходьба вперёд и назад на расстояние примерно 10 метров босиком\n\n"
                "Описание:\n"
                "Упражнение необходимо выполнить в помещении — дома, в коридоре, комнате или другом закрытом пространстве.\n"
                "Важно: ходьба выполняется босиком, на ровной, безопасной поверхности.\n"
                "Точное измерение 10 метров не требуется — ориентируйтесь на примерно 12–15 шагов в одну сторону.\n\n"
                "Как выполнять:\n"
                "1. Разуйтесь и встаньте в начале выбранного маршрута.\n"
                "2. Пройдите спокойным шагом вперёд примерно 10 метров (12–15 шагов).\n"
                "3. Развернитесь и вернитесь обратно тем же шагом.\n"
                "4. Двигайтесь в ровном, естественном для себя темпе.\n"
                "5. Сохраняйте обычную походку, без изменения осанки.\n"
                "6. Запишите выполнение упражнения на видео.\n\n"
                "Обязательные условия:\n"
                "— Упражнение выполняется только в помещении.\n"
                "— Поверхность должна быть ровной, сухой и безопасной для ходьбы босиком.\n"
                "— В кадре должно быть видно всё движение — туда и обратно.\n"
                "— Съёмка может быть вертикальной или горизонтальной."
            ),
            parse_mode="HTML",
        )


@router.message(
    F.content_type == ContentType.VIDEO, WalkingVideoStates.waiting_walking_video
)
async def handle_walking_video(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    video = message.video
    video_path = None

    try:
        # Скачиваем видео
        file = await message.bot.get_file(video.file_id)
        video_path = temp_dir / f"walking_{user_id}_{file.file_id}.mp4"

        await message.bot.download_file(file.file_path, destination=str(video_path))

        # Сохраняем в S3
        s3_url = await s3_client.upload_file(
            file_path=str(video_path),
            username=username,
            filename=f"walking_{user_id}_{int(datetime.now().timestamp())}.mp4",
        )

        await message.answer("✅ Видео ходьбы сохранено для анализа")
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
