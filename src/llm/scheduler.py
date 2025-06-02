import asyncio
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
import logging
import pytz

from src.bot.handlers.testing import get_global_testing_start_date
from src.db.connection import get_db_connection
from src.db.patient_repository import get_all_patients, get_all_records_by_user
from src.llm.service import dispatch_weekly_to_llm, dispatch_to_llm

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


async def run_daily_digest(bot: Bot):
    logger.info("Starting daily digest task...")
    conn = await get_db_connection()
    patients = await get_all_patients(conn)

    async def handle_patient(patient):
        try:
            tz = pytz.timezone(patient.get("timezone", "Europe/Moscow"))
            now = datetime.now(tz)

            if now.hour != 23:
                return

            telegram_id = patient["telegram_id"]
            username = patient["username"]

            utc_now = datetime.utcnow()
            today_start = datetime(utc_now.year, utc_now.month, utc_now.day)
            today_end = today_start + timedelta(days=1)

            records = await get_all_records_by_user(
                telegram_id, conn, today_start, today_end
            )
            if not records:
                logger.info(f"No records for {telegram_id}")
                return

            for record in records:
                message = await dispatch_to_llm(
                    username=username,
                    telegram_id=telegram_id,
                    current_record=record,
                    media_urls=record.get("s3_files", []),
                )
                await bot.send_message(chat_id=telegram_id, text=message)

        except Exception as e:
            logger.exception(f"Failed for {patient['telegram_id']}: {e}")

    await asyncio.gather(*(handle_patient(p) for p in patients))


async def run_weekly_digest(bot: Bot):
    logger.info("Starting weekly digest task...")
    conn = await get_db_connection()
    patients = await get_all_patients(conn)

    start_date = await get_global_testing_start_date()
    if not start_date:
        logger.warning("Global testing start date not set. Skipping weekly digest.")
        return

    async def handle_patient(patient):
        try:
            tz = pytz.timezone(patient.get("timezone", "Europe/Moscow"))
            local_start_date = start_date.astimezone(tz).date()
            now = datetime.now(tz).date()

            days_passed = (now - local_start_date).days
            if days_passed < 0:
                return

            current_week = days_passed // 7 + 1
            is_last_day_of_week = (days_passed + 1) % 7 == 0

            if is_last_day_of_week and 1 <= current_week <= 4:
                message = await dispatch_weekly_to_llm(
                    username=patient["username"],
                    telegram_id=patient["telegram_id"],
                    week_number=current_week,
                    media_urls=[],
                )
                await bot.send_message(chat_id=patient["telegram_id"], text=message)

        except Exception as e:
            logger.error(f"Weekly dispatch failed for {patient['telegram_id']}: {e}")

    await asyncio.gather(*(handle_patient(p) for p in patients))


def setup_llm_scheduler(bot: Bot):
    # scheduler.add_job(
    #     run_daily_digest, CronTrigger(minute="0", hour="*"), kwargs={"bot": bot}
    # )
    scheduler.add_job(
        run_weekly_digest, CronTrigger(minute="0", hour="*"), kwargs={"bot": bot}
    )
    scheduler.start()
