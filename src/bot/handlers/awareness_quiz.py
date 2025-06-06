import json

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.types import ReplyKeyboardRemove

from src.bot.is_test_allowed import is_test_day_allowed
from src.bot.keyboards import (
    get_yes_no_kb,
    get_frequency_communication_kb,
    get_difficulty_kb,
)
from src.bot.states import MindfulnessQuestionnaire
from src.bot.utils import send_llm_advice
from src.db.connection import get_db_connection
from src.db.patient_repository import save_patient_record

router = Router()


async def finish_questionnaire(message: Message, state: FSMContext, data: dict):
    conn = await get_db_connection()
    q_type = "mindfulness"

    answers = {
        "questionnaire_type": q_type,
        "prompt_type": "subjective_health",
        "has_practice": data.get("has_practice", "Нет"),
        "practice_frequency": data.get("practice_frequency", ""),
        "focus_object": data.get("focus_object", ""),
        "concentration_difficulty": data.get("concentration_difficulty", ""),
        "positive_changes": data.get("positive_changes", ""),
    }

    await save_patient_record(
        conn=conn,
        telegram_id=message.from_user.id,
        answers=json.dumps(answers, ensure_ascii=False),
        gpt_response="",
        s3_links=[],
        summary="Анкета уровня осознанности",
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
    await send_llm_advice(message, data, [])
    await state.clear()


@router.message(Command("mindfulness"))
async def start_mindfulness_questionnaire(message: Message, state: FSMContext):
    await state.clear()
    if not await is_test_day_allowed("mindfulness"):
        await message.answer("⏳ Анкета осознанности сегодня не доступна.")
        return

    await message.answer(
        "АНКЕТА НА УРОВЕНЬ ОСОЗНАННОСТИ\n\n1. Практикуете ли Вы какие-либо медитации?",
        reply_markup=get_yes_no_kb(),
    )
    await state.set_state(MindfulnessQuestionnaire.HAS_PRACTICE)


@router.message(MindfulnessQuestionnaire.HAS_PRACTICE)
async def process_has_practice(message: Message, state: FSMContext):
    if message.text not in ["Да", "Нет"]:
        await message.answer("Пожалуйста, выберите вариант из клавиатуры")
        return

    await state.update_data(has_practice=message.text)

    if message.text == "Нет":
        # Пропускаем вопросы для не практикующих
        data = await state.get_data()
        await finish_questionnaire(message, state, data)
    else:
        await message.answer(
            "2. Как часто Вы практикуете медитации?",
            reply_markup=get_frequency_communication_kb(),
        )
        await state.set_state(MindfulnessQuestionnaire.PRACTICE_FREQUENCY)


@router.message(MindfulnessQuestionnaire.PRACTICE_FREQUENCY)
async def process_practice_frequency(message: Message, state: FSMContext):
    valid_answers = ["Каждый день", "Несколько раз в неделю", "Раз в неделю", "Реже"]
    if message.text not in valid_answers:
        await message.answer("Пожалуйста, выберите вариант из клавиатуры")
        return

    await state.update_data(practice_frequency=message.text)
    await message.answer(
        "3. На чем Вы сосредотачиваетесь во время практики: " \
        "Дыхание, Телесные ощущения, Мантры/звуки, Визуальные образы, Эмоции? "
        "(Перечислите через запятую)",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(MindfulnessQuestionnaire.FOCUS_OBJECT)


@router.message(MindfulnessQuestionnaire.FOCUS_OBJECT)
async def process_focus_object(message: Message, state: FSMContext):
    await state.update_data(focus_object=message.text)
    await message.answer(
        "4. Насколько легко вам возвращать внимание к объекту концентрации, когда ум отвлечен?",
        reply_markup=get_difficulty_kb(),
    )
    await state.set_state(MindfulnessQuestionnaire.CONCENTRATION_DIFFICULTY)


@router.message(MindfulnessQuestionnaire.CONCENTRATION_DIFFICULTY)
async def process_concentration_difficulty(message: Message, state: FSMContext):
    valid_answers = ["Очень трудно", "Трудно", "Легко"]
    if message.text not in valid_answers:
        await message.answer("Пожалуйста, выберите вариант из клавиатуры")
        return

    await state.update_data(concentration_difficulty=message.text)
    await message.answer(
        "5. Какие положительные изменения Вы заметили благодаря медитации? "
        "(Напишите в свободной форме)",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(MindfulnessQuestionnaire.POSITIVE_CHANGES)


@router.message(MindfulnessQuestionnaire.POSITIVE_CHANGES)
async def process_positive_changes(message: Message, state: FSMContext):
    if len(message.text.strip()) < 10:
        await message.answer("Пожалуйста, опишите подробнее (минимум 10 символов)")
        return

    await state.update_data(positive_changes=message.text)
    data = await state.get_data()
    data["questionnaire_type"] = "mindfulness"

    await finish_questionnaire(message, state, data)
