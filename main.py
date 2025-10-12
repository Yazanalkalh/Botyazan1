# -*- coding: utf-8 -*-

import asyncio
from telegram import Update
from telegram.ext import Application

from config import TELEGRAM_TOKEN, ADMIN_USER_ID
from bot.database.manager import db_connection

# --- استيراد معالجات المستخدمين ---
from bot.handlers.user.start import (
    start_handler, recheck_subscription_callback_handler, contact_admin_handler
)
from bot.handlers.user.callbacks import (
    show_date_handler, show_time_handler, show_reminder_handler
)
from bot.handlers.user.message_handler import message_forwarder_handler

# --- استيراد معالجات المدير ---
from bot.handlers.admin.main_panel import admin_handler, admin_panel_back_handler
from bot.handlers.admin.approval_handler import (
    channel_approval_tracker, channel_decision_handler
)
from bot.handlers.admin.communication_handler import admin_reply_handler
from bot.handlers.admin.reminders_handler import (
    reminders_panel_handler, view_all_reminders_handler, delete_reminder_handler,
    add_reminder_conv_handler, import_reminders_conv_handler
)
from bot.handlers.admin.interface_handler import (
    interface_menu_handler, change_timezone_conv_handler
)
from bot.handlers.admin.subscription_handler import (
    subscription_menu_handler, view_channels_main_handler, delete_channel_main_handler,
    add_channel_conversation_handler
)
from bot.handlers.admin.text_editor_handler import (
    edit_texts_menu_handler, edit_texts_conversation_handler
)

async def main():
    """نقطة انطلاق البوت الرئيسية."""
    if db_connection is None:
        print("لا يمكن تشغيل البوت بسبب فشل الاتصال بقاعدة البيانات")
        return
        
    if not TELEGRAM_TOKEN or not ADMIN_USER_ID:
        print("يرجى التأكد من إعداد التوكن ومعرف المدير في ملف الإعدادات.")
        return

    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # --- قائمة المعالجات الكاملة ---
    # الترتيب مهم هنا
    all_handlers = [
        # 1. معالجات المدير (لها أولوية في المحادثات)
        add_reminder_conv_handler,
        import_reminders_conv_handler,
        change_timezone_conv_handler,
        add_channel_conversation_handler,
        edit_texts_conversation_handler,
        
        # 2. نظام الموافقة على القنوات
        channel_approval_tracker,
        channel_decision_handler,
        
        # 3. نظام رد المدير على المستخدمين
        admin_reply_handler,

        # 4. معالجات واجهة المستخدم (أوامر وأزرار)
        start_handler,
        recheck_subscription_callback_handler,
        contact_admin_handler,
        show_date_handler,
        show_time_handler,
        show_reminder_handler,

        # 5. معالجات لوحة تحكم المدير
        admin_handler,
        admin_panel_back_handler,
        reminders_panel_handler,
        view_all_reminders_handler,
        delete_reminder_handler,
        interface_menu_handler,
        subscription_menu_handler,
        view_channels_main_handler,
        delete_channel_main_handler,
        edit_texts_menu_handler,
        
        # 6. معالج الرسائل العامة (يجب أن يكون الأخير)
        # لأنه يلتقط أي رسالة لا تتطابق مع ما سبق
        message_forwarder_handler,
    ]
    
    application.add_handlers(all_handlers)

    print("البوت قيد التشغيل...")
    await application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"حدث خطأ فادح أدى إلى توقف البوت: {e}")
