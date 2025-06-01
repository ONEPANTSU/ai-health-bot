import json
import re

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.types  import ReplyKeyboardRemove

from src.bot.is_test_allowed import is_test_day_allowed
from src.bot.states import BodyQuestionnaire
from src.db.connection import get_db_connection
from src.db.patient_repository import save_patient_record

router = Router()


async def save_body_data(telegram_id: int, data: dict):
    conn = await get_db_connection()
    answers = {
        "questionnaire_type": "body_measurements",
        "prompt_type": "subjective_health",
        "waist": data["waist"],
        "hips": data["hips"],
        "chest": data["chest"],
    }

    await save_patient_record(
        conn=conn,
        telegram_id=telegram_id,
        answers=json.dumps(answers, ensure_ascii=False),  # Преобразуем в JSON строку
        gpt_response="",
        s3_links=[],
        summary="Анкета телосложения",
        is_daily=False,
    )


@router.message(Command("body_measurements"))
async def start_body_questionnaire(message: Message, state: FSMContext):
    await state.clear()
    if not await is_test_day_allowed("body"):
        await message.answer("⏳ Анкета телосложения сегодня не доступна.")
        return
    await message.answer("АНКЕТА ТЕЛОСЛОЖЕНИЯ\n\nОкружность талии (в см):",
        reply_markup=ReplyKeyboardRemove(),)
    await state.set_state(BodyQuestionnaire.WAIST)


@router.message(BodyQuestionnaire.WAIST)
async def process_waist(message: Message, state: FSMContext):
    if (
        not re.match(r"^\d{2,3}(\.\d{1,2})?$", message.text)
        or float(message.text) < 50
        or float(message.text) > 200
    ):
        await message.answer("Пожалуйста, введите корректное значение (50-200 см)")
        return

    await state.update_data(waist=float(message.text))
    await message.answer("Окружность бедер (в см):",
        reply_markup=ReplyKeyboardRemove(),)
    await state.set_state(BodyQuestionnaire.HIPS)


@router.message(BodyQuestionnaire.HIPS)
async def process_hips(message: Message, state: FSMContext):
    if (
        not re.match(r"^\d{2,3}(\.\d{1,2})?$", message.text)
        or float(message.text) < 50
        or float(message.text) > 200
    ):
        await message.answer("Пожалуйста, введите корректное значение (50-200 см)")
        return

    await state.update_data(hips=float(message.text))
    await message.answer("Окружность груди (в см):",
        reply_markup=ReplyKeyboardRemove(),)
    await state.set_state(BodyQuestionnaire.CHEST)


@router.message(BodyQuestionnaire.CHEST)
async def process_chest(message: Message, state: FSMContext):
    if (
        not re.match(r"^\d{2,3}(\.\d{1,2})?$", message.text)
        or float(message.text) < 50
        or float(message.text) > 200
    ):
        await message.answer("Пожалуйста, введите корректное значение (50-200 см)")
        return
    q_type = "body_shape"
    data = await state.get_data()
    data["questionnaire_type"] = q_type

    data["chest"] = float(message.text)
    await save_body_data(message.from_user.id, data)

    await message.answer(
        "✅ Данные телосложения сохранены:\n\n"
        f"Талия: {data['waist']} см\n"
        f"Бёдра: {data['hips']} см\n"
        f"Грудь: {data['chest']} см",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.clear()
