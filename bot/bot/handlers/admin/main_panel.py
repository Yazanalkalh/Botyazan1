# -*- coding: utf-8 -*-

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler
from config import ADMIN_USER_ID

# --- شرح ---
# هذا الملف مسؤول فقط عن الأمر /admin
# يقوم بالتحقق من هوية المدير ثم يعرض له لوحة التحكم

button_names = [
    "الردود التلقائية", "التذكيرات", "منشورات القناة", "القنوات",
    "إعدادات القنوات", "إدارة الحظر", "نشر للجميع", "تخصيص الواجهة",
    "الحماية والأمان", "إدارة الذاكرة", "الإحصائيات", "إدارة المكتبة",
    "الاشتراك الإجباري", "مراقبة النظام", "تعديل النصوص"
]

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id

    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("⚠️ هذا الأمر مخصص للمدير فقط.")
        return

    keyboard = []
    for i, name in enumerate(button_names, 1):
        button = InlineKeyboardButton(f"({i}) {name}", callback_data=f'admin_panel_{str(i).zfill(2)}')
        keyboard.append([button])
        
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("أهلاً بك في لوحة تحكم المدير:", reply_markup=reply_markup)

admin_handler = CommandHandler('admin', admin_panel)
