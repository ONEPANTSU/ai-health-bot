import json

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.types  import ReplyKeyboardRemove

from src.bot.keyboards import (
    get_sleep_time_kb,
    get_sleep_quality_kb,
    get_yes_no_kb,
    get_morning_feeling_kb,
    get_mood_kb,
    get_rating_10_kb,
    get_anxiety_kb,
    get_workout_intensity_kb,
    get_fatigue_level_kb,
    get_after_work_kb,
    get_sleep_rating_kb,
    get_frequency_kb,
)
from src.bot.states import DailyQuestionnaire
from src.db.connection import get_db_connection
from src.db.patient_repository import save_patient_record

router = Router()


@router.message(Command("daily"))
async def start_daily_questionnaire(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Ежедневная анкета:\n1. Во сколько Вы вчера легли спать?",
        reply_markup=get_sleep_time_kb(),
    )
    await state.set_state(DailyQuestionnaire.SLEEP_TIME)


@router.message(DailyQuestionnaire.SLEEP_TIME)
async def process_sleep_time(message: Message, state: FSMContext):
    if message.text not in ["До 22:00", "22:00-00:00", "После 00:00"]:
        await message.answer("Пожалуйста, выберите вариант из клавиатуры.")
        return

    await state.update_data(sleep_time=message.text)
    await message.answer(
        "2. Как Вы вчера заснули?", reply_markup=get_sleep_quality_kb()
    )
    await state.set_state(DailyQuestionnaire.SLEEP_QUALITY)


@router.message(DailyQuestionnaire.SLEEP_QUALITY)
async def process_sleep_quality(message: Message, state: FSMContext):
    if message.text not in ["Легко", "Долго пытался(лась) уснуть", "Другое"]:
        await message.answer("Пожалуйста, выберите вариант из клавиатуры.")
        return

    await state.update_data(sleep_quality=message.text)
    await message.answer("3. Просыпались среди ночи?", reply_markup=get_yes_no_kb())
    await state.set_state(DailyQuestionnaire.WAKE_UP_COUNT)


@router.message(DailyQuestionnaire.WAKE_UP_COUNT)
async def process_wake_up_count(message: Message, state: FSMContext):
    if message.text not in ["Да", "Нет"]:
        await message.answer("Пожалуйста, укажите Да или Нет.")
        return

    await state.update_data(wake_up_count=message.text)
    await message.answer(
        "4. Как проснулись утром?", reply_markup=get_morning_feeling_kb()
    )
    await state.set_state(DailyQuestionnaire.MORNING_FEELING)


@router.message(DailyQuestionnaire.MORNING_FEELING)
async def process_morning_feeling(message: Message, state: FSMContext):
    if message.text not in ["Легко", "С трудом заставляю себя встать"]:
        await message.answer("Пожалуйста, выберите вариант из клавиатуры.")
        return

    await state.update_data(morning_feeling=message.text)
    await message.answer(
        "5. Беспокоила ли сонливость в течение дня?", reply_markup=get_yes_no_kb()
    )
    await state.set_state(DailyQuestionnaire.DAY_SLEEPINESS)


@router.message(DailyQuestionnaire.DAY_SLEEPINESS)
async def process_day_sleepiness(message: Message, state: FSMContext):
    if message.text not in ["Да", "Нет"]:
        await message.answer("Пожалуйста, укажите Да или Нет.")
        return

    await state.update_data(day_sleepiness=message.text)
    await message.answer(
        "6. Как Вы оцениваете качество своего сна сегодня?",
        reply_markup=get_sleep_rating_kb(),
    )
    await state.set_state(DailyQuestionnaire.SLEEP_RATING)


@router.message(DailyQuestionnaire.SLEEP_RATING)
async def process_sleep_rating(message: Message, state: FSMContext):
    if message.text not in ["Хорошо", "Средне", "Плохо"]:
        await message.answer("Пожалуйста, выберите вариант из клавиатуры.")
        return

    await state.update_data(sleep_rating=message.text)
    await message.answer(
        "7. Оцените уровень вашего стресса за прошедший день (1-10)",
        reply_markup=get_rating_10_kb(),
    )
    await state.set_state(DailyQuestionnaire.STRESS_LEVEL)


