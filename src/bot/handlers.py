from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from src.db.connection import get_db_connection
from src.db.patient_repository import create_patient

router = Router()


@router.message(CommandStart())
async def handle_start(msg: Message, state: FSMContext):
    conn = await get_db_connection()

    await create_patient(
        conn,
        telegram_id=msg.from_user.id,
        username=msg.from_user.username,
        full_name=msg.from_user.full_name
    )

    await msg.answer("👋 Привет! Ты зарегистрирован. Готов к приёму анкеты и медиа.")
    await conn.close()
