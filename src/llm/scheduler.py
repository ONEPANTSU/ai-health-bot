
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging
import pytz

from src.bot.handlers.testing import get_global_testing_start_date
from src.db.connection import get_db_connection
from src.db.patient_repository import get_all_patients
from src.llm.service import dispatch_weekly_to_llm, dispatch_to_llm

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


async def run_daily_digest(bot: Bot):
    logger.info("Starting daily digest task...")
    conn = await get_db_connection()
    patients = await get_all_patients(conn)

    for patient in patients:
        tz = pytz.timezone(patient.get("timezone", "Europe/Moscow"))
        now = datetime.now(tz)
        if now.hour == 21:  # например, отправлять в 21:00 локального времени
            try:
                # Мы предполагаем, что у пациента есть текущая анкета/медиа (можно расширить)
                message = await dispatch_to_llm(
                    username=patient["username"],
                    telegram_id=patient["telegram_id"],
                    current_record={},  # тут ты можешь брать последний ответ или собирать срез
                    media_urls=[],
                )
                await bot.send_message(chat_id=patient["telegram_id"], text=message)
            except Exception as e:
                logger.error(f"Daily dispatch failed for {patient['telegram_id']}: {e}")

async def run_weekly_digest(bot: Bot):
    logger.info("Starting weekly digest task...")
    conn = await get_db_connection()
    patients = await get_all_patients(conn)

    start_date = await get_global_testing_start_date()
    if not start_date:
        logger.warning("Global testing start date not set. Skipping weekly digest.")
        return

    for patient in patients:
        tz = pytz.timezone(patient.get("timezone", "Europe/Moscow"))
        now = datetime.now(tz).date()

        days_passed = (now - start_date.date()).days
        if days_passed < 0:
            continue

        current_week = days_passed // 7 + 1
        is_last_day_of_week = (days_passed + 1) % 7 == 0

        if is_last_day_of_week and 1 <= current_week <= 4:
            try:
                message = await dispatch_weekly_to_llm(
                    username=patient["username"],
                    telegram_id=patient["telegram_id"],
                    week_number=current_week,
                    media_urls=[],
                )
                await bot.send_message(chat_id=patient["telegram_id"], text=message)
            except Exception as e:
                logger.error(f"Weekly dispatch failed for {patient['telegram_id']}: {e}")

def setup_llm_scheduler(bot: Bot):
    scheduler.add_job(run_daily_digest, CronTrigger(minute=0, hour="*"), kwargs={"bot": bot})
    scheduler.add_job(run_weekly_digest, CronTrigger(minute=0, hour="*"), kwargs={"bot": bot})
    scheduler.start()