@router.message(DailyQuestionnaire.STRESS_LEVEL)
async def process_stress_level(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) not in range(1, 11):
        await message.answer("Пожалуйста, введите число от 1 до 10.")
        return

    await state.update_data(stress_level=int(message.text))
    await message.answer(
        "8. Что стало основным источником стресса прошедший день? (Напишите текст)",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(DailyQuestionnaire.STRESS_SOURCE)


@router.message(DailyQuestionnaire.STRESS_SOURCE)
async def process_stress_source(message: Message, state: FSMContext):
    await state.update_data(stress_source=message.text)
    await message.answer(
        "9. Каким было ваше настроение вчера?", reply_markup=get_mood_kb()
    )
    await state.set_state(DailyQuestionnaire.MOOD)


@router.message(DailyQuestionnaire.MOOD)
async def process_mood(message: Message, state: FSMContext):
    if message.text not in [
        "Отличное",
        "Хорошее",
        "Нейтральное",
        "Плохое",
        "Очень плохое",
    ]:
        await message.answer("Пожалуйста, выберите вариант из клавиатуры.")
        return

    await state.update_data(mood=message.text)
    await message.answer(
        "10. Испытывали ли Вы чувство радости вчера?", reply_markup=get_yes_no_kb()
    )
    await state.set_state(DailyQuestionnaire.JOY)


@router.message(DailyQuestionnaire.JOY)
async def process_joy(message: Message, state: FSMContext):
    if message.text not in ["Да", "Нет"]:
        await message.answer("Пожалуйста, укажите Да или Нет.")
        return

    await state.update_data(joy=message.text)
    await message.answer(
        "11. Оцените уровень вашей энергии за прошедший день (1-10)",
        reply_markup=get_rating_10_kb(),
    )
    await state.set_state(DailyQuestionnaire.ENERGY_LEVEL)


@router.message(DailyQuestionnaire.ENERGY_LEVEL)
async def process_energy_level(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) not in range(1, 11):
        await message.answer("Пожалуйста, введите число от 1 до 10.")
        return

    await state.update_data(energy_level=int(message.text))
    await message.answer(
        "12. Вы чувствовали усталость в течение прошедшего дня?",
        reply_markup=get_frequency_kb(),
    )
    await state.set_state(DailyQuestionnaire.FATIGUE_FREQUENCY)


@router.message(DailyQuestionnaire.FATIGUE_FREQUENCY)
async def process_fatigue_frequency(message: Message, state: FSMContext):
    if message.text not in ["Ни разу", "Пару раз", "Часто"]:
        await message.answer("Пожалуйста, выберите вариант из клавиатуры.")
        return

    await state.update_data(fatigue_frequency=message.text)
    await message.answer(
        "13. Как часто Вы чувствовали тревожность вчера?", reply_markup=get_anxiety_kb()
    )
    await state.set_state(DailyQuestionnaire.ANXIETY_FREQUENCY)


@router.message(DailyQuestionnaire.ANXIETY_FREQUENCY)
async def process_anxiety_frequency(message: Message, state: FSMContext):
    if message.text not in ["Ни разу", "Один раз", "Пару раз", "Весь день"]:
        await message.answer("Пожалуйста, выберите вариант из клавиатуры.")
        return

    await state.update_data(anxiety_frequency=message.text)
    await message.answer(
        "14. Оцените уровень мотивации за прошедший день (1-10)",
        reply_markup=get_rating_10_kb(),
    )
    await state.set_state(DailyQuestionnaire.MOTIVATION_LEVEL)


@router.message(DailyQuestionnaire.MOTIVATION_LEVEL)
async def process_motivation_level(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) not in range(1, 11):
        await message.answer("Пожалуйста, введите число от 1 до 10.")
        return

    await state.update_data(motivation_level=int(message.text))
    await message.answer("15. Сколько шагов в среднем Вы прошли вчера? (Введите число)",
        reply_markup=ReplyKeyboardRemove(),)
    await state.set_state(DailyQuestionnaire.STEPS_COUNT)


@router.message(DailyQuestionnaire.STEPS_COUNT)
async def process_steps_count(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите число.")
        return

    await state.update_data(steps_count=int(message.text))
    await message.answer(
        "16. Были ли вчера у вас тренировки?", reply_markup=get_workout_intensity_kb()
    )
    await state.set_state(DailyQuestionnaire.WORKOUT_INTENSITY)


@router.message(DailyQuestionnaire.WORKOUT_INTENSITY)
async def process_workout_intensity(message: Message, state: FSMContext):
    if message.text not in ["Нет", "Да, легкие", "Да, средние", "Да, тяжелые"]:
        await message.answer("Пожалуйста, выберите вариант из клавиатуры.")
        return

    await state.update_data(workout_intensity=message.text)

    if message.text != "Нет":
        await message.answer(
            "17. Тревожат ли вас какие-либо боли после тренировки?",
            reply_markup=get_yes_no_kb(),
        )
        await state.set_state(DailyQuestionnaire.WORKOUT_PAIN)
    else:
        await state.update_data(workout_pain="Нет", workout_pain_location="")
        await message.answer(
            "18. Оцените уровень утомляемости (0-10)",
            reply_markup=get_fatigue_level_kb(),
        )
        await state.set_state(DailyQuestionnaire.FATIGUE_LEVEL)


@router.message(DailyQuestionnaire.WORKOUT_PAIN)
async def process_workout_pain(message: Message, state: FSMContext):
    if message.text not in ["Да", "Нет"]:
        await message.answer("Пожалуйста, укажите Да или Нет.")
        return

    await state.update_data(workout_pain=message.text)

    if message.text == "Да":
        await message.answer("Укажите, где именно болит (напишите текст):", 
                             reply_markup=ReplyKeyboardRemove(),)
        await state.set_state(DailyQuestionnaire.WORKOUT_PAIN_LOCATION)
    else:
        await state.update_data(workout_pain_location="")
        await message.answer(
            "18. Оцените уровень утомляемости (0-10)",
            reply_markup=get_fatigue_level_kb(),
        )
        await state.set_state(DailyQuestionnaire.FATIGUE_LEVEL)


@router.message(DailyQuestionnaire.WORKOUT_PAIN_LOCATION)
async def process_workout_pain_location(message: Message, state: FSMContext):
    await state.update_data(workout_pain_location=message.text)
    await message.answer(
        "18. Оцените уровень утомляемости (0-10)", reply_markup=get_fatigue_level_kb()
    )
    await state.set_state(DailyQuestionnaire.FATIGUE_LEVEL)


@router.message(DailyQuestionnaire.FATIGUE_LEVEL)
async def process_fatigue_level(message: Message, state: FSMContext):
    valid_responses = (
        ["Не утомлен(а)"] + [str(i) for i in range(1, 11)] + ["Крайне утомлен(а)"]
    )
    if message.text not in valid_responses:
        await message.answer("Пожалуйста, выберите вариант из клавиатуры.")
        return

    await state.update_data(fatigue_level=message.text)
    await message.answer(
        "19. Как Вы вчера себя чувствовали после завершения работы?",
        reply_markup=get_after_work_kb(),
    )
    await state.set_state(DailyQuestionnaire.AFTER_WORK_FEELING)


@router.message(DailyQuestionnaire.AFTER_WORK_FEELING)
async def process_after_work_feeling(message: Message, state: FSMContext):
    if message.text not in [
        "Очень хорошо",
        "Хорошо",
        "Удовлетворительно",
        "Плохо",
        "Очень плохо",
    ]:
        await message.answer("Пожалуйста, выберите вариант из клавиатуры.")
        return

    await state.update_data(after_work_feeling=message.text)
    data = await state.get_data()
    q_type = "daily"
    data["questionnaire_type"] = q_type
    data["prompt_type"] = "subjective_health",

    # Сохранение в БД
    conn = await get_db_connection()
    await save_patient_record(
        conn=conn,
        telegram_id=message.from_user.id,
        answers=json.dumps(data, ensure_ascii=False),
        gpt_response="",
        s3_links=[],
        summary="Ежедневная анкета",
        is_daily=True,
    )

    await message.answer("✅ Анкета успешно сохранена! Спасибо за участие!",
        reply_markup=ReplyKeyboardRemove(),)
    await state.clear()
