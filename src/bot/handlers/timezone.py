from aiogram import Router, F
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from src.bot.states import TimezoneStates
from src.db.connection import get_db_connection

router = Router()

# Список популярных часовых поясов с понятными названиями
TIMEZONE_OPTIONS = [
    ("UTC+0 (Лондон)", "UTC+0"),
    ("UTC+1 (Париж, Берлин)", "UTC+1"),
    ("UTC+2 (Киев, Хельсинки)", "UTC+2"),
    ("UTC+3 (Москва, Стамбул)", "UTC+3"),
    ("UTC+4 (Дубай, Самара)", "UTC+4"),
    ("UTC+5 (Екатеринбург, Исламабад)", "UTC+5"),
    ("UTC+6 (Алматы, Дакка)", "UTC+6"),
    ("UTC+7 (Бангкок, Красноярск)", "UTC+7"),
    ("UTC+8 (Пекин, Сингапур)", "UTC+8"),
    ("UTC+9 (Токио, Сеул)", "UTC+9"),
    ("UTC+10 (Владивосток, Сидней)", "UTC+10"),
    ("UTC+11 (Магадан, Новая Каледония)", "UTC+11"),
    ("UTC+12 (Камчатка, Окленд)", "UTC+12"),
    ("UTC-1 (Азорские о-ва)", "UTC-1"),
    ("UTC-2 (Южная Георгия)", "UTC-2"),
    ("UTC-3 (Бразилия, Аргентина)", "UTC-3"),
    ("UTC-4 (Нью-Йорк, Торонто)", "UTC-4"),
    ("UTC-5 (Чикаго, Мехико)", "UTC-5"),
    ("UTC-6 (Денвер, Гватемала)", "UTC-6"),
    ("UTC-7 (Лос-Анджелес, Ванкувер)", "UTC-7"),
    ("UTC-8 (Аляска)", "UTC-8"),
    ("UTC-9 (Гавайи)", "UTC-9"),
    ("UTC-10 (Гавайи-Алеуты)", "UTC-10"),
]


@router.message(Command("set_timezone"))
async def ask_timezone(message: Message, state: FSMContext):
    # Создаем клавиатуру с кнопками (по 3 в ряду)
    keyboard = []
    row = []

    for i, (label, tz) in enumerate(TIMEZONE_OPTIONS, 1):
        row.append(KeyboardButton(text=label))
        if i % 3 == 0 or i == len(TIMEZONE_OPTIONS):
            keyboard.append(row)
            row = []

    # Добавляем кнопку для ручного ввода
    keyboard.append([KeyboardButton(text="Ввести вручную (например UTC+3)")])

    timezone_keyboard = ReplyKeyboardMarkup(
        keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True
    )

    await message.answer(
        "🕒 Пожалуйста, выберите ваш часовой пояс:\n\n"
        "Можете выбрать из списка или ввести вручную в формате:\n"
        "<code>UTC+3</code> или <code>UTC-5</code>",
        reply_markup=timezone_keyboard,
        parse_mode="HTML",
    )
    await state.set_state(TimezoneStates.waiting_timezone)


@router.message(TimezoneStates.waiting_timezone, F.text.regexp(r"^UTC[+-]\d{1,2}$"))
async def handle_timezone_input(message: Message, state: FSMContext):
    await save_timezone(message, message.text.strip())
    await state.clear()


@router.message(TimezoneStates.waiting_timezone, F.text.startswith("UTC"))
async def handle_timezone_button(message: Message, state: FSMContext):
    # Обрабатываем выбор из кнопок (ищем соответствие в TIMEZONE_OPTIONS)
    selected_text = message.text
    for label, tz in TIMEZONE_OPTIONS:
        if selected_text.startswith(label.split()[0]):
            await save_timezone(message, tz)
            await state.clear()
            return

    await message.answer(
        "❌ Пожалуйста, выберите вариант из списка или введите вручную"
    )


@router.message(TimezoneStates.waiting_timezone)
async def handle_wrong_timezone_format(message: Message):
    await message.answer(
        "❌ Неверный формат часового пояса.\n\n"
        "Пожалуйста, введите в формате:\n"
        "<code>UTC+3</code> или <code>UTC-5</code>\n\n"
        "Или выберите один из предложенных вариантов.",
        parse_mode="HTML",
    )


async def save_timezone(message: Message, timezone_str: str):
    # Маппинг для преобразования в формат IANA (Europe/Moscow)
    iana_timezones = {
        "UTC+0": "Europe/London",
        "UTC+1": "Europe/Paris",
        "UTC+2": "Europe/Kiev",
        "UTC+3": "Europe/Moscow",
        "UTC+4": "Asia/Dubai",
        "UTC+5": "Asia/Yekaterinburg",
        "UTC+6": "Asia/Almaty",
        "UTC+7": "Asia/Bangkok",
        "UTC+8": "Asia/Shanghai",
        "UTC+9": "Asia/Tokyo",
        "UTC+10": "Asia/Vladivostok",
        "UTC+11": "Asia/Magadan",
        "UTC+12": "Pacific/Auckland",
        "UTC-1": "Atlantic/Azores",
        "UTC-2": "Atlantic/South_Georgia",
        "UTC-3": "America/Sao_Paulo",
        "UTC-4": "America/New_York",
        "UTC-5": "America/Chicago",
        "UTC-6": "America/Denver",
        "UTC-7": "America/Los_Angeles",
        "UTC-8": "America/Anchorage",
        "UTC-9": "Pacific/Honolulu",
        "UTC-10": "Pacific/Honolulu",
    }

    # Получаем красивое название из кнопки ("UTC+10 (Владивосток...)" -> "UTC+10")
    selected_tz = next(
        (
            tz
            for label, tz in TIMEZONE_OPTIONS
            if label.startswith(timezone_str.split()[0])
        ),
        timezone_str,
    )

    timezone_db = iana_timezones.get(selected_tz, selected_tz)

    try:
        conn = await get_db_connection()
        await conn.execute(
            "UPDATE patients SET timezone = $1 WHERE telegram_id = $2",
            timezone_db,
            message.from_user.id,
        )

        # Находим полное название для подтверждения
        display_tz = next(
            (label for label, tz in TIMEZONE_OPTIONS if tz == selected_tz), selected_tz
        )

        await message.answer(
            f"✅ Часовой пояс установлен: <b>{display_tz}</b>\n"
            f"Теперь напоминания будут приходить в ваше местное время.",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="HTML",
        )
    except Exception as e:
        await message.answer("❌ Произошла ошибка при сохранении часового пояса")
        print(f"Timezone save error: {e}")
