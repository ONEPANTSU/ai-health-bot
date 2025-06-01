from datetime import datetime
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from src.bot.is_admin import IsAdmin
from src.db.connection import get_db_connection

router = Router()


async def set_global_testing_start_date(start_date: datetime):
    """Устанавливает глобальную дату начала тестирования"""
    conn = await get_db_connection()
    await conn.execute(
        "INSERT INTO system_settings (setting_name, setting_value) "
        "VALUES ('testing_start_date', $1) "
        "ON CONFLICT (setting_name) DO UPDATE SET setting_value = EXCLUDED.setting_value",
        start_date.isoformat(),
    )


async def get_global_testing_start_date():
    """Получает глобальную дату начала тестирования"""
    conn = await get_db_connection()
    date_str = await conn.fetchval(
        "SELECT setting_value FROM system_settings WHERE setting_name = 'testing_start_date'"
    )
    return datetime.fromisoformat(date_str) if date_str else None


async def update_all_users_testing_date(start_date: datetime):
    """Обновляет дату тестирования для всех пользователей"""
    conn = await get_db_connection()
    await conn.execute("UPDATE patients SET testing_start_date = $1", start_date)


async def is_testing_started():
    """Проверяет, было ли начато тестирование"""
    return await get_global_testing_start_date() is not None


@router.message(Command("start_testing"), IsAdmin())
async def start_testing(message: Message):
    """Команда для начала тестирования (только для админа)"""
    if await is_testing_started():
        start_date = await get_global_testing_start_date()
        await message.answer(
            f"⚠️ Тестирование уже начато {start_date.strftime('%d.%m.%Y')}\n"
            "Используйте /reset_testing_date для сброса"
        )
        return

    start_date = datetime.now()
    await set_global_testing_start_date(start_date)
    await update_all_users_testing_date(start_date)

    await message.answer(
        f"✅ Тестирование начато для всех пользователей\n"
        f"Дата старта: {start_date.strftime('%d.%m.%Y %H:%M')}"
    )


@router.message(Command("set_testing_date"), IsAdmin())
async def manual_set_testing_date(message: Message):
    """Установка даты тестирования вручную. Пример: /set_testing_date 2025-06-01"""
    parts = message.text.strip().split()

    if len(parts) != 2:
        await message.answer(
            "❗ Укажи дату в формате yyyy-mm-dd, например: /set_testing_date 2025-06-01"
        )
        return

    date_str = parts[1]

    try:
        start_date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        await message.answer(
            "❗ Неверный формат даты. Используй yyyy-mm-dd, например: /set_testing_date 2025-06-01"
        )
        return

    await set_global_testing_start_date(start_date)
    await update_all_users_testing_date(start_date)

    await message.answer(
        f"✅ Дата тестирования установлена вручную: {start_date.strftime('%d.%m.%Y')}"
    )


@router.message(Command("check_testing_date"))
async def check_testing_date(message: Message):
    """Проверка текущей даты тестирования"""
    start_date = await get_global_testing_start_date()
    if start_date:
        await message.answer(
            f"📅 Тестирование начато: {start_date.strftime('%d.%m.%Y %H:%M')}\n"
            f"Прошло дней: {(datetime.now() - start_date).days}"
        )
    else:
        await message.answer("Тестирование еще не начато")


# В функции регистрации пользователя (patient_repository.py)
async def create_patient(
    conn, telegram_id: int, username: str = None, full_name: str = None
):
    """Создает пользователя с текущей датой тестирования (если она установлена)"""
    testing_date = await get_global_testing_start_date()

    await conn.execute(
        """
        INSERT INTO patients (telegram_id, username, full_name, testing_start_date)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (telegram_id) DO UPDATE SET
            username = EXCLUDED.username,
            full_name = EXCLUDED.full_name
        """,
        telegram_id,
        username,
        full_name,
        testing_date,  # Автоматически ставится текущая дата тестирования
    )
