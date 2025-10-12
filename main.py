# -*- coding: utf-8 -*-

import asyncio
import logging
import os
import threading
from telegram import Update
from telegram.ext import Application
import web_server

# --- استيراد الأدوات ---
from config import TELEGRAM_TOKEN
from bot.database.manager import db

# --- استيراد معالجات البوت (من أماكنها الصحيحة) ---
# 1. معالجات المستخدم
from bot.handlers.user.start import start_handler, check_subscription_handler
from bot.handlers.user.callbacks import show_date_handler, show_time_handler, show_reminder_handler, contact_admin_handler
from bot.handlers.user.message_handler import message_forwarder_handler

# 2. معالجات المدير (كل معالج من ملفه الخاص)
from bot.handlers.admin.main_panel import admin_handler, admin_panel_back_handler
from bot.handlers.admin.approval_handler import new_member_handler, channel_approval_handler
from bot.handlers.admin.communication_handler import admin_reply_handler
from bot.handlers.admin.reminders_handler import *
from bot.handlers.admin.interface_handler import *
from bot.handlers.admin.subscription_handler import *
from bot.handlers.admin.text_editor_handler import *

# --- إعداد البوت ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def main() -> None:
    """الوظيفة الرئيسية لإعداد وتشغيل البوت."""
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # --- إضافة جميع المعالجات بالترتيب الصحيح ---
    handlers = [
        # معالجات المستخدم
        start_handler, check_subscription_handler, show_date_handler,
        show_time_handler, show_reminder_handler, contact_admin_handler,
        
        # معالجات المدير (نقاط الدخول والأوامر)
        admin_handler, new_member_handler, channel_approval_handler,
        admin_reply_handler, 
        
        # معالجات أزرار لوحة التحكم
        reminders_panel_handler, interface_menu_handler,
        subscription_menu_handler, texts_menu_handler,

        # معالجات الرجوع والصفحات
        admin_panel_back_handler, reminders_panel_back_handler,
        subscription_menu_back_handler, reminders_page_handler,
        subscription_page_handler,

        # معالجات الحذف
        delete_reminder_handler, delete_subscription_channel_handler,
        
        # معالجات المحادثات
        add_reminder_conv_handler, import_reminders_conv_handler,
        change_timezone_conv_handler, add_channel_conversation_handler,
        edit_texts_conversation_handler,

        # معالج الرسائل العام يجب أن يكون في النهاية
        message_forwarder_handler
    ]
    application.add_handlers(handlers)

    logger.info("البوت قيد التشغيل...")
    await application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        logger.error("لم يتم العثور على متغير البيئة MONGO_URI.")
    else:
        flask_thread = threading.Thread(target=web_server.run_flask)
        flask_thread.daemon = True
        flask_thread.start()
        logger.info("خادم الويب قيد التشغيل...")

        loop = asyncio.get_event_loop()
        if not loop.is_running():
            loop.run_until_complete(db.connect_to_database(uri=mongo_uri))
            loop.run_until_complete(main())
