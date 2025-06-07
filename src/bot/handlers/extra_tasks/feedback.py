import json

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.types import ReplyKeyboardRemove

from src.bot.states import FeedbackStates
from src.db.connection import get_db_connection
from src.db.patient_repository import save_patient_record

router = Router()


@router.message(Command("feedback"))
async def start_feedback(message: Message, state: FSMContext):
    await state.clear()

    await message.answer(
        "Напишите обратную связь в свободной текстовой форме.",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(FeedbackStates.PROCESSING)


@router.message(FeedbackStates.PROCESSING)
async def process_feedback(message: Message, state: FSMContext):
    conn = await get_db_connection()
    q_type = "feedback"

    answers = {
        "questionnaire_type": q_type,
        "data": message.text,
    }

    await save_patient_record(
        conn=conn,
        telegram_id=message.from_user.id,
        answers=json.dumps(answers, ensure_ascii=False),
        gpt_response="",
        s3_links=[],
        summary="Фидбек",
        is_daily=False,
    )

    # Формируем отчет для пользователя
    report = "✅ Обратная связь сохранены!"
    await message.answer(
        report,
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.clear()
