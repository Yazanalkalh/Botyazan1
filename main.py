# -*- coding: utf-8 -*-

import os
import asyncio
import logging
from aiohttp import web

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.mongo import MongoStorage

# --- نستورد المتغيرات والمحركات الجديدة ---
from bot.core.bot_data import START_TIME
from bot.core.scheduler import scheduler, load_pending_jobs

from config import TELEGRAM_TOKEN, MONGO_URI
from bot.utils.loader import discover_handlers
from bot.database.manager import db
from bot.middlewares.admin_filter import IsAdminFilter
from bot.middlewares.ban_middleware import BanMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- دالة لتشغيل البوت ---
async def start_bot():
    """يقوم بإعداد وتشغيل البوت بالترتيب الصحيح للمعالجات."""
    bot = Bot(token=TELEGRAM_TOKEN)
    storage = MongoStorage(uri=MONGO_URI, db_name="aiogram_fsm")
    dp = Dispatcher(bot, storage=storage)

    dp.filters_factory.bind(IsAdminFilter)
    dp.middleware.setup(BanMiddleware())

    if not await db.connect_to_database(MONGO_URI):
        logger.critical("❌ فشل الاتصال بقاعدة البيانات، إيقاف البوت.")
        return

    # --- 💡 الإضافة الجديدة: إعادة تحميل المهام المجدولة 💡 ---
    await load_pending_jobs(bot)

    all_handler_modules = discover_handlers()
    logger.info("🚦 بدء تسجيل المعالجات...")
    
    for module in all_handler_modules:
        if module.__name__.endswith("messages"): continue 
        for attr_name in dir(module):
            if attr_name.startswith("register_"):
                getattr(module, attr_name)(dp)
                logger.info(f"✅ [أولوية عالية] تم تسجيل: {attr_name}")

    for module in all_handler_modules:
        if module.__name__.endswith("messages"):
            for attr_name in dir(module):
                if attr_name.startswith("register_"):
                    getattr(module, attr_name)(dp)
                    logger.info(f"✅ [أولوية منخفضة] تم تسجيل: {attr_name}")
            break

    logger.info("✅ البوت جاهز للعمل وينتظر الرسائل...")
    await dp.start_polling()

# --- (بقية الملف كما هو) ---
async def handle_root(request):
    return web.Response(text="Bot is alive and running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_root)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    try:
        await site.start()
        logger.info(f"🌐 خادم الويب يعمل على المنفذ {port}")
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()

async def main():
    # --- 💡 الإضافة الجديدة: بدء تشغيل محرك الجدولة 💡 ---
    scheduler.start()
    
    await asyncio.gather(
        start_web_server(),
        start_bot()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("...إيقاف البوت")
        scheduler.shutdown() # إيقاف آمن للمجدول
