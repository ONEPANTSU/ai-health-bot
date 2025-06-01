from aiogram import Bot
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.db.connection import get_db_connection

scheduler = AsyncIOScheduler()


async def get_user_timezone(user_id: int) -> str:
    """Получает часовой пояс пользователя из базы данных"""
    try:
        conn = await get_db_connection()
        tz = await conn.fetchval(
            "SELECT timezone FROM patients WHERE telegram_id = $1", user_id
        )
        return tz if tz else "Europe/Moscow"  # Значение по умолчанию
    except Exception as e:
        print(f"Ошибка получения часового пояса: {e}")
        return "Europe/Moscow"


async def send_daily_reminder(bot: Bot):
    """Функция для рассылки напоминаний всем активным пользователям"""
    conn = await get_db_connection()
    active_users = await conn.fetch(
        "SELECT telegram_id FROM patients WHERE is_active = true"
    )

    for user in active_users:
        try:
            await bot.send_message(
                chat_id=user["telegram_id"],
                text="⏰ Время заполнить ежедневную анкету!\nВведите /daily чтобы начать",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="/daily")]], resize_keyboard=True
                ),
            )
        except Exception as e:
            print(f"Ошибка отправки пользователю {user['telegram_id']}: {e}")


async def send_greeting_questionnaire(bot: Bot):
    conn = await get_db_connection()
    users = await conn.fetch("""
        SELECT telegram_id FROM patients 
        WHERE NOT EXISTS (
            SELECT 1 FROM patient_history 
            WHERE patient_history.patient_id = patients.id 
            AND patient_history.answers->>'questionnaire_type' = 'greeting'
        )
        AND is_active = true
    """)

    for user in users:
        try:
            await bot.send_message(
                chat_id=user["telegram_id"],
                text="⏰ Пожалуйста, заполните анкету приветствия: /greeting",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="/greeting")]],
                    resize_keyboard=True,
                ),
            )
        except Exception as e:
            print(f"Ошибка отправки пользователю {user['telegram_id']}: {e}")


async def send_body_questionnaire(bot: Bot):
    conn = await get_db_connection()
    # Отправляем только тем, кто заполнил анкету приветствия
    users = await conn.fetch("""
        SELECT p.telegram_id FROM patients p
        WHERE EXISTS (
            SELECT 1 FROM patient_history ph
            WHERE ph.patient_id = p.id
            AND ph.answers->>'questionnaire_type' = 'greeting'
        )
        AND NOT EXISTS (
            SELECT 1 FROM patient_history ph
            WHERE ph.patient_id = p.id
            AND ph.answers->>'questionnaire_type' = 'body_shape'
            AND DATE(ph.created_at) = CURRENT_DATE
        )
        AND p.is_active = true
    """)

    for user in users:
        try:
            await bot.send_message(
                chat_id=user["telegram_id"],
                text="📏 Пожалуйста, заполните анкету телосложения: /body_measurements",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="/body_measurements")]],
                    resize_keyboard=True,
                ),
            )
        except Exception as e:
            print(f"Ошибка отправки пользователю {user['telegram_id']}: {e}")


async def send_health_questionnaire(bot: Bot):
    conn = await get_db_connection()
    users = await conn.fetch("""
        SELECT p.telegram_id FROM patients p
        WHERE p.is_active = true
        AND NOT EXISTS (
            SELECT 1 FROM patient_history ph
            WHERE ph.patient_id = p.id
            AND ph.answers->>'questionnaire_type' = 'subjective_health'
            AND DATE(ph.created_at) = CURRENT_DATE
        )
    """)

    for user in users:
        try:
            await bot.send_message(
                chat_id=user["telegram_id"],
                text="🏥 Пожалуйста, заполните анкету состояния здоровья: /health",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="/health")]],
                    resize_keyboard=True,
                ),
            )
        except Exception as e:
            print(f"Ошибка отправки пользователю {user['telegram_id']}: {e}")


async def send_nutrition_questionnaire(bot: Bot):
    conn = await get_db_connection()
    users = await conn.fetch("""
        SELECT p.telegram_id FROM patients p
        WHERE p.is_active = true
        AND NOT EXISTS (
            SELECT 1 FROM patient_history ph
            WHERE ph.patient_id = p.id
            AND ph.answers->>'questionnaire_type'= 'nutrition'
            AND DATE(ph.created_at) = CURRENT_DATE
        )
    """)

    for user in users:
        try:
            await bot.send_message(
                chat_id=user["telegram_id"],
                text="🍎 Пожалуйста, заполните анкету питания: /nutrition",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="/nutrition")]],
                    resize_keyboard=True,
                ),
            )
        except Exception as e:
            print(f"Ошибка отправки пользователю {user['telegram_id']}: {e}")


async def send_supplements_questionnaire(bot: Bot):
    conn = await get_db_connection()
    users = await conn.fetch("""
        SELECT p.telegram_id FROM patients p
        WHERE p.is_active = true
        AND NOT EXISTS (
            SELECT 1 FROM patient_history ph
            WHERE ph.patient_id = p.id
            AND ph.answers->>'questionnaire_type' = 'supplements'
            AND DATE(ph.created_at) = CURRENT_DATE
        )
    """)

    for user in users:
        try:
            await bot.send_message(
                chat_id=user["telegram_id"],
                text="💊 Пожалуйста, заполните анкету приема БАДов/витаминов: /supplements",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[
                        [KeyboardButton(text="/supplements")]
                    ],
                    resize_keyboard=True,
                ),
            )
        except Exception as e:
            print(f"Ошибка отправки пользователю {user['telegram_id']}: {e}")


