import json
import re
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from src.bot.states import PressurePulseStates
from src.bot.utils import send_llm_advice
from src.db.connection import get_db_connection
from src.db.patient_repository import save_patient_record

router = Router()


@router.message(Command("pressure"))
async def request_pressure_pulse(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(PressurePulseStates.waiting_pressure_pulse)
    await message.answer(
        "🩺 Пожалуйста, отправьте ваши показатели давления и пульса в покое в формате:\n\n"
        "<b>120/80 70</b>\n\n"
        "Где:\n"
        "- Первое число (120) - систолическое давление\n"
        "- Второе число (80) - диастолическое давление\n"
        "- Третье число (70) - пульс\n\n"
        "Примеры корректных сообщений:\n"
        "• 120/80 70\n"
        "• 115 75 65\n"
        "• Давление: 130/85, пульс: 72 (можно с пояснениями)"
    )


@router.message(PressurePulseStates.waiting_pressure_pulse)
async def handle_pressure_pulse(message: Message, state: FSMContext):
    try:
        numbers = re.findall(r"\d+", message.text)

        if len(numbers) >= 3:
            systolic = int(numbers[0])
            diastolic = int(numbers[1])
            pulse = int(numbers[2])

            conn = await get_db_connection()
            answers = {
                "questionnaire_type": "pressure_pulse",
                "prompt_type": "physiology",
                "data": message.text,
                "extracted_values": {
                    "systolic": systolic,
                    "diastolic": diastolic,
                    "pulse": pulse,
                },
            }

            await save_patient_record(
                conn=conn,
                telegram_id=message.from_user.id,
                answers=json.dumps(answers, ensure_ascii=False),
                gpt_response="",
                s3_links=[],
                summary=f"Давление: {systolic}/{diastolic}, Пульс: {pulse}",
                is_daily=True,
            )

            await message.answer(
                f"✅ Данные сохранены:\n"
                f"• Давление: <b>{systolic}/{diastolic}</b>\n"
                f"• Пульс: <b>{pulse}</b>",
                parse_mode="HTML",
            )

            await send_llm_advice(
                message,
                answers,
                [],
            )
            await state.clear()

        else:
            await message.answer(
                "❌ Не удалось распознать данные. Пожалуйста, используйте формат: 120/80 70"
            )

    except Exception as e:
        await message.answer(
            "❌ Ошибка при обработке данных. Пожалуйста, проверьте формат и попробуйте еще раз."
        )
        print(f"Error: {e}")
