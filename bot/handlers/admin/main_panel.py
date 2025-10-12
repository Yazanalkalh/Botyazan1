# -*- coding: utf-8 -*-

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from config import ADMIN_USER_ID

async def admin_panel_markup() -> InlineKeyboardMarkup:
    """ينشئ لوحة مفاتيح لوحة التحكم الرئيسية للمدير."""
    # callback_data هنا يجب أن تتطابق مع الأنماط (patterns) في المعالجات المتخصصة
    keyboard = [
        [
            InlineKeyboardButton("🗓️ التذكيرات", callback_data="reminders_panel"),
            InlineKeyboardButton("🎨 تخصيص الواجهة", callback_data="customize_interface")
        ],
        [
            InlineKeyboardButton("🔐 الاشتراك الإجباري", callback_data="subscription_menu"),
            InlineKeyboardButton("📝 تعديل النصوص", callback_data="edit_texts_menu")
        ],
        # --- سيتم إضافة بقية الأزرار هنا عند بنائها ---
    ]
    return InlineKeyboardMarkup(keyboard)

async def admin_handler_func(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """يعرض لوحة التحكم الرئيسية عند إرسال الأمر /admin."""
    user = update.effective_user
    if str(user.id) != ADMIN_USER_ID:
        return  # تجاهل إذا لم يكن المدير

    reply_markup = await admin_panel_markup()
    await update.message.reply_text("أهلاً بك في لوحة التحكم الرئيسية.", reply_markup=reply_markup)

async def admin_panel_back_handler_func(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """يعالج زر 'الرجوع' للعودة إلى لوحة التحكم الرئيسية."""
    query = update.callback_query
    await query.answer()
    reply_markup = await admin_panel_markup()
    await query.edit_message_text("أهلاً بك في لوحة التحكم الرئيسية.", reply_markup=reply_markup)

# --- المعالجات التي يتم تصديرها من هذا الملف ---
admin_handler = CommandHandler("admin", admin_handler_func)
admin_panel_back_handler = CallbackQueryHandler(admin_panel_back_handler_func, pattern="^admin_panel_back$")
