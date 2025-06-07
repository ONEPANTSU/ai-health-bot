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
    ALCOHOL = State()
    COFFEE = State()
    WATER = State()


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


class FacePhotoStates(StatesGroup):
    waiting_face_photo = State()


class FeetPhotoStates(StatesGroup):
    waiting_feet_photo = State()


class FullbodyPhotoStates(StatesGroup):
    waiting_fullbody_photo = State()


class WalkingVideoStates(StatesGroup):
    waiting_walking_video = State()


class RunningVideoStates(StatesGroup):
    waiting_running_video = State()


class SquatsVideoStates(StatesGroup):
    waiting_squats_video = State()


class NeckVideoStates(StatesGroup):
    waiting_neck_video = State()


class PickUpObjectStates(StatesGroup):
    waiting_pickup_video = State()


class HandsPhotoStates(StatesGroup):
    waiting_hands_photo = State()


class BalanceTestStates(StatesGroup):
    waiting_balance_video = State()


class EyePhotoStates(StatesGroup):
    waiting_eye_photo = State()


class PlankStates(StatesGroup):
    waiting_plank_video = State()


class TimezoneStates(StatesGroup):
    waiting_timezone = State()


class TestingStates(StatesGroup):
    testing_started = State()


class DeviceData(StatesGroup):
    PROCESSING = State()

class ReactionStates(StatesGroup):
    PROCESSING = State()
    
class FeedbackStates(StatesGroup):
    PROCESSING = State()

class SpeechVideoStates(StatesGroup):
    waiting_video = State()


class ExaminationStates(StatesGroup):
    waiting_examination_files = State()


class PressurePulseStates(StatesGroup):
    waiting_pressure_pulse = State()


class BreathingTestStates(StatesGroup):
    waiting_breathing_video = State()


class RestBreathingStates(StatesGroup):
    waiting_rest_breathing_video = State()


class TonguePhotoStates(StatesGroup):
    waiting_tongue_photo = State()


class LaughterVideoStates(StatesGroup):
    waiting_laughter_video = State()
