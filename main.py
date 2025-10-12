# -*- coding: utf-8 -*-

import asyncio
import logging
import threading
import os
from telegram import Update
from telegram.ext import Application

import web_server
from config import TELEGRAM_TOKEN, MONGO_URI
from bot.database.manager import db

# --- استيراد معالجات المستخدم ---
from bot.handlers.user.start import start_handler, check_subscription_handler
from bot.handlers.user.callbacks import (
    show_date_handler, show_time_handler, show_reminder_handler, contact_admin_handler
)
from bot.handlers.user.message_handler import message_forwarder_handler

# --- استيراد معالجات المدير ---
from bot.handlers.admin.main_panel import admin_command_handler, admin_panel_callback_handler
from bot.handlers.admin.approval_handler import new_member_handler, channel_approval_handler
from bot.handlers.admin.communication_handler import admin_reply_handler
from bot.handlers.admin.reminders_handler import get_reminders_handlers
from bot.handlers.admin.interface_handler import get_interface_handlers
from bot.handlers.admin.subscription_handler import get_subscription_handlers
from bot.handlers.admin.text_editor_handler import get_text_editor_handlers
from bot.handlers.admin.publishing_handler import get_publishing_handlers # <-- إضافة جديدة

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def startup():
    """الوظيفة الرئيسية لإعداد وتشغيل البوت."""
    await db.connect_to_database(uri=MONGO_URI)
    
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # --- تجميع جميع المعالجات ---
    handlers = [
        start_handler, check_subscription_handler,
        show_date_handler, show_time_handler, show_reminder_handler, contact_admin_handler,
        admin_command_handler, admin_panel_callback_handler,
        new_member_handler, channel_approval_handler, admin_reply_handler,
        message_forwarder_handler
    ]
    handlers.extend(get_reminders_handlers())
    handlers.extend(get_interface_handlers())
    handlers.extend(get_subscription_handlers())
    handlers.extend(get_text_editor_handlers())
    handlers.extend(get_publishing_handlers()) # <-- إضافة جديدة

    application.add_handlers(handlers)
    logger.info("البوت قيد التشغيل...")
    await application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    if not (TELEGRAM_TOKEN and MONGO_URI):
        logger.critical("لم يتم العثور على متغيرات البيئة الأساسية (TELEGRAM_TOKEN, MONGO_URI).")
    else:
        flask_thread = threading.Thread(target=web_server.run_flask)
        flask_thread.daemon = True
        flask_thread.start()
        logger.info("خادم الويب Flask قيد التشغيل...")

        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(startup())
        else:
            loop.run_until_complete(startup())
