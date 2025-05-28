import json

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.llm_analyzer import dispatch_to_llm
from src.bot.is_test_allowed import is_test_day_allowed
from src.bot.keyboards import get_yes_no_kb, get_support_count_kb
from src.bot.states import SafetyQuestionnaire
from src.db.connection import get_db_connection
from src.db.patient_repository import save_patient_record

router = Router()


async def save_safety_data(telegram_id: int, data: dict):
    conn = await get_db_connection()
    answers = {
        "questionnaire_type": "safety_support",
        "has_support": data.get("has_support", ""),
        "support_count": data.get("support_count", ""),
        "feels_safe": data.get("feels_safe", ""),
    }

    await save_patient_record(
        conn=conn,
        telegram_id=telegram_id,
        answers=json.dumps(answers, ensure_ascii=False),
        gpt_response="",
        s3_links=[],
        summary="Анкета чувства безопасности и поддержки",
        is_daily=False,
    )
    await conn.close()


@router.message(Command("safety"))
async def start_safety_questionnaire(message: Message, state: FSMContext):
    await state.clear()
    if not is_test_day_allowed("safety"):
        await message.answer(
            "⏳ Анкета чувства безопасности и поддержки не предназначена для заполнения сегодня"
        )
        return
    await message.answer(
        "АНКЕТА ЧУВСТВА БЕЗОПАСНОСТИ И ПОДДЕРЖКИ\n\n"
        "1. Чувствуете ли Вы поддержку со стороны своего окружения?\n",
        reply_markup=get_yes_no_kb(),
    )
    await state.set_state(SafetyQuestionnaire.HAS_SUPPORT)


@router.message(SafetyQuestionnaire.HAS_SUPPORT)
async def process_has_support(message: Message, state: FSMContext):
    if message.text.lower() not in ["да", "нет"]:
        await message.answer("Пожалуйста, введите только Да или Нет")
        return

    await state.update_data(has_support=message.text.capitalize())
    await message.answer(
        "2. Сколько людей вас поддерживают эмоционально?\n",
        reply_markup=get_support_count_kb(),
    )
    await state.set_state(SafetyQuestionnaire.SUPPORT_COUNT)


@router.message(SafetyQuestionnaire.SUPPORT_COUNT)
async def process_support_count(message: Message, state: FSMContext):
    valid_answers = ["никто", "1-2 человека", "3-5 человек", "более 6 человек"]
    if message.text.lower() not in valid_answers:
        await message.answer(
            "Пожалуйста, выберите один из вариантов:\n"
            "Никто, 1-2 человека, 3-5 человек, Более 6 человек"
        )
        return

    await state.update_data(support_count=message.text.capitalize())
    await message.answer(
        "3. Ощущаете ли Вы себя в безопасности среди своего окружения?\n",
        reply_markup=get_yes_no_kb(),
    )
    await state.set_state(SafetyQuestionnaire.FEELS_SAFE)


@router.message(SafetyQuestionnaire.FEELS_SAFE)
async def process_feels_safe(message: Message, state: FSMContext):
    if message.text.lower() not in ["да", "нет"]:
        await message.answer("Пожалуйста, введите только Да или Нет")
        return

    await state.update_data(feels_safe=message.text.capitalize())
    data = await state.get_data()
    q_type = "safety_support"
    data["questionnaire_type"] = q_type

    # Сохраняем результаты
    conn = await get_db_connection()
    try:
        await save_patient_record(
            conn=conn,
            telegram_id=message.from_user.id,
            answers=json.dumps(data, ensure_ascii=False),
            gpt_response="",
            s3_links=[],
            summary="Анкета безопасности и поддержки",
            is_daily=False,
        )
    finally:
        await conn.close()

    # Формируем отчет
    report = (
        "✅ Результаты анкеты:\n\n"
        f"1. Поддержка окружения: {data['has_support']}\n"
        f"2. Количество поддерживающих: {data['support_count']}\n"
        f"3. Чувство безопасности: {data['feels_safe']}"
    )

    await message.answer(report)
    try:
        llm_response = await dispatch_to_llm(
            username=message.from_user.username or message.from_user.full_name,
            telegram_id=message.from_user.id,
            current_record={
                "questionnaire_type": q_type,
                "answers": data
            },
            media_urls=[]
        )
        await message.answer(f"🤖 Рекомендации от AI:\n\n{llm_response}")
    except Exception as e:
        await message.answer(f"⚠️ Не удалось получить рекомендации от AI:\n{e}")
    await state.clear()
