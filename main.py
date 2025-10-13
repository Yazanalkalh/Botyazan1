# -*- coding: utf-8 -*-

import asyncio
import logging
import threading

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.mongo import MongoStorage

import web_server
from config import TELEGRAM_TOKEN, MONGO_URI
from bot.database.manager import db

# --- استيراد وظائف التسجيل ---
from bot.handlers.user.start import register_start_handlers
from bot.handlers.user.callbacks import register_callback_handlers
from bot.handlers.user.messages import register_messages_handler # تم التغيير هنا
from bot.handlers.admin.communication_handler import register_communication_handlers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

storage = MongoStorage(uri=MONGO_URI)
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot, storage=storage)

async def on_startup(dispatcher: Dispatcher):
    """يتم تنفيذ هذه الوظيفة عند بدء تشغيل البوت."""
    logger.info("الاتصال بقاعدة البيانات...")
    await db.connect_to_database(uri=MONGO_URI)
    
    # --- تسجيل المعالجات بالترتيب الصحيح ---
    
    # 1. المعالجات المتخصصة أولاً (الأوامر والأزرار)
    register_start_handlers(dispatcher)
    register_callback_handlers(dispatcher)
    
    # 2. معالجات المدير
    register_communication_handlers(dispatcher)
    
    # 3. المعالج العام (catch-all) يجب أن يكون الأخير دائماً
    register_messages_handler(dispatcher)
    
    logger.info("البوت جاهز للعمل بشكل كامل.")

# ... (بقية الكود يبقى كما هو)
async def on_shutdown(dispatcher: Dispatcher):
    logger.warning('إيقاف البوت...')

if __name__ == '__main__':
    flask_thread = threading.Thread(target=web_server.run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    logger.info("خادم الويب Flask قيد التشغيل...")

    executor.start_polling(
        dispatcher=dp,
        skip_updates=True,
        on_startup=on_startup,
        on_shutdown=on_shutdown
    )
