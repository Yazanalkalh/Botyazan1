# -*- coding: utf-8 -*-

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ContextTypes, ConversationHandler, CallbackQueryHandler, MessageHandler, filters
)
from bot.database.manager import db

# --- تعريف النصوص القابلة للتعديل ---
EDITABLE_TEXTS = {
    "welcome_message": "رسالة الترحيب",
    "date_button": "نص زر التاريخ",
    "time_button": "نص زر الساعة",
    "reminder_button": "نص زر الأذكار",
    "contact_button": "نص زر التواصل",
    "contact_prompt": "رسالة طلب التواصل",
}

# --- состояний ---
SELECTING_TEXT, ENTERING_NEW_TEXT = range(2)

async def texts_menu_handler_func(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    keyboard = []
    for key, description in EDITABLE_TEXTS.items():
        keyboard.append([InlineKeyboardButton(description, callback_data=f"edit_text_{key}")])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel_back")])
    
    await query.edit_message_text(
        text="اختر النص الذي تريد تعديله:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECTING_TEXT

async def request_new_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    text_key = query.data.replace("edit_text_", "")
    
    # حفظ المفتاح في بيانات المستخدم للمحادثة
    context.user_data['text_key_to_edit'] = text_key
    
    default_text = "N/A" # قيمة افتراضية في حالة عدم وجود نص
    if text_key == "welcome_message": default_text = "أهلاً بك في بوت التقويم الإسلامي!"
    # ... يمكن إضافة قيم افتراضية للبقية ...
    
    current_text = await db.get_text(text_key, default_text)

    await query.edit_message_text(
        f"النص الحالي لـ '{EDITABLE_TEXTS[text_key]}' هو:\n\n"
        f"`{current_text}`\n\n"
        "أرسل الآن النص الجديد.",
        parse_mode='MarkdownV2'
    )
    return ENTERING_NEW_TEXT

async def handle_new_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    new_text = update.message.text
    text_key = context.user_data.get('text_key_to_edit')
    
    if not text_key:
        await update.message.reply_text("حدث خطأ ما، يرجى المحاولة مرة أخرى.")
        return ConversationHandler.END

    await db.set_text(text_key, new_text)
    await update.message.reply_text(f"✅ تم تحديث نص '{EDITABLE_TEXTS[text_key]}' بنجاح!")
    
    # مسح البيانات المؤقتة والعودة
    del context.user_data['text_key_to_edit']
    
    # العودة إلى قائمة تعديل النصوص
    keyboard = []
    for key, description in EDITABLE_TEXTS.items():
        keyboard.append([InlineKeyboardButton(description, callback_data=f"edit_text_{key}")])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel_back")])
    
    await update.message.reply_text(
        text="اختر النص الذي تريد تعديله:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ConversationHandler.END

def get_text_editor_handlers():
    edit_texts_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(texts_menu_handler_func, pattern="^edit_texts_menu$")],
        states={
            SELECTING_TEXT: [CallbackQueryHandler(request_new_text_input, pattern="^edit_text_")],
            ENTERING_NEW_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_text_input)]
        },
        fallbacks=[CallbackQueryHandler(admin_panel_handler, pattern="^admin_panel_back$")],
        per_message=False
    )
    return [edit_texts_conv]
