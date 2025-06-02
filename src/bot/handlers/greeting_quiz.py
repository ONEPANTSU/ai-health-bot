import json

from aiogram import Router, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.types import ReplyKeyboardRemove

from src.bot.is_test_allowed import is_test_day_allowed
from src.bot.keyboards import get_gender_keyboard
from src.bot.scheduler import get_user_timezone
from src.bot.states import GreetingQuestionnaire
from src.bot.utils import send_llm_advice
from src.db.connection import get_db_connection
from src.db.patient_repository import save_patient_record, create_patient

router = Router()


async def save_greeting_data(telegram_id: int, data: dict):
    conn = await get_db_connection()
    answers = {
        "questionnaire_type": "greeting",
        "prompt_type": "subjective_health",
        "full_name": data.get("full_name"),
        "phone": data.get("phone"),
        "telegram_nick": data.get("telegram_nick"),
        "age": data.get("age"),
        "gender": data.get("gender"),
        "height": data.get("height"),
        "weight": data.get("weight"),
    }

    await save_patient_record(
        conn=conn,
        telegram_id=telegram_id,
        answers=json.dumps(answers, ensure_ascii=False),
        gpt_response="",
        s3_links=[],
        summary="Анкета приветствия",
        is_daily=False,
    )


@router.message(Command("start"))
async def handle_start(msg: Message, bot: Bot):
    conn = await get_db_connection()

    # Пытаемся автоматически определить часовой пояс
    tz = await get_user_timezone(bot, msg.from_user.id)

    await create_patient(
        conn,
        telegram_id=msg.from_user.id,
        username=msg.from_user.username,
        full_name=msg.from_user.full_name,
        timezone=tz,
    )

    await msg.answer("👋 Вы зарегистрированы!")
    await conn.close()


@router.message(Command("greeting"))
async def start_greeting(message: Message, state: FSMContext):
    if not await is_test_day_allowed("greeting"):
        await message.answer("⏳ Анкета приветствия сегодня не доступна.")
        return
    await message.answer(
        "АНКЕТА ПРИВЕТСТВИЯ\n\nФИО*:",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(GreetingQuestionnaire.FULL_NAME)


@router.message(GreetingQuestionnaire.FULL_NAME)
async def process_full_name(message: Message, state: FSMContext):
    if len(message.text.strip().split()) < 2:
        await message.answer("Пожалуйста, введите ФИО полностью")
        return

    await state.update_data(full_name=message.text)
    await message.answer(
        "Контактный номер телефона* (в формате +7...):",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(GreetingQuestionnaire.PHONE)


@router.message(GreetingQuestionnaire.PHONE)
async def process_phone(message: Message, state: FSMContext):
    if not message.text.startswith("+"):
        await message.answer("Пожалуйста, введите номер с + в начале")
        return

    await state.update_data(phone=message.text)
    await message.answer(
        "Ник в Telegram (без @):",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(GreetingQuestionnaire.TELEGRAM_NICK)


@router.message(GreetingQuestionnaire.TELEGRAM_NICK)
async def process_telegram_nick(message: Message, state: FSMContext):
    await state.update_data(telegram_nick=message.text.replace("@", ""))
    await message.answer(
        "Возраст (полных лет)*:",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(GreetingQuestionnaire.AGE)


@router.message(GreetingQuestionnaire.AGE)
async def process_age(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) < 12 or int(message.text) > 120:
        await message.answer("Пожалуйста, введите корректный возраст (12-120)")
        return

    await state.update_data(age=int(message.text))
    await message.answer("Пол*:", reply_markup=get_gender_keyboard())
    await state.set_state(GreetingQuestionnaire.GENDER)


@router.message(GreetingQuestionnaire.GENDER)
async def process_gender(message: Message, state: FSMContext):
    if message.text not in ["Женский", "Мужской"]:
        await message.answer("Пожалуйста, выберите вариант из клавиатуры")
        return

    await state.update_data(gender=message.text)
    await message.answer(
        "Рост* (в см, 120-250):",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(GreetingQuestionnaire.HEIGHT)


@router.message(GreetingQuestionnaire.HEIGHT)
async def process_height(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) < 120 or int(message.text) > 250:
        await message.answer("Пожалуйста, введите корректный рост (120-250 см)")
        return

    await state.update_data(height=int(message.text))
    await message.answer(
        "Вес* (в кг, 30-300):",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(GreetingQuestionnaire.WEIGHT)


@router.message(GreetingQuestionnaire.WEIGHT)
async def process_weight(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) < 30 or int(message.text) > 300:
        await message.answer("Пожалуйста, введите корректный вес (30-300 кг)")
        return

    data = await state.get_data()
    q_type = "greeting"
    data["questionnaire_type"] = q_type

    await save_greeting_data(message.from_user.id, data)

    await message.answer(
        "✅ Анкета сохранена!\n\n"
        f"ФИО: {data['full_name']}\n"
        f"Телефон: {data['phone']}\n"
        f"Ник: @{data['telegram_nick']}\n"
        f"Возраст: {data['age']}\n"
        f"Пол: {data['gender']}\n"
        f"Рост: {data['height']} см\n"
        f"Вес: {message.text} кг",
        reply_markup=ReplyKeyboardRemove(),
    )
    await send_llm_advice(message, data, [])
    await state.clear()
