from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_sleep_time_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="До 22:00")],
            [KeyboardButton(text="22:00-00:00")],
            [KeyboardButton(text="После 00:00")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def get_sleep_quality_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Легко")],
            [KeyboardButton(text="Долго пытался(лась) уснуть")],
            [KeyboardButton(text="Другое")],
        ],
        resize_keyboard=True,
    )


def get_yes_no_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Да")],
            [KeyboardButton(text="Нет")],
        ],
        resize_keyboard=True,
    )


def get_morning_feeling_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Легко")],
            [KeyboardButton(text="С трудом заставляю себя встать")],
        ],
        resize_keyboard=True,
    )


def get_sleep_rating_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Хорошо")],
            [KeyboardButton(text="Средне")],
            [KeyboardButton(text="Плохо")],
        ],
        resize_keyboard=True,
    )


def get_rating_10_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=str(i)) for i in range(1, 11)]],
        resize_keyboard=True,
    )


def get_mood_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Отличное")],
            [KeyboardButton(text="Хорошее")],
            [KeyboardButton(text="Нейтральное")],
            [KeyboardButton(text="Плохое")],
            [KeyboardButton(text="Очень плохое")],
        ],
        resize_keyboard=True,
    )


def get_frequency_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Ни разу")],
            [KeyboardButton(text="Пару раз")],
            [KeyboardButton(text="Часто")],
        ],
        resize_keyboard=True,
    )


def get_anxiety_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Ни разу")],
            [KeyboardButton(text="Один раз")],
            [KeyboardButton(text="Пару раз")],
            [KeyboardButton(text="Весь день")],
        ],
        resize_keyboard=True,
    )


def get_workout_intensity_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Нет")],
            [KeyboardButton(text="Да, легкие")],
            [KeyboardButton(text="Да, средние")],
            [KeyboardButton(text="Да, тяжелые")],
        ],
        resize_keyboard=True,
    )


def get_fatigue_level_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            *[[KeyboardButton(text=str(i))] for i in range(1, 11)],
        ],
        resize_keyboard=True,
    )


def get_after_work_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Очень хорошо")],
            [KeyboardButton(text="Хорошо")],
            [KeyboardButton(text="Удовлетворительно")],
            [KeyboardButton(text="Плохо")],
            [KeyboardButton(text="Очень плохо")],
        ],
        resize_keyboard=True,
    )


def get_gender_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Женский")], [KeyboardButton(text="Мужской")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def get_support_count_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Никто")],
            [KeyboardButton(text="1-2 человека")],
            [KeyboardButton(text="3-5 человек")],
            [KeyboardButton(text="Более 6 человек")],
        ],
        resize_keyboard=True,
    )


def get_frequency_communication_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Каждый день")],
            [KeyboardButton(text="Несколько раз в неделю")],
            [KeyboardButton(text="Раз в неделю")],
            [KeyboardButton(text="Реже")],
        ],
        resize_keyboard=True,
    )


def get_focus_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Дыхание")],
            [KeyboardButton(text="Телесные ощущения")],
            [KeyboardButton(text="Мантры/звуки")],
            [KeyboardButton(text="Визуальные образы")],
            [KeyboardButton(text="Эмоции")],
        ],
        resize_keyboard=True,
    )


def get_difficulty_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Очень трудно")],
            [KeyboardButton(text="Трудно")],
            [KeyboardButton(text="Легко")],
        ],
        resize_keyboard=True,
    )
