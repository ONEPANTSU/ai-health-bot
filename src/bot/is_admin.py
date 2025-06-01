from aiogram import types
from aiogram.filters import Filter

ADMINS = [490473570, 944830799]


class IsAdmin(Filter):
    async def __call__(self, message: types.Message) -> bool:
        return message.from_user.id in ADMINS
