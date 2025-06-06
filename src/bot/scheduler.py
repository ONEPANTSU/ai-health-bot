import asyncio
from aiogram import Bot
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging
import pytz

from src.db.connection import get_db_connection
from src.db.patient_repository import get_all_patients
from src.bot.handlers.testing import get_global_testing_start_date

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


async def get_user_timezone(user_id: int) -> str:
    """Получает часовой пояс пользователя из базы данных"""
    try:
        conn = await get_db_connection()
        tz = await conn.fetchval(
            "SELECT timezone FROM patients WHERE telegram_id = $1", user_id
        )
        return tz if tz else "Europe/Moscow"
    except Exception as e:
        logger.error(f"Ошибка получения часового пояса: {e}")
        return "Europe/Moscow"


async def send_questionnaire_to_user(bot: Bot, user_id: int, text: str, command: str):
    """Отправляет анкету пользователю с кнопкой"""
    try:
        await bot.send_message(
            chat_id=user_id,
            text=text,
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text=command)]],
                resize_keyboard=True,
            ),
        )
    except Exception as e:
        logger.error(f"Ошибка отправки пользователю {user_id}: {e}")


async def check_and_send_questionnaires(
    bot: Bot,
    test_users: list = None,
    test_now: datetime = None,
    force_day: int = None,
    force_time: tuple = None,
):
    logger.info("Starting questionnaire check...")

    try:
        if test_users is not None:
            patients = test_users
            conn = None
            use_test_data = True
        else:
            conn = await get_db_connection()
            patients = await get_all_patients(conn)
            use_test_data = False
            logger.info(f"Patients count: {len(patients)}")

        global_start_date = (
            None if use_test_data else await get_global_testing_start_date()
        )

        async def process_patient(patient):
            try:
                conn = await get_db_connection()

                telegram_id = patient["telegram_id"]
                if not patient.get("is_active", False):
                    return

                tz = pytz.timezone(patient.get("timezone", "Europe/Moscow"))
                now = test_now.astimezone(tz) if test_now else datetime.now(tz)

                if force_time:
                    now = now.replace(
                        hour=force_time[0],
                        minute=force_time[1],
                        second=0,
                        microsecond=0,
                    )

                days_passed = (now.date() - global_start_date).days

                logger.info(
                    f"User {telegram_id}: start_date={global_start_date}, now={now.date()}, days_passed={days_passed}"
                )

                day_of_program = (
                    force_day if force_day is not None else (days_passed + 1)
                )

                current_hour = now.hour
                current_minute = now.minute
                # 1. Ежедневная анкета (10:00)
                if (current_hour == 10 and current_minute == 0) or (
                    force_time and force_time == (10, 0)
                ):
                    await check_and_send_daily_questionnaire(
                        bot, conn, telegram_id, now.date()
                    )

                # 2. Анкета приветствия (день 1, 12:00)
                if day_of_program == 1 and (current_hour == 12 and current_minute == 0):
                    await send_questionnaire_to_user(
                        bot,
                        telegram_id,
                        "⏰ Пожалуйста, заполните анкету приветствия: /greeting",
                        "/greeting",
                    )

                # 3. Анкета здоровья (день 4, 19:00)
                if day_of_program == 4 and (current_hour == 19 and current_minute == 0):
                    await send_questionnaire_to_user(
                        bot,
                        telegram_id,
                        "🏥 Пожалуйста, заполните анкету состояния здоровья: /health",
                        "/health",
                    )

                # 4. Анкета питания (день 5 или 8, 19:00)
                if day_of_program in [5, 8] and (
                    current_hour == 19 and current_minute == 0
                ):
                    await send_questionnaire_to_user(
                        bot,
                        telegram_id,
                        "🍎 Пожалуйста, заполните анкету питания: /nutrition",
                        "/nutrition",
                    )

                # 5. Анкета телосложения (день 10, 18:30)
                if day_of_program == 10 and (
                    current_hour == 18 and current_minute == 30
                ):
                    await send_questionnaire_to_user(
                        bot,
                        telegram_id,
                        "📏 Пожалуйста, заполните анкету телосложения: /body_measurements",
                        "/body_measurements",
                    )

                # 6. Анкета БАДов (день 11, 19:00)
                if day_of_program == 11 and (
                    current_hour == 19 and current_minute == 0
                ):
                    await send_questionnaire_to_user(
                        bot,
                        telegram_id,
                        "💊 Пожалуйста, заполните анкету приема БАДов/витаминов: /supplements",
                        "/supplements",
                    )

                # 7. Анкета осознанности (день 14, 18:30)
                if day_of_program == 14 and (
                    current_hour == 18 and current_minute == 30
                ):
                    await send_questionnaire_to_user(
                        bot,
                        telegram_id,
                        "🧘 Пожалуйста, заполните анкету осознанности (медитации): /mindfulness",
                        "/mindfulness",
                    )

                # 8. Анкета безопасности (день 16, 19:00)
                if day_of_program == 16 and (
                    current_hour == 19 and current_minute == 0
                ):
                    await send_questionnaire_to_user(
                        bot,
                        telegram_id,
                        "🛡️ Пожалуйста, заполните анкету безопасности и поддержки: /safety",
                        "/safety",
                    )

                # 9. Анкета окружения (день 18, 19:00)
                if day_of_program == 18 and (
                    current_hour == 19 and current_minute == 0
                ):
                    await send_questionnaire_to_user(
                        bot,
                        telegram_id,
                        "👨‍👩‍👧‍👦 Пожалуйста, заполните анкету близкого окружения: /close_environment",
                        "/close_environment",
                    )

                if day_of_program == 2 and (current_hour == 11 and current_minute == 0):
                    await send_questionnaire_to_user(
                        bot,
                        telegram_id,
                        "👨‍🦱 Пожалуйста, выполните задание 'Фото лица': /face",
                        "/face",
                    )
                if day_of_program == 22 and (
                    current_hour == 19 and current_minute == 0
                ):
                    await send_questionnaire_to_user(
                        bot,
                        telegram_id,
                        "👨‍🦱 Пожалуйста, выполните задание 'Фото лица': /face",
                        "/face",
                    )
                if day_of_program == 20 and (
                    current_hour == 19 and current_minute == 0
                ):
                    await send_questionnaire_to_user(
                        bot,
                        telegram_id,
                        "🖐️ Пожалуйста, выполните задание 'Фото рук': /hands",
                        "/hands",
                    )

                if day_of_program == 3 and (
                    current_hour == 18 and current_minute == 30
                ):
                    await send_questionnaire_to_user(
                        bot,
                        telegram_id,
                        "🧍 Пожалуйста, выполните задание 'Фото в полный рост': /full_body",
                        "/full_body",
                    )
                if day_of_program == 17 and (
                    current_hour == 19 and current_minute == 0
                ):
                    await send_questionnaire_to_user(
                        bot,
                        telegram_id,
                        "🧍 Пожалуйста, выполните задание 'Фото в полный рост': /full_body",
                        "/full_body",
                    )

                if day_of_program in [5, 19] and (
                    current_hour == 19 and current_minute == 0
                ):
                    await send_questionnaire_to_user(
                        bot,
                        telegram_id,
                        "🚶 Пожалуйста, выполните задание 'Ходьба': /walking",
                        "/walking",
                    )

                if day_of_program in [8, 29] and (
                    current_hour == 18 and current_minute == 30
                ):
                    await send_questionnaire_to_user(
                        bot,
                        telegram_id,
                        "🏃 Пожалуйста, выполните задание 'Бег': /running",
                        "/running",
                    )

                if day_of_program == 10 and (
                    current_hour == 19 and current_minute == 0
                ):
                    await send_questionnaire_to_user(
                        bot,
                        telegram_id,
                        "⚡️ Пожалуйста, выполните задание 'Приседания': /squats",
                        "/squats",
                    )

                if day_of_program == 9 and (current_hour == 19 and current_minute == 0):
                    await send_questionnaire_to_user(
                        bot,
                        telegram_id,
                        "‍👦 Пожалуйста, выполните задание 'Вращения головой': /neck",
                        "/neck",
                    )

                if day_of_program == 27 and (
                    current_hour == 19 and current_minute == 0
                ):
                    await send_questionnaire_to_user(
                        bot,
                        telegram_id,
                        "⚖️ Пожалуйста, выполните задание 'Баланс': /balance",
                        "/balance",
                    )
                if day_of_program == 15 and (
                    current_hour == 10 and current_minute == 0
                ):
                    await send_questionnaire_to_user(
                        bot,
                        telegram_id,
                        "⚡️ Пожалуйста, выполните задание 'Планка': /plank",
                        "/plank",
                    )
                if day_of_program == 12 and (
                    current_hour == 18 and current_minute == 30
                ):
                    await send_questionnaire_to_user(
                        bot,
                        telegram_id,
                        "🫳 Пожалуйста, выполните задание 'Поднятие объекта': /picking_up",
                        "/picking_up",
                    )

                if day_of_program == 9 and (
                    current_hour == 10 and current_minute == 30
                ):
                    await send_questionnaire_to_user(
                        bot,
                        telegram_id,
                        "🦶 Пожалуйста, выполните задание 'Фото стоп': /feet",
                        "/feet",
                    )

                if day_of_program == 23 and (
                    current_hour == 19 and current_minute == 0
                ):
                    await send_questionnaire_to_user(
                        bot,
                        telegram_id,
                        "🦶 Пожалуйста, выполните задание 'Фото стоп': /feet",
                        "/feet",
                    )

                if day_of_program == 15 and (
                    current_hour == 9 and current_minute == 30
                ):
                    await send_questionnaire_to_user(
                        bot,
                        telegram_id,
                        "👁️ Пожалуйста, выполните задание 'Микрофото глаза': /eye",
                        "/eye",
                    )
                if day_of_program in [1, 30] and (
                    current_hour == 20 and current_minute == 0
                ):
                    await send_questionnaire_to_user(
                        bot,
                        telegram_id,
                        "⌚ Пожалуйста, выполните задание 'Данные с носимого устройства': /wearable_data",
                        "/wearable_data",
                    )

                if day_of_program == 2 and (current_hour == 19 and current_minute == 0):
                    await send_questionnaire_to_user(
                        bot,
                        telegram_id,
                        "📱 Пожалуйста, выполните задание 'Рассказ о себе': /speech",
                        "/speech",
                    )
                if day_of_program == 3 and (current_hour == 19 and current_minute == 0):
                    await send_questionnaire_to_user(
                        bot,
                        telegram_id,
                        "🧑‍⚕️ Пожалуйста, выполните задание 'Обследования за 3 месяца': /checkups",
                        "/checkups",
                    )
                if day_of_program == 4 and (current_hour == 12 and current_minute == 0):
                    await send_questionnaire_to_user(
                        bot,
                        telegram_id,
                        "🩸️ Пожалуйста, выполните задание 'Сдача анализов крови': /blood",
                        "/blood",
                    )
                if day_of_program in [7, 14, 21, 28] and (
                    current_hour == 9 and current_minute == 0
                ):
                    await send_questionnaire_to_user(
                        bot,
                        telegram_id,
                        "️❤️ Пожалуйста, выполните задание 'Измерения давления и пульса': /pressure",
                        "/pressure",
                    )
                if day_of_program == 13 and (
                    current_hour == 19 and current_minute == 0
                ):
                    await send_questionnaire_to_user(
                        bot,
                        telegram_id,
                        "🫁 Пожалуйста, выполните задание 'Дыхание после нагрузки': /breathing",
                        "/breathing",
                    )

                if day_of_program == 24 and (
                    current_hour == 19 and current_minute == 0
                ):
                    await send_questionnaire_to_user(
                        bot,
                        telegram_id,
                        "🫁 Пожалуйста, выполните задание 'Дыхание в покое': /rest_breathing",
                        "/rest_breathing",
                    )
                if day_of_program == 25 and (
                    current_hour == 9 and current_minute == 30
                ):
                    await send_questionnaire_to_user(
                        bot,
                        telegram_id,
                        "👅 Пожалуйста, выполните задание 'Фото языка утром': /tongue",
                        "/tongue",
                    )
                if day_of_program == 26 and (
                    current_hour == 19 and current_minute == 0
                ):
                    await send_questionnaire_to_user(
                        bot,
                        telegram_id,
                        "😁 Пожалуйста, выполните задание 'Запись смеха/улыбки': /laughter",
                        "/laughter",
                    )

            except Exception as e:
                logger.error(
                    f"Error processing patient {patient.get('telegram_id')}: {e}"
                )
                if use_test_data:
                    raise

        await asyncio.gather(*(process_patient(p) for p in patients))

    except Exception as e:
        logger.error(f"Critical error in questionnaire scheduler: {e}")
        raise
    finally:
        if not use_test_data and conn:
            await conn.close()


async def check_and_send_daily_questionnaire(
    bot: Bot, conn, user_id: int, today: datetime.date
):
    """Проверяет и отправляет ежедневную анкету, если она еще не заполнена"""
    try:
        filled = await conn.fetchval(
            """
            SELECT 1 FROM patient_history ph
            JOIN patients p ON ph.patient_id = p.id
            WHERE p.telegram_id = $1
            AND DATE(ph.created_at AT TIME ZONE p.timezone) = $2
            LIMIT 1
        """,
            user_id,
            today,
        )
        if not filled:
            await send_questionnaire_to_user(
                bot,
                user_id,
                "⏰ Время заполнить ежедневную анкету!\nВведите /daily чтобы начать",
                "/daily",
            )
    except Exception as e:
        logger.error(f"Error checking daily questionnaire for {user_id}: {e}")


def setup_scheduler(bot: Bot):
    """Настройка планировщика"""
    scheduler.add_job(
        check_and_send_questionnaires,
        CronTrigger(minute="*", hour="*"),
        args=[bot],
        id="hourly_questionnaire_check",
        replace_existing=True,
    )
    scheduler.start()
