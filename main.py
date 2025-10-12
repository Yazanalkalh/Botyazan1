# -*- coding: utf-8 -*-

import os
import asyncio
import logging
from aiohttp import web

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.mongo import MongoStorage

from config import TELEGRAM_TOKEN, MONGO_URI
from bot.utils.loader import auto_register_handlers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def on_startup(dp: Dispatcher):
    """يتم التنفيذ عند بدء تشغيل البوت."""
    # استدعاء "المفتش الآلي" ليقوم بتسجيل كل شيء
    auto_register_handlers(dp)
    logger.info("البوت جاهز للعمل.")

# --- إعداد خادم الويب aiohttp ---
async def handle_root(request):
    return web.Response(text="Bot is alive!")

async def start_web_server():
    """يبدأ تشغيل خادم الويب بشكل متزامن."""
    app = web.Application()
    app.router.add_get('/', handle_root)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    try:
        await site.start()
        logger.info(f"🌐 خادم الويب يعمل على المنفذ {port}")
        # حلقة لا نهائية لإبقاء الخادم يعمل في الخلفية
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()

async def start_bot():
    """يبدأ تشغيل البوت."""
    bot = Bot(token=TELEGRAM_TOKEN)
    storage = MongoStorage(uri=MONGO_URI)
    dp = Dispatcher(bot, storage=storage)

    await on_startup(dp)
    await dp.start_polling()

async def main():
    """الوظيفة الرئيسية التي تجمع كل شيء."""
    # تشغيل خادم الويب والبوت في نفس الوقت
    await asyncio.gather(
        start_web_server(),
        start_bot(),
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("إيقاف البوت...")
