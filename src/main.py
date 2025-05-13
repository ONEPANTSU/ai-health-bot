import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher

from src import config
from src.bot.handlers import router


async def main():
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(router)

    print("🤖 Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
