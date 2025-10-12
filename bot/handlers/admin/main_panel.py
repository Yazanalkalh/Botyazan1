# -*- coding: utf-8 -*-

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from config import ADMIN_USER_ID

async def get_admin_panel_markup() -> InlineKeyboardMarkup:
    """ينشئ لوحة مفاتيح لوحة التحكم الرئيسية للمدير."""
    keyboard = [
        [
            InlineKeyboardButton("🗓️ التذكيرات", callback_data="reminders_panel"),
            InlineKeyboardButton("🎨 تخصيص الواجهة", callback_data="customize_interface")
        ],
        [
            InlineKeyboardButton("🔐 الاشتراك الإجباري", callback_data="subscription_menu"),
            InlineKeyboardButton("📝 تعديل النصوص", callback_data="edit_texts_menu")
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

async def admin_panel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """يعرض لوحة التحكم الرئيسية."""
    user = update.effective_user
    if str(user.id) != ADMIN_USER_ID:
        return

    reply_markup = await get_admin_panel_markup()
    
    # إذا كان مصدر الطلب هو أمر /admin
    if update.message:
        await update.message.reply_text("أهلاً بك في لوحة التحكم الرئيسية.", reply_markup=reply_markup)
    # إذا كان مصدر الطلب هو زر رجوع
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("أهلاً بك في لوحة التحكم الرئيسية.", reply_markup=reply_markup)

# --- المعالجات ---
admin_command_handler = CommandHandler("admin", admin_panel_handler)
admin_panel_callback_handler = CallbackQueryHandler(admin_panel_handler, pattern="^admin_panel_back$")