async def send_awareness_quiz(bot: Bot):
    """Отправка анкеты осознанности (медитации)"""
    conn = await get_db_connection()
    users = await conn.fetch("""
        SELECT p.telegram_id FROM patients p
        WHERE p.is_active = true
        AND NOT EXISTS (
            SELECT 1 FROM patient_history ph
            WHERE ph.patient_id = p.id
            AND ph.answers->>'questionnaire_type' = 'mindfulness'
            AND DATE(ph.created_at) = CURRENT_DATE
        )
    """)

    for user in users:
        try:
            await bot.send_message(
                chat_id=user["telegram_id"],
                text="🧘 Пожалуйста, заполните анкету осознанности (медитации): /mindfulness",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="/mindfulness")]],
                    resize_keyboard=True,
                ),
            )
        except Exception as e:
            print(f"Ошибка отправки пользователю {user['telegram_id']}: {e}")


async def send_supplements_quiz(bot: Bot):
    """Отправка анкеты по БАДам/витаминам"""
    conn = await get_db_connection()
    users = await conn.fetch("""
        SELECT p.telegram_id FROM patients p
        WHERE p.is_active = true
        AND NOT EXISTS (
            SELECT 1 FROM patient_history ph
            WHERE ph.patient_id = p.id
            AND ph.answers->>'questionnaire_type' = 'supplements'
            AND DATE(ph.created_at) = CURRENT_DATE
        )
    """)

    for user in users:
        try:
            await bot.send_message(
                chat_id=user["telegram_id"],
                text="💊 Пожалуйста, заполните анкету по БАДам/витаминам: /supplements",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="/supplements")]],
                    resize_keyboard=True,
                ),
            )
        except Exception as e:
            print(f"Ошибка отправки пользователю {user['telegram_id']}: {e}")


async def send_safety_support_quiz(bot: Bot):
    """Отправка анкеты безопасности и поддержки"""
    conn = await get_db_connection()
    users = await conn.fetch("""
        SELECT p.telegram_id FROM patients p
        WHERE p.is_active = true
        AND NOT EXISTS (
            SELECT 1 FROM patient_history ph
            WHERE ph.patient_id = p.id
            AND ph.answers->>'questionnaire_type' = 'safety_support'
            AND DATE(ph.created_at) = CURRENT_DATE
        )
    """)

    for user in users:
        try:
            await bot.send_message(
                chat_id=user["telegram_id"],
                text="🛡️ Пожалуйста, заполните анкету безопасности и поддержки: /safety",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="/safety")]],
                    resize_keyboard=True,
                ),
            )
        except Exception as e:
            print(f"Ошибка отправки пользователю {user['telegram_id']}: {e}")


async def send_close_environment_quiz(bot: Bot):
    """Отправка анкеты близкого окружения"""
    conn = await get_db_connection()
    users = await conn.fetch("""
        SELECT p.telegram_id FROM patients p
        WHERE p.is_active = true
        AND NOT EXISTS (
            SELECT 1 FROM patient_history ph
            WHERE ph.patient_id = p.id
            AND ph.answers->>'questionnaire_type' = 'close_environment'
            AND DATE(ph.created_at) = CURRENT_DATE
        )
    """)

    for user in users:
        try:
            await bot.send_message(
                chat_id=user["telegram_id"],
                text="👨‍👩‍👧‍👦 Пожалуйста, заполните анкету близкого окружения: /close_environment",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="/close_environment")]],
                    resize_keyboard=True,
                ),
            )
        except Exception as e:
            print(f"Ошибка отправки пользователю {user['telegram_id']}: {e}")


def setup_scheduler(bot: Bot):
    """Настройка планировщика"""
    scheduler.add_job(
        send_daily_reminder,
        "cron",
        hour=10,
        minute=0,
        args=[bot],
        timezone="Europe/Moscow",
        id="daily_reminder",
        replace_existing=True,
    )
    scheduler.add_job(
        send_greeting_questionnaire,
        "cron",
        day=1,
        hour=10,
        minute=0,
        args=[bot],
        timezone="Europe/Moscow",
        id="monthly_greeting",
        replace_existing=True,
    )
    scheduler.add_job(
        send_health_questionnaire,
        "cron",
        day=4,
        hour=19,
        minute=0,
        args=[bot],
        timezone="Europe/Moscow",
        id="monthly_health",
        replace_existing=True,
    )
    scheduler.add_job(
        send_nutrition_questionnaire,
        "cron",
        day="5,8",
        hour=19,
        minute=0,
        args=[bot],
        timezone="Europe/Moscow",
        id="monthly_nutrition",
        replace_existing=True,
    )
    scheduler.add_job(
        send_body_questionnaire,
        "cron",
        day=10,
        hour=18,
        minute=30,
        args=[bot],
        timezone="Europe/Moscow",
        id="monthly_body",
    )

    scheduler.add_job(
        send_supplements_questionnaire, "cron", day=11, hour=19, minute=0, args=[bot]
    )
    scheduler.add_job(
        send_awareness_quiz,
        "cron",
        day=14,
        hour=18,
        minute=30,
        args=[bot],
        timezone="Europe/Moscow",
        id="monthly_awareness",
    )
    scheduler.add_job(
        send_safety_support_quiz,
        "cron",
        day=16,
        hour=19,
        minute=0,
        args=[bot],
        timezone="Europe/Moscow",
        id="monthly_safety_support",
    )
    scheduler.add_job(
        send_close_environment_quiz,
        "cron",
        day=18,
        hour=19,
        minute=0,
        args=[bot],
        timezone="Europe/Moscow",
        id="monthly_close_environment",
    )

    scheduler.start()
