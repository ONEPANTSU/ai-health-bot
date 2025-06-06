from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.bot.is_test_allowed import is_task_day_allowed

router = Router()


@router.message(Command("blood"))
async def send_breathing_instructions(message: Message, state: FSMContext):
    await state.clear()
    if not await is_task_day_allowed("blood"):
        await message.answer(
            '⏳ Задание "Сдача крови" не предназначено для прохождения сегодня'
        )
        return

    try:
        await message.answer(
            text=("Просим сдать все анализы крови за один визит в течение дня."),
            parse_mode="HTML",
        )
    except Exception as e:
        await message.answer(f"⚠️ Не удалось загрузить медиа с инструкцией: {e}")
