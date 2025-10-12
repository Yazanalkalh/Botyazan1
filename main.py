# -*- coding: utf-8 -*-

import asyncio
import logging
import threading
import time

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

import web_server
from config import TELEGRAM_TOKEN, MONGO_URI, ADMIN_USER_ID
from bot.database.manager import db

# --- استيراد وتسجيل المعالجات ---
from bot.handlers.user.start import register_start_handlers
from bot.handlers.user.callbacks import register_callback_handlers
from bot.handlers.user.message_handler import register_message_handlers
from bot.handlers.admin.communication_handler import register_communication_handlers

# --- إعداد البوت ---
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

storage = MemoryStorage()
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot, storage=storage)


# === إشعار المدير ===
async def notify_admin_startup():
    """إرسال إشعار للمدير عند بدء تشغيل البوت."""
    try:
        await bot.send_message(
            ADMIN_USER_ID,
            "🚀 *تم تشغيل البوت بنجاح!*\n\n"
            "البوت الآن متصل بالخادم ويعمل بدون مشاكل 👌",
            parse_mode=types.ParseMode.MARKDOWN
        )
        logger.info("تم إشعار المدير بنجاح.")
    except Exception as e:
        logger.error(f"فشل إرسال إشعار للمدير: {e}")


async def notify_admin_shutdown():
    """إشعار عند إيقاف البوت."""
    try:
        await bot.send_message(
            ADMIN_USER_ID,
            "⚠️ *تم إيقاف البوت الآن.*",
            parse_mode=types.ParseMode.MARKDOWN
        )
    except Exception:
        pass


async def notify_admin_flask_crash(error_msg: str):
    """إشعار المدير إذا توقف Flask فجأة."""
    try:
        await bot.send_message(
            ADMIN_USER_ID,
            f"🔥 *تحذير مهم!*\n\nخادم الويب Flask توقف عن العمل.\n\nالخطأ:\n`{error_msg}`",
            parse_mode=types.ParseMode.MARKDOWN
        )
        logger.warning("تم إرسال تنبيه توقف Flask إلى المدير.")
    except Exception as e:
        logger.error(f"فشل إشعار المدير بتوقف Flask: {e}")


# === تشغيل Flask مع مراقبة الأخطاء ===
def run_flask_safe():
    try:
        web_server.run_flask()
    except Exception as e:
        error_message = str(e)
        logger.error(f"Flask server failed: {error_message}")
        # تأخير بسيط حتى يتصل البوت ثم يرسل الإشعار
        time.sleep(5)
        asyncio.run(notify_admin_flask_crash(error_message))


# === وظائف Aiogram الأساسية ===
async def on_startup(dispatcher: Dispatcher):
    """عند بدء التشغيل."""
    logger.info("جارٍ الاتصال بقاعدة البيانات...")
    await db.connect_to_database(uri=MONGO_URI)
    
    register_start_handlers(dispatcher)
    register_callback_handlers(dispatcher)
    register_communication_handlers(dispatcher)
    register_message_handlers(dispatcher)
    
    await notify_admin_startup()
    logger.info("✅ البوت جاهز للعمل.")


async def on_shutdown(dispatcher: Dispatcher):
    """عند إيقاف البوت."""
    await notify_admin_shutdown()
    logger.warning('تم إيقاف البوت بنجاح.')


# === نقطة البداية ===
if __name__ == '__main__':
    # تشغيل Flask في خيط منفصل
    flask_thread = threading.Thread(target=run_flask_safe)
    flask_thread.daemon = True
    flask_thread.start()
    logger.info("خادم الويب Flask قيد التشغيل...")

    # تشغيل البوت
    executor.start_polling(
        dispatcher=dp,
        skip_updates=True,
        on_startup=on_startup,
        on_shutdown=on_shutdown
    )
