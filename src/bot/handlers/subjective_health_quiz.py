import json

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.bot.is_test_allowed import is_test_day_allowed
from src.bot.keyboards import get_yes_no_kb
from src.bot.states import HealthQuestionnaire
from src.db.connection import get_db_connection
from src.db.patient_repository import save_patient_record

router = Router()


async def save_health_data(telegram_id: int, data: dict):
    conn = await get_db_connection()
    answers = {
        "questionnaire_type": "health_status",
        "chronic_diseases": data.get("chronic_diseases"),
        "diseases_details": data.get("diseases_details", ""),
        "medication": data.get("medication"),
        "medication_details": data.get("medication_details", ""),
        "chronic_pain": data.get("chronic_pain"),
        "pain_details": data.get("pain_details", ""),
    }

    await save_patient_record(
        conn=conn,
        telegram_id=telegram_id,
        answers=json.dumps(answers, ensure_ascii=False),
        gpt_response="",
        s3_links=[],
        summary="Анкета состояния здоровья",
        is_daily=False,
    )


@router.message(Command("start_health_questionnaire"))
async def start_health_questionnaire(message: Message, state: FSMContext):
    if not is_test_day_allowed("health"):
        await message.answer(
            "⏳ Анкета субъективного состояния здоровья не предназначена для заполнения сегодня"
        )
        return
    await message.answer(
        "АНКЕТА СУБЪЕКТИВНОГО СОСТОЯНИЯ ЗДОРОВЬЯ\n\n"
        "Есть ли у вас хронические заболевания?",
        reply_markup=get_yes_no_kb(),
    )
    await state.set_state(HealthQuestionnaire.CHRONIC_DISEASES)


@router.message(HealthQuestionnaire.CHRONIC_DISEASES)
async def process_chronic_diseases(message: Message, state: FSMContext):
    if message.text not in ["Да", "Нет"]:
        await message.answer("Пожалуйста, выберите Да или Нет")
        return

    await state.update_data(chronic_diseases=message.text)

    if message.text == "Да":
        await message.answer("Если хронические заболевания есть, то какие?")
        await state.set_state(HealthQuestionnaire.DISEASES_DETAILS)
    else:
        await state.update_data(diseases_details="")
        await message.answer(
            "Принимаете ли Вы какие-либо лекарственные препараты на постоянной основе?",
            reply_markup=get_yes_no_kb(),
        )
        await state.set_state(HealthQuestionnaire.MEDICATION)


@router.message(HealthQuestionnaire.DISEASES_DETAILS)
async def process_diseases_details(message: Message, state: FSMContext):
    await state.update_data(diseases_details=message.text)
    await message.answer(
        "Принимаете ли Вы какие-либо лекарственные препараты на постоянной основе?",
        reply_markup=get_yes_no_kb(),
    )
    await state.set_state(HealthQuestionnaire.MEDICATION)


@router.message(HealthQuestionnaire.MEDICATION)
async def process_medication(message: Message, state: FSMContext):
    if message.text not in ["Да", "Нет"]:
        await message.answer("Пожалуйста, выберите Да или Нет")
        return

    await state.update_data(medication=message.text)

    if message.text == "Да":
        await message.answer("Если да, то какие?")
        await state.set_state(HealthQuestionnaire.MEDICATION_DETAILS)
    else:
        await state.update_data(medication_details="")
        await message.answer(
            "Есть ли у вас постоянные боли (например, спина, шея, суставы)?",
            reply_markup=get_yes_no_kb(),
        )
        await state.set_state(HealthQuestionnaire.CHRONIC_PAIN)


@router.message(HealthQuestionnaire.MEDICATION_DETAILS)
async def process_medication_details(message: Message, state: FSMContext):
    await state.update_data(medication_details=message.text)
    await message.answer(
        "Есть ли у вас постоянные боли (например, спина, шея, суставы)?",
        reply_markup=get_yes_no_kb(),
    )
    await state.set_state(HealthQuestionnaire.CHRONIC_PAIN)


@router.message(HealthQuestionnaire.CHRONIC_PAIN)
async def process_chronic_pain(message: Message, state: FSMContext):
    if message.text not in ["Да", "Нет"]:
        await message.answer("Пожалуйста, выберите Да или Нет")
        return

    await state.update_data(chronic_pain=message.text)

    if message.text == "Да":
        await message.answer("Если есть, то где именно?")
        await state.set_state(HealthQuestionnaire.PAIN_DETAILS)
    else:
        await state.update_data(pain_details="")
        await finish_health_questionnaire(message, state)


@router.message(HealthQuestionnaire.PAIN_DETAILS)
async def process_pain_details(message: Message, state: FSMContext):
    await state.update_data(pain_details=message.text)
    await finish_health_questionnaire(message, state)


async def finish_health_questionnaire(message: Message, state: FSMContext):
    data = await state.get_data()
    data["questionnaire_type"] = "subjective_health"

    await save_health_data(message.from_user.id, data)

    summary = (
        "✅ Анкета состояния здоровья сохранена:\n\n"
        f"Хронические заболевания: {data['chronic_diseases']}\n"
    )

    if data["chronic_diseases"] == "Да":
        summary += f"Подробности: {data['diseases_details']}\n"

    summary += f"Приём лекарств: {data['medication']}\n"

    if data["medication"] == "Да":
        summary += f"Какие: {data['medication_details']}\n"

    summary += f"Постоянные боли: {data['chronic_pain']}\n"

    if data["chronic_pain"] == "Да":
        summary += f"Локализация: {data['pain_details']}"

    await message.answer(summary)
    await state.clear()
