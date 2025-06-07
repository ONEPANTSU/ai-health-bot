import json
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, ContentType
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from src.bot.states import ExaminationStates
from src.bot.utils import send_llm_advice
from src.db.connection import get_db_connection
from src.db.patient_repository import save_patient_record
from src.media.s3_client import S3Client

router = Router()
s3_client = S3Client()

current_dir = Path(__file__).parent
temp_dir = current_dir / "temp"
temp_dir.mkdir(exist_ok=True)


@router.message(Command("checkups"))
async def request_examination_files(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(ExaminationStates.waiting_examination_files)
    await message.answer(
        "📁 Пожалуйста, отправьте файлы с медицинскими обследованиями (анализы, снимки, заключения) "
        "за последние месяцы. Можно отправлять несколько файлов подряд.\n\n"
        "Поддерживаются файлы любых форматов: PDF, JPG, PNG, DOCX и другие."
    )


@router.message(
    F.content_type.in_(
        {
            ContentType.DOCUMENT,
            ContentType.PHOTO,
            ContentType.VIDEO,
            ContentType.AUDIO,
            ContentType.VOICE,
        }
    ),
    ExaminationStates.waiting_examination_files,
)
async def handle_examination_files(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    file_path = None

    try:
        if message.document:
            file = message.document
        elif message.photo:
            file = message.photo[-1]
        elif message.video:
            file = message.video
        elif message.audio:
            file = message.audio
        elif message.voice:
            file = message.voice
        else:
            await message.answer("❌ Неподдерживаемый тип файла")
            return

        file_info = await message.bot.get_file(file.file_id)
        file_ext = Path(file_info.file_path).suffix if file_info.file_path else ".dat"
        file_path = temp_dir / f"checkup_{user_id}_{file.file_id}{file_ext}"

        await message.bot.download_file(file_info.file_path, destination=str(file_path))

        original_filename = (
            file.file_name
            if hasattr(file, "file_name")
            else f"checkup_{file.file_id}{file_ext}"
        )
        s3_key = await s3_client.upload_file(
            file_path=str(file_path),
            username=username,
            filename=f"checkup/{original_filename}",
        )

        conn = await get_db_connection()
        answers = {"questionnaire_type": "checkup", "prompt_type": "blood_tests"}

        await save_patient_record(
            conn=conn,
            telegram_id=user_id,
            answers=json.dumps(answers, ensure_ascii=False),
            gpt_response="",
            s3_links=[s3_key],
            summary=f"Медицинское обследование: {original_filename}",
            is_daily=False,
        )

        await message.answer(f"✅ Файл '{original_filename}' успешно сохранен!")
        await send_llm_advice(message, {"prompt_type": "blood_tests"}, [s3_key])
        await state.clear()

    except Exception as e:
        await message.answer("❌ Ошибка при сохранении файла")
        print(f"Error: {e}")
    finally:
        if file_path and file_path.exists():
            file_path.unlink()
        await state.clear()


@router.message(ExaminationStates.waiting_examination_files)
async def handle_wrong_examination_input(message: Message):
    if message.content_type not in {
        ContentType.DOCUMENT,
        ContentType.PHOTO,
        ContentType.VIDEO,
        ContentType.AUDIO,
        ContentType.VOICE,
    }:
        await message.answer("Пожалуйста, отправьте файл с медицинским обследованием")
