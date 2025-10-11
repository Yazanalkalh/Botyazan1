# -*- coding: utf-8 -*-

from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler
import logging

from config import TELEGRAM_TOKEN
from bot.database.manager import db

# --- شرح ---
# هذا هو الملف الرئيسي الذي يقوم بتشغيل البوت.
# وظيفته هي تجميع كل "المعالجات" (Handlers) من الملفات الأخرى وتسجيلها في التطبيق.

# إعداد سجلات الأخطاء (Logging)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# استيراد المعالجات من ملفاتها المنفصلة
from bot.handlers.user.start import start_handler
from bot.handlers.user.callbacks import (
    date_button_handler,
    time_button_handler,
    daily_reminder_button_handler
)
from bot.handlers.admin.main_panel import admin_handler, admin_panel_back_handler
from bot.handlers.admin.reminders_handler import (
    reminders_panel_handler,
    add_reminder_conv_handler,
    view_reminders_handler,
    delete_reminder_handler,
    reminders_panel_from_view_handler,
    import_reminders_conv_handler,
)
# --- استيراد جديد ---
from bot.handlers.admin.interface_handler import (
    interface_panel_handler,
    change_timezone_conv_handler,
)

def main() -> None:
    """يبدأ تشغيل البوت."""
    if db is None:
        logging.error("لا يمكن تشغيل البوت بسبب فشل الاتصال بقاعدة البيانات")
        return

    # إنشاء كائن التطبيق ووضع التوكن الخاص بالبوت
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # --- تسجيل المعالجات (Handlers) ---
    
    # 1. معالجات المستخدم العادي
    application.add_handler(start_handler)
    application.add_handler(date_button_handler)
    application.add_handler(time_button_handler)
    application.add_handler(daily_reminder_button_handler)

    # 2. معالجات لوحة تحكم المدير
    application.add_handler(admin_handler)
    application.add_handler(admin_panel_back_handler)
    
    # 3. معالجات وحدة التذكيرات
    application.add_handler(reminders_panel_handler)
    application.add_handler(add_reminder_conv_handler)
    application.add_handler(view_reminders_handler)
    application.add_handler(delete_reminder_handler)
    application.add_handler(reminders_panel_from_view_handler)
    application.add_handler(import_reminders_conv_handler)

    # 4. --- معالجات جديدة لوحدة تخصيص الواجهة ---
    application.add_handler(interface_panel_handler)
    application.add_handler(change_timezone_conv_handler)

    # تشغيل البوت حتى يتم إيقافه يدوياً (Ctrl+C)
    application.run_polling()

if __name__ == '__main__':
    main()
