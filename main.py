# -*- coding: utf-8 -*-

import asyncio
from telegram import Update
from telegram.ext import Application

from config import TELEGRAM_TOKEN
from bot.database.manager import db

# --- استيراد معالجات المستخدمين ---
from bot.handlers.user.start import start_handler, recheck_subscription_callback_handler, contact_admin_handler
from bot.handlers.user.callbacks import show_date, show_time, show_reminder
from bot.handlers.user.message_handler import message_forwarder_handler

# --- استيراد معالجات المدير ---
# كل استيراد في سطر منفصل (هذا هو التصحيح)
from bot.handlers.admin.main_panel import admin_handler, admin_panel_back_handler
from bot.handlers.admin.approval_handler import channel_approval_tracker, channel_decision_handler
from bot.handlers.admin.communication_handler import admin_reply_handler
from bot.handlers.admin.reminders_handler import *
from bot.handlers.admin.interface_handler import *
from bot.handlers.admin.subscription_handler import *
from bot.handlers.admin.text_editor_handler import *

async def main():
    if db is None:
        print("لا يمكن تشغيل البوت بسبب فشل الاتصال بقاعدة البيانات")
        return

    application = Application.builder().token(TELEGRAM_TOKEN).build()

    handlers = [
        # أنظمة أساسية للمدير
        channel_approval_tracker, channel_decision_handler,
        admin_reply_handler,
        
        # معالجات واجهة المستخدم
        start_handler, recheck_subscription_callback_handler, contact_admin_handler,
        show_date, show_time, show_reminder,
        message_forwarder_handler,

        # لوحة تحكم المدير ووحداتها
        admin_handler, admin_panel_back_handler,
        reminders_panel_handler, view_all_reminders_handler, delete_reminder_handler, add_reminder_conv_handler, import_reminders_conv_handler,
        interface_menu_handler, change_timezone_conv_handler,
        subscription_menu_handler, view_channels_main_handler, delete_channel_main_handler, add_channel_conversation_handler,
        edit_texts_menu_handler, edit_texts_conversation_handler
    ]
    application.add_handlers(handlers)

    print("البوت قيد التشغيل...")
    await application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    asyncio.run(main())
