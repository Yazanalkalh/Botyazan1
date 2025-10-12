# -*- coding: utf-8 -*-

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from config import ADMIN_USER_ID

# --- شرح ---
# هذا هو "البهو الرئيسي" للمدير. يعرض لوحة التحكم الرئيسية المنظمة
# ويوفر وظيفة "الرجوع" للعودة إلى هذه اللوحة.

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يعرض لوحة التحكم الرئيسية للمدير فقط."""
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        return

    keyboard = [
        [InlineKeyboardButton("✍️ الردود التلقائية", callback_data="auto_replies_panel"), InlineKeyboardButton("🗓️ التذكيرات", callback_data="reminders_panel")],
        [InlineKeyboardButton("📢 نشر للجميع", callback_data="broadcast_panel"), InlineKeyboardButton("📊 الإحصائيات", callback_data="stats_panel")],
        [InlineKeyboardButton("📝 تعديل النصوص", callback_data="edit_texts_panel"), InlineKeyboardButton("🎨 تخصيص الواجهة", callback_data="interface_panel")],
        [InlineKeyboardButton("🔗 الاشتراك الإجباري", callback_data="subscription_panel"), InlineKeyboardButton("🛡️ الحماية والأمان", callback_data="security_panel")],
        [InlineKeyboardButton("🚫 إدارة الحظر", callback_data="ban_panel"), InlineKeyboardButton("📣 إدارة القنوات", callback_data="channels_panel")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = "أهلاً بك في لوحة تحكم المدير."
    # إذا كان قادماً من زر رجوع، يتم تعديل الرسالة، وإلا يتم إرسال رسالة جديدة
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)

# هذه الوظيفة مهمة جداً لأنها تسمح بالعودة للوحة الرئيسية من أي قائمة فرعية
async def back_to_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يعالج زر الرجوع إلى لوحة التحكم الرئيسية."""
    # إعادة استخدام نفس وظيفة اللوحة الرئيسية
    await admin_panel(update, context)

admin_handler = CommandHandler("admin", admin_panel)
admin_panel_back_handler = CallbackQueryHandler(back_to_admin_panel, pattern="^admin_panel_back$")
