import json

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.bot.is_test_allowed import is_test_day_allowed
from src.bot.keyboards import (
    get_rating_10_kb,
    get_frequency_communication_kb,
)
from src.bot.states import CloseCircleQuestionnaire
from src.db.connection import get_db_connection
from src.db.patient_repository import save_patient_record

router = Router()


async def save_close_circle_data(telegram_id: int, data: dict):
    conn = await get_db_connection()
    answers = {
        "questionnaire_type": "close_circle",
        "relationships": data.get("relationships", ""),
        "relationship_quality": data.get("relationship_quality", 0),
        "communication_frequency": data.get("communication_frequency", ""),
    }

    await save_patient_record(
        conn=conn,
        telegram_id=telegram_id,
        answers=json.dumps(answers, ensure_ascii=False),
        gpt_response="",
        s3_links=[],
        summary="Анкета о близком окружении",
        is_daily=False,
    )
    await conn.close()


@router.message(Command("close_environment"))
async def start_close_circle(message: Message, state: FSMContext):
    await state.clear()
    if not is_test_day_allowed("close_environment"):
        await message.answer(
            "⏳ Анкета о близком окружении сегодня не доступна."
        )
        return
    await message.answer(
        "МИНИ-АНКЕТА О БЛИЗКОМ ОКРУЖЕНИИ\n\n"
        "Кто входит в ваше близкое окружение? (укажите отношения, например: "
        "'мама, отец, сестра, лучший друг Алекс')"
    )
    await state.set_state(CloseCircleQuestionnaire.RELATIONSHIPS)


# Обработка состава окружения
@router.message(CloseCircleQuestionnaire.RELATIONSHIPS)
async def process_relationships(message: Message, state: FSMContext):
    if len(message.text.strip()) < 5:
        await message.answer(
            "Пожалуйста, укажите хотя бы одного человека и ваши отношения"
        )
        return

    await state.update_data(relationships=message.text)
    await message.answer(
        "Как Вы оцениваете свои отношения с близкими по шкале от 0 до 10?\n"
        "0 - Очень плохие, 10 - Отличные",
        reply_markup=get_rating_10_kb(),
    )
    await state.set_state(CloseCircleQuestionnaire.RELATIONSHIP_QUALITY)


# Обработка оценки отношений
@router.message(CloseCircleQuestionnaire.RELATIONSHIP_QUALITY)
async def process_relationship_quality(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) not in range(0, 11):
        await message.answer("Пожалуйста, выберите оценку от 0 до 10")
        return

    await state.update_data(relationship_quality=int(message.text))
    await message.answer(
        "Как часто Вы общаетесь с членами вашего близкого окружения?",
        reply_markup=get_frequency_communication_kb(),
    )
    await state.set_state(CloseCircleQuestionnaire.COMMUNICATION_FREQUENCY)


# Обработка частоты общения
@router.message(CloseCircleQuestionnaire.COMMUNICATION_FREQUENCY)
async def process_communication_frequency(message: Message, state: FSMContext):
    valid_answers = ["Каждый день", "Несколько раз в неделю", "Раз в неделю", "Реже"]
    if message.text not in valid_answers:
        await message.answer("Пожалуйста, выберите вариант из клавиатуры")
        return

    await state.update_data(communication_frequency=message.text)
    data = await state.get_data()
    q_type = "close_circle"
    data["questionnaire_type"] = q_type

    # Сохраняем результаты
    await save_close_circle_data(message.from_user.id, data)

    # Формируем отчет
    report = (
        "✅ Анкета сохранена!\n\n"
        f"Близкое окружение: {data['relationships']}\n"
        f"Оценка отношений: {data['relationship_quality']}/10\n"
        f"Частота общения: {data['communication_frequency']}"
    )

    await message.answer(report)
    await state.clear()
