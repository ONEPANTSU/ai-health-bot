import json

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.types import ReplyKeyboardRemove

from src.bot.states import DeviceData, MindfulnessQuestionnaire
from src.bot.utils import send_llm_advice
from src.db.connection import get_db_connection
from src.db.patient_repository import save_patient_record

router = Router()

@router.message(Command("wearable_data"))
async def start_device_data(message: Message, state: FSMContext):
    await state.clear()

    await message.answer(
        "Пришлите данные с носимого устройства за последний месяц в свободной текстовой форме.",
        reply_markup=ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Нет")],
        ],
        resize_keyboard=True,
    ),
    )
    await state.set_state(MindfulnessQuestionnaire.HAS_PRACTICE)


@router.message(DeviceData.PROCESSING)
async def process_device_data(message: Message, state: FSMContext):

    conn = await get_db_connection()
    q_type = "device"

    answers = {
        "questionnaire_type": q_type,
        "prompt_type": "wearable_data",
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
    report = (
        "✅ Анкета сохранена!"
    )
    await message.answer(
        report,
        reply_markup=ReplyKeyboardRemove(),
    )
    await send_llm_advice(message, answers, [])
    await state.clear()