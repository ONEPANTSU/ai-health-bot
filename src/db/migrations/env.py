from alembic import context
from logging.config import fileConfig
import os
from sqlalchemy import engine_from_config, pool

from dotenv import load_dotenv

load_dotenv(".env")

config = context.config
fileConfig(config.config_file_name)

# подключение через DSN
config.set_main_option("sqlalchemy.url", os.getenv("POSTGRES_DSN_SYNC"))


def run_migrations_offline():
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
