from datetime import datetime
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from src.bot.is_admin import IsAdmin
from src.db.connection import get_db_connection

router = Router()


async def get_global_testing_start_date():
    conn = await get_db_connection()
    try:
        date = await conn.fetchval(
            "SELECT MIN(testing_start_date) FROM patients WHERE testing_start_date IS NOT NULL"
        )
        return date
    finally:
        await conn.close()


async def update_all_users_testing_date(start_date: datetime):
    """Обновляет дату тестирования для всех пользователей"""
    conn = await get_db_connection()
    try:
        await conn.execute("UPDATE patients SET testing_start_date = $1", start_date)
    finally:
        await conn.close()


@router.message(Command("start_testing"), IsAdmin())
async def start_testing(message: Message):
    """Команда для начала тестирования (только для админа)"""
    if await get_global_testing_start_date() is not None:
        start_date = await get_global_testing_start_date()
        await message.answer(
            f"⚠️ Тестирование уже начато {start_date.strftime('%d.%m.%Y')}\n"
            "Используйте /reset_testing_date для сброса"
        )
        return

    start_date = datetime.now()
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

    await update_all_users_testing_date(start_date)

    await message.answer(
        f"✅ Дата тестирования установлена вручную: {start_date.strftime('%d.%m.%Y')}"
    )


@router.message(Command("reset_testing_date"), IsAdmin())
async def reset_testing_date(message: Message):
    """Сбрасывает дату тестирования для всех пользователей (только для админа)"""
    conn = await get_db_connection()
    try:
        await conn.execute("UPDATE patients SET testing_start_date = NULL")
    finally:
        await conn.close()

    await message.answer("✅ Дата тестирования сброшена для всех пользователей")
