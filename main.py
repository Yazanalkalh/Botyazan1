# -*- coding: utf-8 -*-

import asyncio
import signal
from telegram import Update
from telegram.ext import Application

from config import TELEGRAM_TOKEN, ADMIN_USER_ID
from bot.database.manager import db_connection

# --- استيراد جميع المعالجات كما هي ---
from bot.handlers.user.start import (
    start_handler, recheck_subscription_callback_handler, contact_admin_handler
)
from bot.handlers.user.callbacks import (
    show_date_handler, show_time_handler, show_reminder_handler
)
from bot.handlers.user.message_handler import message_forwarder_handler
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

# --- نظام الإيقاف الآمن والاحترافي ---
async def shutdown(application: Application, loop: asyncio.AbstractEventLoop):
    """إيقاف البوت بأمان."""
    print("بدء عملية إيقاف البوت بأمان...")
    await application.shutdown()
    # نوقف المهام المتبقية ونلغيها
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()
    print("تم إيقاف البوت بنجاح.")

def main():
    """نقطة انطلاق البوت الرئيسية مع معالجة الإيقاف الآمن."""
    if db_connection is None:
        print("فشل الاتصال بقاعدة البيانات. لا يمكن تشغيل البوت.")
        return
        
    if not TELEGRAM_TOKEN or not ADMIN_USER_ID:
        print("يرجى التأكد من إعداد التوكن ومعرف المدير.")
        return

    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # --- إضافة جميع المعالجات ---
    all_handlers = [
        add_reminder_conv_handler, import_reminders_conv_handler,
        change_timezone_conv_handler, add_channel_conversation_handler,
        edit_texts_conversation_handler, channel_approval_tracker,
        channel_decision_handler, admin_reply_handler, start_handler,
        recheck_subscription_callback_handler, contact_admin_handler,
        show_date_handler, show_time_handler, show_reminder_handler,
        admin_handler, admin_panel_back_handler, reminders_panel_handler,
        view_all_reminders_handler, delete_reminder_handler,
        interface_menu_handler, subscription_menu_handler,
        view_channels_main_handler, delete_channel_main_handler,
        edit_texts_menu_handler, message_forwarder_handler,
    ]
    application.add_handlers(all_handlers)

    # --- إعداد حلقة الحدث ونظام الإيقاف ---
    loop = asyncio.get_event_loop()
    
    # إعداد مستمع لإشارة الإيقاف من Render (SIGTERM)
    loop.add_signal_handler(
        signal.SIGTERM,
        lambda: asyncio.create_task(shutdown(application, loop))
    )
    # إعداد مستمع لإشارة الإيقاف من الكيبورد (Ctrl+C)
    loop.add_signal_handler(
        signal.SIGINT,
        lambda: asyncio.create_task(shutdown(application, loop))
    )

    # --- تشغيل البوت ---
    try:
        print("البوت قيد التشغيل... اضغط Ctrl+C للإيقاف.")
        loop.run_until_complete(application.initialize())
        loop.run_until_complete(application.start())
        # هذا سيبقي البوت يعمل إلى الأبد حتى تأتي إشارة الإيقاف
        loop.run_forever()
    except KeyboardInterrupt:
        # هذا الجزء للتعامل مع Ctrl+C إذا لم يعمل المستمع
        pass
    finally:
        # التأكد من أن الحلقة أغلقت بشكل صحيح
        if loop.is_running():
            loop.run_until_complete(shutdown(application, loop))
        loop.close()

if __name__ == "__main__":
    main()
