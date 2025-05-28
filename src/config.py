import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv("./.env")


BOT_TOKEN = os.getenv("BOT_TOKEN")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
S3_URL = os.getenv("S3_URL")
S3_BUCKET = os.getenv("S3_BUCKET")

POSTGRES_DSN = os.getenv("POSTGRES_DSN")

QUESTION_TEXT_MAP = json.loads(Path("question_map.json").read_text(encoding="utf-8"))
QUESTION_TYPE_PROMPTS = json.loads(Path("question_type_prompts.json").read_text(encoding="utf-8"))