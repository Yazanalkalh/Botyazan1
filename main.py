# -*- coding: utf-8 -*-

import asyncio
import logging
import threading

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

import web_server
from config import TELEGRAM_TOKEN, MONGO_URI
from bot.database.manager import db

# --- استيراد وتسجيل المعالجات ---
from bot.handlers.user.start import register_start_handlers

# --- إعداد البوت ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FSM Storage for conversations
storage = MemoryStorage()

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot, storage=storage)

async def on_startup(dispatcher: Dispatcher):
    """
    يتم تنفيذ هذه الوظيفة عند بدء تشغيل البوت.
    """
    logger.info("الاتصال بقاعدة البيانات...")
    await db.connect_to_database(uri=MONGO_URI)
    
    # تسجيل كل المعالجات هنا
    register_start_handlers(dispatcher)
    
    logger.info("البوت جاهز للعمل.")

async def on_shutdown(dispatcher: Dispatcher):
    """
    يتم تنفيذ هذه الوظيفة عند إيقاف البوت.
    """
    logger.warning('إيقاف البوت...')
    # هنا يمكن إضافة كود لتنظيف الموارد إذا احتجنا

if __name__ == '__main__':
    # 1. تشغيل Flask في الخلفية
    flask_thread = threading.Thread(target=web_server.run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    logger.info("خادم الويب Flask قيد التشغيل...")

    # 2. تشغيل البوت باستخدام aiogram executor
    executor.start_polling(
        dispatcher=dp,
        skip_updates=True,
        on_startup=on_startup,
        on_shutdown=on_shutdown
    )
