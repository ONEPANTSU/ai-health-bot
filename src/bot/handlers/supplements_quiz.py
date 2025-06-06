import json

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.types import ReplyKeyboardRemove

from src.bot.is_test_allowed import is_test_day_allowed
from src.bot.keyboards import get_yes_no_kb
from src.bot.states import SupplementsQuestionnaire
from src.bot.utils import send_llm_advice
from src.db.connection import get_db_connection
from src.db.patient_repository import save_patient_record

router = Router()


async def save_supplements_data(telegram_id: int, data: dict):
    conn = await get_db_connection()
    answers = {
        "questionnaire_type": "supplements",
        "prompt_type": "subjective_health",
        "taking_supplements": data["taking_supplements"],
        "supplements_details": data.get("supplements_details", ""),
    }

    await save_patient_record(
        conn=conn,
        telegram_id=telegram_id,
        answers=json.dumps(answers, ensure_ascii=False),
        gpt_response="",
        s3_links=[],
        summary="Анкета приема БАДов/витаминов",
        is_daily=False,
    )


@router.message(Command("supplements"))
async def start_supplements_questionnaire(message: Message, state: FSMContext):
    await state.clear()
    if not await is_test_day_allowed("supplements"):
        await message.answer(
            "⏳ Анкета приема БАДов/витаминов не предназначена для заполнения сегодня",
            reply_markup=ReplyKeyboardRemove(),
        )
        return
    await message.answer(
        "АНКЕТА ПРИЕМА БАДов/ВИТАМИНОВ\n\nПринимаете ли Вы витамины/БАДы регулярно?",
        reply_markup=get_yes_no_kb(),
    )
    await state.set_state(SupplementsQuestionnaire.TAKING_SUPPLEMENTS)


@router.message(SupplementsQuestionnaire.TAKING_SUPPLEMENTS)
async def process_taking_supplements(message: Message, state: FSMContext):
    if message.text not in ["Да", "Нет"]:
        await message.answer("Пожалуйста, выберите Да или Нет")
        return

    await state.update_data(taking_supplements=message.text)

    if message.text == "Да":
        await message.answer(
            "Что именно принимаете? (Перечислите названия и дозировки)",
            reply_markup=ReplyKeyboardRemove(),
        )
        await state.set_state(SupplementsQuestionnaire.SUPPLEMENTS_DETAILS)
    else:
        await state.update_data(supplements_details="")
        await finish_supplements_questionnaire(message, state)


@router.message(SupplementsQuestionnaire.SUPPLEMENTS_DETAILS)
async def process_supplements_details(message: Message, state: FSMContext):
    if len(message.text) < 3:  # Минимальная проверка на ввод
        await message.answer(
            "Пожалуйста, укажите хотя бы один препарат",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    await state.update_data(supplements_details=message.text)
    await finish_supplements_questionnaire(message, state)


async def finish_supplements_questionnaire(message: Message, state: FSMContext):
    data = await state.get_data()
    q_type = "supplements"
    data["questionnaire_type"] = q_type
    await save_supplements_data(message.from_user.id, data)

    summary = "✅ Данные о приеме БАДов/витаминов сохранены"

    if data["taking_supplements"] == "Да":
        summary += f"\nПрепараты: {data['supplements_details']}"

    await message.answer(
        summary,
        reply_markup=ReplyKeyboardRemove(),
    )
    await send_llm_advice(message, data, [])
    await state.clear()
