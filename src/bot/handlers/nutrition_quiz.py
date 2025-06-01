import json
import re

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.bot.is_test_allowed import is_test_day_allowed
from src.bot.states import NutritionQuestionnaire
from src.db.connection import get_db_connection
from src.db.patient_repository import save_patient_record

router = Router()


async def save_nutrition_data(telegram_id: int, data: dict):
    conn = await get_db_connection()
    answers = {
        "questionnaire_type": "nutrition",
        "prompt_type": "subjective_health",
        "breakfast": data["breakfast"],
        "lunch": data["lunch"],
        "dinner": data["dinner"],
        "snacks": data["snacks"],
        "water": data["water"],
    }

    await save_patient_record(
        conn=conn,
        telegram_id=telegram_id,
        answers=json.dumps(answers, ensure_ascii=False),  # Fixed: proper JSON encoding
        gpt_response="",
        s3_links=[],
        summary="Анкета питания за 3 дня",
        is_daily=False,
    )


@router.message(Command("nutrition"))
async def start_nutrition_questionnaire(message: Message, state: FSMContext):
    await state.clear()
    if not await is_test_day_allowed("nutrition"):
        await message.answer(
            "⏳ Анкета питания не предназначена для заполнения сегодня"
        )
        return
    await message.answer(
        "АНКЕТА ПИТАНИЯ\n\n"
        "Перечислите, что Вы ели за последние 3 дня на завтрак (например: "
        "'1 день: овсянка, чай; 2 день: омлет, кофе; 3 день: творог с фруктами'):"
    )
    await state.set_state(NutritionQuestionnaire.BREAKFAST_3DAYS)


@router.message(NutritionQuestionnaire.BREAKFAST_3DAYS)
async def process_breakfast(message: Message, state: FSMContext):
    if len(message.text) < 10:  # Минимальная проверка на ввод
        await message.answer("Пожалуйста, укажите подробнее что Вы ели")
        return

    await state.update_data(breakfast=message.text)
    await message.answer(
        "Перечислите, что Вы ели за последние 3 дня на обед (например: "
        "'1 день: курица с гречкой; 2 день: суп, салат; 3 день: рыба с овощами'):"
    )
    await state.set_state(NutritionQuestionnaire.LUNCH_3DAYS)


@router.message(NutritionQuestionnaire.LUNCH_3DAYS)
async def process_lunch(message: Message, state: FSMContext):
    if len(message.text) < 10:
        await message.answer("Пожалуйста, укажите подробнее что Вы ели")
        return

    await state.update_data(lunch=message.text)
    await message.answer(
        "Перечислите, что Вы ели за последние 3 дня на ужин (например: "
        "'1 день: творог; 2 день: курица с овощами; 3 день: омлет'):"
    )
    await state.set_state(NutritionQuestionnaire.DINNER_3DAYS)


@router.message(NutritionQuestionnaire.DINNER_3DAYS)
async def process_dinner(message: Message, state: FSMContext):
    if len(message.text) < 10:
        await message.answer("Пожалуйста, укажите подробнее что Вы ели")
        return

    await state.update_data(dinner=message.text)
    await message.answer(
        "Перечислите, какие у вас были перекусы за последние три дня (например: "
        "'1 день: яблоко, йогурт; 2 день: орехи; 3 день: банан'):"
    )
    await state.set_state(NutritionQuestionnaire.SNACKS_3DAYS)


@router.message(NutritionQuestionnaire.SNACKS_3DAYS)
async def process_snacks(message: Message, state: FSMContext):
    if len(message.text) < 5:  # Минимальная проверка
        await message.answer("Пожалуйста, укажите хотя бы основные перекусы")
        return

    await state.update_data(snacks=message.text)
    await message.answer(
        "Сколько воды в среднем Вы выпиваете в день? (укажите в литрах, например: 1.5):"
    )
    await state.set_state(NutritionQuestionnaire.WATER_INTAKE)


@router.message(NutritionQuestionnaire.WATER_INTAKE)
async def process_water(message: Message, state: FSMContext):
    if (
        not re.match(r"^\d{1,2}(\.\d{1,2})?$", message.text)
        or float(message.text) < 0.1
        or float(message.text) > 10
    ):
        await message.answer(
            "Пожалуйста, введите корректное количество (0.1-10 литров)"
        )
        return

    data = await state.get_data()
    q_type = "nutrition"
    data["questionnaire_type"] = q_type

    data["water"] = float(message.text)
    await save_nutrition_data(message.from_user.id, data)

    summary = (
        "✅ Анкета питания сохранена:\n\n"
        f"Завтраки за 3 дня:\n{data['breakfast']}\n\n"
        f"Обеды за 3 дня:\n{data['lunch']}\n\n"
        f"Ужины за 3 дня:\n{data['dinner']}\n\n"
        f"Перекусы за 3 дня:\n{data['snacks']}\n\n"
        f"Вода: {data['water']} л/день"
    )

    await message.answer(summary)
    await state.clear()
