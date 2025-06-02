from datetime import datetime
from aiogram import Router

# from src.bot.handlers.testing import get_testing_start_date

router = Router()


async def is_test_day_allowed(test_name: str) -> bool:
    """Проверяет, можно ли проходить тест сегодня с учетом даты старта"""
    # start_date = await get_testing_start_date()
    start_date = datetime.now()
    if not start_date:
        return False

    days_passed = (datetime.now() - start_date).days

    test_schedule = {
        "greeting": [0],
        "health": [3],
        "nutrition": [4, 7],
        "body": [9],
        "supplements": [10],
        "mindfulness": [13],
        "safety": [15],
        "close_environment": [17],
    }

    return days_passed in test_schedule.get(test_name, [])


async def is_task_day_allowed(task_name: str) -> bool:
    """Проверяет, можно ли выполнять задание сегодня с учетом даты старта"""
    # start_date = await get_testing_start_date()
    start_date = datetime.now()
    if not start_date:
        return False

    days_passed = (datetime.now() - start_date).days

    # Расписание заданий относительно даты старта
    task_schedule = {
        # "face_photo": [1, 21],  # Через 1
        # "hands_photo": [19],
        # "fullbody_photo": [2, 16],
        # "walking": [4, 18],
        # "running": [7, 28],
        # "squats": [9],
        # "neck_exercise": [8],
        # "balance": [26],
        # "plank": [14],
        # "pickup_object": [11],
        # "feet_photo": [8, 22],
        # "eye_photo": [14],
    }

    return days_passed in task_schedule.get(task_name, [])
