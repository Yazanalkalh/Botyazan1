# -*- coding: utf-8 -*-

# (الكود الكامل للملف موجود في ردود سابقة وهو صحيح، قم بلصقه هنا)
# للتأكيد، هذا الملف يجب أن يحتوي على:
# - edit_texts_menu_handler
# - edit_texts_conversation_handler (ConversationHandler)
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
)
from bot.database.manager import get_text, set_text

# --- States for ConversationHandler ---
EDIT_TEXT = range(1)

# --- قائمة النصوص القابلة للتعديل ---
EDITABLE_TEXTS = {
    "welcome_message": "رسالة الترحيب",
    "date_button": "نص زر التاريخ",
    "time_button": "نص زر الساعة",
    "reminder_button": "نص زر الأذكار",
    "contact_button": "نص زر التواصل",
    "sub_required_text": "رسالة طلب الاشتراك",
    "sub_recheck_button": "نص زر التحقق من الاشتراك",
    "contact_prompt": "رسالة طلب إرسال رسالة للإدارة"
}

# --- Menu Handler ---
async def edit_texts_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = []
    for key, description in EDITABLE_TEXTS.items():
        keyboard.append([InlineKeyboardButton(description, callback_data=f"edit_text_{key}")])
    
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel_back")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="اختر النص الذي تريد تعديله:", reply_markup=reply_markup)

# --- Edit Text Conversation ---
async def edit_text_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    text_id = query.data.split("_")[2]
    context.user_data['text_to_edit'] = text_id
    
    current_text = await get_text(text_id, " (لا يوجد نص محدد حالياً)")

    text_description = EDITABLE_TEXTS.get(text_id, "نص غير معروف")
    
    prompt = (
        f"📝 **تعديل: {text_description}**\n\n"
        f"**النص الحالي:**\n`{current_text}`\n\n"
        f"أرسل الآن النص الجديد. يمكنك استخدام `{user}` ليتم استبداله باسم المستخدم في رسالة الترحيب."
    )
    keyboard = [[InlineKeyboardButton("🔙 إلغاء", callback_data="cancel_edit_text")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=prompt, reply_markup=reply_markup, parse_mode='Markdown')
    return EDIT_TEXT

async def edit_text_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_text = update.message.text
    text_id = context.user_data.get('text_to_edit')
    
    if not text_id:
        # Should not happen in a conversation
        await update.message.reply_text("حدث خطأ. يرجى المحاولة مرة أخرى.")
        return ConversationHandler.END

    await set_text(text_id, new_text)
    await update.message.reply_text("✅ تم تحديث النص بنجاح.")
    
    del context.user_data['text_to_edit']
    
    from unittest.mock import Mock
    mock_query = Mock()
    mock_query.message = update.message
    mock_update = Mock()
    mock_update.callback_query = mock_query
    await edit_texts_menu(mock_update, context)

    return ConversationHandler.END

async def cancel_edit_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if 'text_to_edit' in context.user_data:
        del context.user_data['text_to_edit']
    await query.answer()
    await edit_texts_menu(update, context)
    return ConversationHandler.END

# --- Handlers Definition ---
edit_texts_menu_handler = CallbackQueryHandler(edit_texts_menu, pattern="^edit_texts_panel$")

edit_texts_conversation_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(edit_text_start, pattern="^edit_text_")],
    states={
        EDIT_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_text_receive)]
    },
    fallbacks=[CallbackQueryHandler(cancel_edit_text, pattern="^cancel_edit_text$")]
)
