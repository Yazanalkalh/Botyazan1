# -*- coding: utf-8 -*-

import asyncio
import logging
import os
from telegram import Update
from telegram.ext import Application
from config import TELEGRAM_TOKEN
from bot.database.manager import db

# استيراد معالجات المستخدم
from bot.handlers.user.start import start_handler
from bot.handlers.user.callbacks import show_date_handler, show_time_handler, show_reminder_handler
from bot.handlers.user.message_handler import message_forwarder_handler

# استيراد معالجات المدير
from bot.handlers.admin.main_panel import admin_handler, admin_panel_back_handler, reminders_panel_callback, subscription_menu_callback, texts_menu_callback
from bot.handlers.admin.approval_handler import new_member_handler, channel_approval_handler
from bot.handlers.admin.communication_handler import admin_reply_handler
from bot.handlers.admin.reminders_handler import *
from bot.handlers.admin.interface_handler import *
from bot.handlers.admin.subscription_handler import *
from bot.handlers.admin.text_editor_handler import *

# إعداد تسجيل الدخول الأساسي
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main() -> None:
    """Функция запуска и настройки бота."""
    
    # إعداد التطبيق
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # --- إضافة المعالجات ---
    handlers = [
        # معالجات المستخدم
        start_handler,
        show_date_handler,
        show_time_handler,
        show_reminder_handler,
        message_forwarder_handler,
        
        # معالجات المدير
        admin_handler,
        admin_panel_back_handler,
        new_member_handler,
        channel_approval_handler,
        admin_reply_handler,
        
        # وحدة التذكيرات
        reminders_panel_handler,
        reminders_panel_back_handler,
        reminders_page_handler,
        delete_reminder_handler,
        add_reminder_conv_handler,
        import_reminders_conv_handler,

        # وحدة الواجهة
        interface_menu_handler,
        change_timezone_conv_handler,
        
        # وحدة الاشتراك الإجباري (مع نظام الصفحات الجديد)
        subscription_menu_handler,
        subscription_menu_back_handler,
        add_channel_conversation_handler,
        subscription_page_handler, # المعالج الجديد
        delete_subscription_channel_handler, # المعالج الجديد

        # وحدة تعديل النصوص
        texts_menu_handler,
        edit_texts_conversation_handler
    ]
    application.add_handlers(handlers)

    # تشغيل البوت
    logger.info("البوت قيد التشغيل...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    # الاتصال بقاعدة البيانات قبل تشغيل البوت
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        logger.error("لم يتم العثور على متغير البيئة MONGO_URI.")
    else:
        # استخدام asyncio.run لتشغيل الدالة غير المتزامنة
        loop = asyncio.get_event_loop()
        loop.run_until_complete(db.connect_to_database(uri=mongo_uri))
        main()
