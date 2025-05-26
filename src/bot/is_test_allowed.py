from datetime import datetime


def is_test_day_allowed(test_name: str) -> bool:
    """Проверяет, можно ли проходить тест сегодня"""
    today = datetime.now().day
    test_schedule = {
        "greeting": [1],
        "health": [4],
        "nutrition": [5, 8],
        "body": [10],
        "supplements": [11],
        "mindfulness": [14],
        "safety": [16],
        "close_environment": [18],
    }
    return today in test_schedule.get(test_name, [])
