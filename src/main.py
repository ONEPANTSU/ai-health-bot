import asyncio
from aiogram import Bot, Dispatcher

import config
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

    print("🤖 Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
