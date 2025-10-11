# -*- coding: utf-8 -*-

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

from bot.database.manager import get_setting, set_setting

EDITING_WELCOME_MESSAGE, EDITING_DATE_BTN, EDITING_TIME_BTN, EDITING_REMINDER_BTN = range(4)

async def edit_texts_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📝 تعديل رسالة الترحيب", callback_data="edit_welcome_msg")],
        [InlineKeyboardButton("📅 تعديل نص زر التاريخ", callback_data="edit_date_btn")],
        [InlineKeyboardButton("⏰ تعديل نص زر الساعة", callback_data="edit_time_btn")],
        [InlineKeyboardButton("📿 تعديل نص زر الأذكار", callback_data="edit_reminder_btn")],
        [InlineKeyboardButton("🔙 رجوع للوحة التحكم", callback_data="admin_panel_back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.edit_text(
        text="🖋️ قسم تعديل نصوص البوت.\n\nاختر النص الذي تريد تعديله.",
        reply_markup=reply_markup
    )

async def request_new_text(update: Update, context: ContextTypes.DEFAULT_TYPE, text_key: str, description: str, state: int):
    current_text = get_setting(text_key, f"({description} الافتراضي)")
    await update.callback_query.message.edit_text(
        text=f"النص الحالي لـ'{description}':\n\n`{current_text}`\n\nأرسل الآن النص الجديد.\n\nملاحظة: يمكنك استخدام `{{user_mention}}` ليتم استبداله بمنشن المستخدم في رسالة الترحيب.",
        parse_mode='Markdown'
    )
    return state

async def request_welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await request_new_text(update, context, "text_welcome", "رسالة الترحيب", EDITING_WELCOME_MESSAGE)

async def request_date_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await request_new_text(update, context, "btn_date", "زر التاريخ", EDITING_DATE_BTN)

async def request_time_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await request_new_text(update, context, "btn_time", "زر الساعة", EDITING_TIME_BTN)

async def request_reminder_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await request_new_text(update, context, "btn_reminder", "زر الأذكار", EDITING_REMINDER_BTN)

async def save_new_text(update: Update, context: ContextTypes.DEFAULT_TYPE, text_key: str, description: str):
    new_text = update.message.text
    set_setting(text_key, new_text)
    await update.message.reply_text(f"✅ تم تحديث نص '{description}' بنجاح.")
    await update.message.reply_text("اضغط /admin للعودة إلى لوحة التحكم.")
    return ConversationHandler.END

async def save_welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await save_new_text(update, context, "text_welcome", "رسالة الترحيب")

async def save_date_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await save_new_text(update, context, "btn_date", "زر التاريخ")

async def save_time_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await save_new_text(update, context, "btn_time", "زر الساعة")

async def save_reminder_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await save_new_text(update, context, "btn_reminder", "زر الأذكار")

edit_texts_menu_handler = CallbackQueryHandler(edit_texts_menu, pattern="^edit_texts_menu$")

edit_texts_conversation_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(request_welcome_message, pattern="^edit_welcome_msg$"),
        CallbackQueryHandler(request_date_button, pattern="^edit_date_btn$"),
        CallbackQueryHandler(request_time_button, pattern="^edit_time_btn$"),
        CallbackQueryHandler(request_reminder_button, pattern="^edit_reminder_btn$"),
    ],
    states={
        EDITING_WELCOME_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_welcome_message)],
        EDITING_DATE_BTN: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_date_button)],
        EDITING_TIME_BTN: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_time_button)],
        EDITING_REMINDER_BTN: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_reminder_button)],
    },
    fallbacks=[]
  )
