import os
from dotenv import load_dotenv

load_dotenv("./.env")


BOT_TOKEN = os.getenv("BOT_TOKEN")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
S3_URL = os.getenv("S3_URL")
S3_BUCKET = os.getenv("S3_BUCKET")

POSTGRES_DSN = os.getenv("POSTGRES_DSN")
