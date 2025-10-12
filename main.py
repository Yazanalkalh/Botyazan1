# -*- coding: utf-8 -*-

import logging
import threading
from aiogram import Bot, Dispatcher, executor
from aiogram_mongo import MongoStorage # <-- استيراد الأرشيف الدائم

import web_server
from config import TELEGRAM_TOKEN, MONGO_URI # <-- استيراد رابط القاعدة
from bot.utils.loader import auto_register_handlers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def on_startup(dispatcher: Dispatcher):
    """يتم التنفيذ عند بدء تشغيل البوت."""
    auto_register_handlers(dispatcher)
    logger.info("البوت جاهز للعمل.")

if __name__ == '__main__':
    bot = Bot(token=TELEGRAM_TOKEN)
    
    # --- الإصلاح الجذري: استخدام MongoDB للتخزين ---
    # هذا يضمن أن كل المحادثات والحالات يتم حفظها بشكل دائم
    storage = MongoStorage(uri=MONGO_URI)
    
    dp = Dispatcher(bot, storage=storage)

    # تشغيل خادم الويب في الخلفية
    flask_thread = threading.Thread(target=web_server.run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    logger.info("خادم الويب قيد التشغيل...")

    # تشغيل البوت
    executor.start_polling(
        dispatcher=dp,
        skip_updates=True,
        on_startup=on_startup
    )
