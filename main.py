# -*- coding: utf-8 -*-

import os
import asyncio
import logging
from aiohttp import web

from aiogram import Bot, Dispatcher
# --- هذا هو التصحيح الجذري والنهائي ---
from aiogram.contrib.fsm_storage.mongo import MongoStorage

from config import TELEGRAM_TOKEN, MONGO_URI
from bot.utils.loader import auto_register_handlers
from bot.database.manager import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- دالة لتشغيل البوت ---
async def start_bot():
    """يقوم بإعداد وتشغيل البوت."""
    bot = Bot(token=TELEGRAM_TOKEN)
    
    # --- استخدام التخزين الدائم بالطريقة الرسمية والصحيحة ---
    storage = MongoStorage(uri=MONGO_URI, db_name="aiogram_fsm")
    
    dp = Dispatcher(bot, storage=storage)

    # الاتصال بقاعدة البيانات الخاصة بنا
    if not await db.connect_to_database(MONGO_URI):
        logger.critical("❌ فشل الاتصال بقاعدة البيانات، لا يمكن تشغيل البوت.")
        return

    # استدعاء "المفتش الآلي" لتسجيل كل المعالجات
    auto_register_handlers(dp)

    # بدء الاستطلاع لاستقبال الرسائل
    logger.info("✅ البوت جاهز للعمل وينتظر الرسائل...")
    await dp.start_polling()

# --- خادم ويب متزامن (aiohttp) ---
async def handle_root(request):
    """صفحة بسيطة لإبقاء الخدمة نشطة."""
    return web.Response(text="Bot is alive and running!")

async def start_web_server():
    """يبدأ تشغيل خادم الويب بشكل متزامن."""
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

# --- الدالة الرئيسية التي تجمع كل شيء ---
async def main():
    """تشغل خادم الويب والبوت في نفس الوقت."""
    await asyncio.gather(
        start_web_server(),
        start_bot()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("...إيقاف البوت")
