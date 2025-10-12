# -*- coding: utf-8 -*-
from aiogram import types, Dispatcher

async def start_command(message: types.Message):
    """يستجيب لأمر /start."""
    await message.answer("أهلاً بك! البوت يعمل بالهيكل النهائي والمستقر.")

def register_start_handlers(dp: Dispatcher):
    """وظيفة التسجيل التلقائي."""
    dp.register_message_handler(start_command, commands=["start"])
