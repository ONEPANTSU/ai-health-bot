from aiogram.fsm.state import StatesGroup, State


class DailyQuestionnaire(StatesGroup):
    SLEEP_TIME = State()
    SLEEP_QUALITY = State()
    WAKE_UP_COUNT = State()
    MORNING_FEELING = State()
    DAY_SLEEPINESS = State()
    SLEEP_RATING = State()
    STRESS_LEVEL = State()
    STRESS_SOURCE = State()
    MOOD = State()
    JOY = State()
    ENERGY_LEVEL = State()
    FATIGUE_FREQUENCY = State()
    ANXIETY_FREQUENCY = State()
    MOTIVATION_LEVEL = State()
    STEPS_COUNT = State()
    WORKOUT_INTENSITY = State()
    WORKOUT_PAIN = State()
    WORKOUT_PAIN_LOCATION = State()
    FATIGUE_LEVEL = State()
    AFTER_WORK_FEELING = State()


class GreetingQuestionnaire(StatesGroup):
    FULL_NAME = State()
    PHONE = State()
    TELEGRAM_NICK = State()
    AGE = State()
    GENDER = State()
    HEIGHT = State()
    WEIGHT = State()


class BodyQuestionnaire(StatesGroup):
    WAIST = State()
    HIPS = State()
    CHEST = State()


class HealthQuestionnaire(StatesGroup):
    CHRONIC_DISEASES = State()
    DISEASES_DETAILS = State()
    MEDICATION = State()
    MEDICATION_DETAILS = State()
    CHRONIC_PAIN = State()
    PAIN_DETAILS = State()


class NutritionQuestionnaire(StatesGroup):
    BREAKFAST_3DAYS = State()
    LUNCH_3DAYS = State()
    DINNER_3DAYS = State()
    SNACKS_3DAYS = State()
    WATER_INTAKE = State()


class SupplementsQuestionnaire(StatesGroup):
    TAKING_SUPPLEMENTS = State()
    SUPPLEMENTS_DETAILS = State()


class SafetyQuestionnaire(StatesGroup):
    HAS_SUPPORT = State()
    SUPPORT_COUNT = State()
    FEELS_SAFE = State()


class CloseCircleQuestionnaire(StatesGroup):
    RELATIONSHIPS = State()
    RELATIONSHIP_QUALITY = State()
    COMMUNICATION_FREQUENCY = State()


class MindfulnessQuestionnaire(StatesGroup):
    HAS_PRACTICE = State()
    PRACTICE_FREQUENCY = State()
    FOCUS_OBJECT = State()
    CONCENTRATION_DIFFICULTY = State()
    POSITIVE_CHANGES = State()
