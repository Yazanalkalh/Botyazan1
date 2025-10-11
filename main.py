# -*- coding: utf-8 -*-

import logging
from telegram.ext import Application

from config import TELEGRAM_TOKEN
from bot.database.manager import db

# معالجات المستخدم
from bot.handlers.user.start import start_handler
from bot.handlers.user.callbacks import user_callback_handler

# معالجات المدير الرئيسية
from bot.handlers.admin.main_panel import admin_handler, admin_panel_back_handler

# --- جديد ---
# استيراد المعالجات الجديدة الخاصة بوحدة التذكيرات
from bot.handlers.admin.02_reminders import (
    reminders_panel_handler,
    add_reminder_conv_handler,
    view_reminders_handler,
    delete_reminder_handler,
    import_reminders_conv_handler,
    reminders_panel_from_view_handler
)

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
    
    # --- تحديث ---
    # تمت إضافة المعالجات الجديدة بالترتيب الصحيح (المحادثات أولاً)
    
    # 1. معالجات المحادثات
    application.add_handler(add_reminder_conv_handler)
    application.add_handler(import_reminders_conv_handler)
    
    # 2. معالجات الأوامر
    application.add_handler(start_handler)
    application.add_handler(admin_handler) # This now uses the decorated admin_panel

    # 3. معالجات ضغطات الأزرار (CallbackQueryHandlers)
    application.add_handler(user_callback_handler)
    application.add_handler(admin_panel_back_handler) # Handles back to main panel
    application.add_handler(reminders_panel_handler)
    application.add_handler(view_reminders_handler)
    application.add_handler(delete_reminder_handler)
    application.add_handler(reminders_panel_from_view_handler)

    logger.info("البوت قيد التشغيل...")
    application.run_polling()

if __name__ == '__main__':
    main()
