import asyncpg
from src import config


async def get_db_connection():
    return await asyncpg.connect(dsn=config.POSTGRES_DSN)
