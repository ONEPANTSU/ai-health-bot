import asyncio
from aiogram import Bot, Dispatcher

from src import config
from src.bot.scheduler import setup_scheduler
from src.bot.handlers.greeting_quiz import router as greeting_router
from src.bot.handlers.daily_quiz import router as daily_router
from src.bot.handlers.nutrition_quiz import router as nutrition_router
from src.bot.handlers.body_shape_quiz import router as body_shape_router
from src.bot.handlers.supplements_quiz import router as supplements_router
from src.bot.handlers.safety_support_quiz import router as safety_support_router
from src.bot.handlers.subjective_health_quiz import router as subjective_health_router
from src.bot.handlers.awareness_quiz import router as awareness_router
from src.bot.handlers.close_enviroment_quiz import router as close_environment_router
from src.bot.handlers.tasks.running_video import router as running_video_router
from src.bot.handlers.tasks.face_photo import router as face_photo_router
from src.bot.handlers.tasks.full_height_photos import router as full_height_photo_router
from src.bot.handlers.tasks.walking_video import router as walking_router
from src.bot.handlers.tasks.feet_photo import router as feet_photo_router
from src.bot.handlers.tasks.neck_and_shoulders_video import (
    router as neck_and_shoulder_router,
)
from src.bot.handlers.tasks.squats_video import router as squats_video_router
from src.bot.handlers.tasks.picking_up_video import router as picking_up_video_router
from src.bot.handlers.tasks.hands_photos import router as hands_photo_router
from src.bot.handlers.tasks.balance_video import router as balance_video_router
from src.bot.handlers.tasks.eye_photo import router as eye_photo_router
from src.bot.handlers.tasks.plank_video import router as plank_video_router
from src.bot.handlers.timezone import router as timezone_router
from src.bot.handlers.testing import router as testing_router


async def main():
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()
    setup_scheduler(bot)

    dp.include_router(greeting_router)
    dp.include_router(daily_router)
    dp.include_router(nutrition_router)
    dp.include_router(body_shape_router)
    dp.include_router(supplements_router)
    dp.include_router(safety_support_router)
    dp.include_router(subjective_health_router)
    dp.include_router(awareness_router)
    dp.include_router(close_environment_router)
    dp.include_router(running_video_router)
    dp.include_router(face_photo_router)
    dp.include_router(full_height_photo_router)
    dp.include_router(walking_router)
    dp.include_router(feet_photo_router)
    dp.include_router(neck_and_shoulder_router)
    dp.include_router(squats_video_router)
    dp.include_router(picking_up_video_router)
    dp.include_router(hands_photo_router)
    dp.include_router(balance_video_router)
    dp.include_router(eye_photo_router)
    dp.include_router(plank_video_router)
    dp.include_router(timezone_router)
    dp.include_router(testing_router)

    print("🤖 Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
