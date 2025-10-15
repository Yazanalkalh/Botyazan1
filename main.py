# -*- coding: utf-8 -*-

import asyncio
import logging
import os
import re # 💡 إضافة جديدة

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.mongo import MongoStorage
from aiohttp import web

# --- نستورد المتغيرات والمحركات الجديدة ---
from bot.core.scheduler import scheduler, load_pending_jobs

from config import TELEGRAM_TOKEN, MONGO_URI
from bot.utils.loader import discover_handlers
from bot.database.manager import db
from bot.middlewares.admin_filter import IsAdminFilter
from bot.middlewares.ban_middleware import BanMiddleware
from bot.middlewares.antiflood_middleware import AntiFloodMiddleware, register_direct_unban_handler


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)


# --- 💡 دالة الفحص الذاتي الجديدة 💡 ---
async def run_database_integrity_check():
    """
    يقوم بفحص سلامة ملف قاعدة البيانات عند بدء التشغيل لمنع أخطاء الدوال الناقصة.
    سيطبع تقريراً في سجلات Render.
    """
    logger.info(" Gearing up for a database integrity check...")
    
    # 1. الحصول على الدوال المعرّفة في manager.py
    defined_functions = set()
    manager_path = 'bot/database/manager.py'
    try:
        with open(manager_path, 'r', encoding='utf-8') as f:
            content = f.read()
            matches = re.findall(r'async def\s+(\w+)\s*\(|def\s+(\w+)\s*\(', content)
            for match in matches:
                func_name = match[0] or match[1]
                if func_name:
                    defined_functions.add(func_name)
    except FileNotFoundError:
        logger.error(f" FATAL: Diagnostic check failed. Could not find '{manager_path}'")
        return False

    # 2. الحصول على كل الدوال التي تم استدعاؤها في المشروع
    called_functions = set()
    pattern = re.compile(r'db\.(\w+)')
    project_directory = 'bot'
    for root, _, files in os.walk(project_directory):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        for line in f:
                            matches = pattern.findall(line)
                            for func_name in matches:
                                called_functions.add(func_name)
                except Exception:
                    pass

    # 3. المقارنة وطباعة التقرير
    missing_functions = called_functions - defined_functions
    
    logger.info("--- Database Integrity Report ---")
    if not missing_functions:
        logger.info("✅ SUCCESS! All database functions are correctly defined in manager.py.")
        return True
    else:
        logger.error("❌ FAILED! Missing database functions found. The application will not start.")
        for func in sorted(list(missing_functions)):
            logger.error(f"  - Function '{func}' is called in the project but NOT defined in manager.py.")
        logger.info("--- End of Report ---")
        return False


# --- دالة لتشغيل البوت ---
async def start_bot():
    """يقوم بإعداد وتشغيل البوت بالترتيب الصحيح للمعالجات."""
    
    # --- 💡 تشغيل الفحص أولاً 💡 ---
    is_ok = await run_database_integrity_check()
    if not is_ok:
        logger.critical(" Shutting down due to critical errors found during integrity check.")
        return

    bot = Bot(token=TELEGRAM_TOKEN)
    storage = MongoStorage(uri=MONGO_URI, db_name="aiogram_fsm")
    dp = Dispatcher(bot, storage=storage)

    # --- ربط الفلاتر والوسائط بالبوت ---
    dp.filters_factory.bind(IsAdminFilter)
    dp.middleware.setup(BanMiddleware())
    dp.middleware.setup(AntiFloodMiddleware())

    if not await db.connect_to_database(MONGO_URI):
        logger.critical("❌ فشل الاتصال بقاعدة البيانات، إيقاف البوت.")
        return

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
            
    register_direct_unban_handler(dp)

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
        scheduler.shutdown()
