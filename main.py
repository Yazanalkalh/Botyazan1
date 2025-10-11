# -*- coding: utf-8 -*-

import logging
from telegram.ext import Application

# --- شرح ---
# هذا هو الملف الذي تقوم بتشغيله. وظيفته تجميع كل الأجزاء معاً.
# هو مثل المايسترو الذي يقود الأوركسترا

from config import TELEGRAM_TOKEN
from bot.database.manager import db

from bot.handlers.user.start import start_handler
from bot.handlers.user.callbacks import user_callback_handler
from bot.handlers.admin.main_panel import admin_handler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main() -> None:
    if db is None:
        logger.error("لا يمكن تشغيل البوت بسبب فشل الاتصال بقاعدة البيانات.")
        return
        
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # هنا نقوم بتسجيل كل المعالجات (الأوامر والأزرار)
    application.add_handler(start_handler)
    application.add_handler(user_callback_handler)
    application.add_handler(admin_handler)

    logger.info("البوت قيد التشغيل...")
    application.run_polling()

if __name__ == '__main__':
    main()
