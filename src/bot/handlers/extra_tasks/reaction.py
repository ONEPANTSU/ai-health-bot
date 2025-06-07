import json

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.types import ReplyKeyboardRemove

from src.bot.states import ReactionStates
from src.bot.utils import send_llm_advice
from src.db.connection import get_db_connection
from src.db.patient_repository import save_patient_record

router = Router()


@router.message(Command("reaction"))
async def start_reaction(message: Message, state: FSMContext):
    await state.clear()

    await message.answer(
        "Пройдите тест на реакцию https://www.arealme.com/reaction-test/ru/ "
        "<br>И пришлите свою среднюю скорость реакции (в мс).",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(ReactionStates.PROCESSING)


@router.message(ReactionStates.PROCESSING)
async def process_reaction(message: Message, state: FSMContext):
    conn = await get_db_connection()
    q_type = "reaction"

    answers = {
        "questionnaire_type": q_type,
        "prompt_type": "balance_tests",
        "data": message.text,
    }

    await save_patient_record(
        conn=conn,
        telegram_id=message.from_user.id,
        answers=json.dumps(answers, ensure_ascii=False),
        gpt_response="",
        s3_links=[],
        summary="Данные с носимого устройства",
        is_daily=False,
    )

    # Формируем отчет для пользователя
    report = "✅ Данные сохранены!"
    await message.answer(
        report,
        reply_markup=ReplyKeyboardRemove(),
    )
    await send_llm_advice(message, answers, [])
    await state.clear()
