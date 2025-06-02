import asyncio
from aiogram import Dispatcher


from aiogram.types import BotCommand
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
from src.bot_instance import bot
from src.llm.scheduler import setup_llm_scheduler
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


async def main():
    commands = [
        BotCommand(command="start", description="Начать общение с ботом (Регистрация)"),
        BotCommand(command="set_timezone", description="Установить часовой пояс"),
        BotCommand(command="greeting", description="Начать анкету приветствия"),
        BotCommand(command="daily", description="Начать ежедневную анкету"),
        BotCommand(command="mindfulness", description="Начать анкету осознанности"),
        BotCommand(
            command="body_measurements", description="Начать анкету телосложения"
        ),
        BotCommand(
            command="close_environment", description="Начать анкету о близком окружении"
        ),
        BotCommand(command="nutrition", description="Начать анкету питания"),
        BotCommand(
            command="safety", description="Начать анкету безопасности и поддержки"
        ),
        BotCommand(
            command="subjective_health",
            description="Начать анкету субъективного здоровья",
        ),
        BotCommand(command="supplements", description="Начать анкету добавок"),
        BotCommand(command="balance", description="Начать задание 'Баланс'"),
        BotCommand(command="eye", description="Начать задание 'Микрофото глаза'"),
        BotCommand(command="face", description="Начать задание 'Фото лица'"),
        BotCommand(command="feet", description="Начать задание 'Фото стоп'"),
        BotCommand(
            command="full_body", description="Начать задание 'Фото в полный рост'"
        ),
        BotCommand(command="hands", description="Начать задание 'Фото рук'"),
        BotCommand(command="neck", description="Начать задание 'Вращение головой'"),
        BotCommand(
            command="picking_up", description="Начать задание 'Поднятие объекта'"
        ),
        BotCommand(command="plank", description="Начать задание 'Планка'"),
        BotCommand(command="running", description="Начать задание 'Бег'"),
        BotCommand(command="squats", description="Начать задание 'Приседания'"),
        BotCommand(command="walking", description="Начать задание 'Хождение'"),
    ]
    await bot.set_my_commands(commands)

    dp = Dispatcher()
    setup_scheduler(bot)
    setup_llm_scheduler(bot)

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
