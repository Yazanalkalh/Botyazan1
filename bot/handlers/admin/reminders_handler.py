# -*- coding: utf-8 -*-

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
)
from bot.database.manager import add_reminder, get_all_reminders, delete_reminder
import io

# --- States for ConversationHandler ---
ADD_REMINDER, IMPORT_REMINDERS = range(2)

# --- Menu Handler ---
async def reminders_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("➕ إضافة ذكر جديد", callback_data="add_reminder_start")],
        [InlineKeyboardButton("📂 استيراد من ملف", callback_data="import_reminders_start")],
        [InlineKeyboardButton("👀 عرض جميع الأذكار", callback_data="view_all_reminders")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel_back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="اختر إجراءً لإدارة الأذكار:", reply_markup=reply_markup)

# --- View and Delete Handlers ---
async def view_all_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    reminders = await get_all_reminders()
    if not reminders:
        keyboard = [
            [InlineKeyboardButton("➕ إضافة المزيد", callback_data="add_reminder_start")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="reminders_panel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("لا توجد أذكار محفوظة حالياً.", reply_markup=reply_markup)
        return

    text = "قائمة الأذكار المحفوظة:\n\n"
    keyboard = []
    for reminder in reminders:
        reminder_text_preview = reminder['text'][:40] + "..." if len(reminder['text']) > 40 else reminder['text']
        keyboard.append([
            InlineKeyboardButton(reminder_text_preview, callback_data=f"rem_noop_{reminder['_id']}"),
            InlineKeyboardButton("🗑️ حذف", callback_data=f"delete_reminder_{reminder['_id']}")]
        )
    
    keyboard.append([InlineKeyboardButton("➕ إضافة المزيد", callback_data="add_reminder_start")])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="reminders_panel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)

async def delete_reminder_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("جاري الحذف...")
    
    reminder_id = query.data.split("_")[2]
    await delete_reminder(reminder_id)
    
    # لا نعدل الرسالة هنا، بل نعيد استدعاء وظيفة العرض لتحديث القائمة
    await view_all_reminders(update, context)

# --- Add Reminder Conversation ---
async def add_reminder_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton("🔙 إلغاء", callback_data="cancel_add_reminder")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("أرسل الآن نص الذكر الجديد.", reply_markup=reply_markup)
    return ADD_REMINDER

async def add_reminder_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reminder_text = update.message.text
    await add_reminder(reminder_text)
    
    # --- الإصلاح ---
    # بدلاً من محاكاة زر، نرسل القائمة الرئيسية مباشرة
    keyboard = [
        [InlineKeyboardButton("➕ إضافة ذكر جديد", callback_data="add_reminder_start")],
        [InlineKeyboardButton("📂 استيراد من ملف", callback_data="import_reminders_start")],
        [InlineKeyboardButton("👀 عرض جميع الأذكار", callback_data="view_all_reminders")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel_back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("✅ تم إضافة الذكر بنجاح.\n\nاختر إجراءً لإدارة الأذكار:", reply_markup=reply_markup)

    return ConversationHandler.END

async def cancel_add_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await reminders_panel(update, context)
    return ConversationHandler.END

# --- Import Reminders Conversation ---
async def import_reminders_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton("🔙 إلغاء", callback_data="cancel_import_reminders")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("أرسل الآن ملف .txt يحتوي على الأذكار (كل ذكر في سطر).", reply_markup=reply_markup)
    return IMPORT_REMINDERS

async def import_reminders_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    if not document or not document.file_name.endswith('.txt'):
        await update.message.reply_text("الملف غير صالح. يرجى إرسال ملف بصيغة .txt")
        return IMPORT_REMINDERS

    file = await context.bot.get_file(document.file_id)
    file_content = await file.download_as_bytearray()
    
    text_stream = io.StringIO(file_content.decode('utf-8'))
    
    count = 0
    for line in text_stream:
        reminder_text = line.strip()
        if reminder_text:
            await add_reminder(reminder_text)
            count += 1
            
    # --- الإصلاح ---
    keyboard = [
        [InlineKeyboardButton("➕ إضافة ذكر جديد", callback_data="add_reminder_start")],
        [InlineKeyboardButton("📂 استيراد من ملف", callback_data="import_reminders_start")],
        [InlineKeyboardButton("👀 عرض جميع الأذكار", callback_data="view_all_reminders")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel_back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"✅ تم استيراد {count} ذكر بنجاح.\n\nاختر إجراءً لإدارة الأذكار:", reply_markup=reply_markup)
    
    return ConversationHandler.END

async def cancel_import_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await reminders_panel(update, context)
    return ConversationHandler.END

# --- Handlers Definition ---
reminders_panel_handler = CallbackQueryHandler(reminders_panel, pattern="^reminders_panel$")
view_all_reminders_handler = CallbackQueryHandler(view_all_reminders, pattern="^view_all_reminders$")
delete_reminder_handler = CallbackQueryHandler(delete_reminder_callback, pattern="^delete_reminder_")

add_reminder_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(add_reminder_start, pattern="^add_reminder_start$")],
    states={
        ADD_REMINDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_reminder_receive)]
    },
    fallbacks=[CallbackQueryHandler(cancel_add_reminder, pattern="^cancel_add_reminder$")],
    per_message=False
)

import_reminders_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(import_reminders_start, pattern="^import_reminders_start$")],
    states={
        IMPORT_REMINDERS: [MessageHandler(filters.Document.TXT, import_reminders_receive)]
    },
    fallbacks=[CallbackQueryHandler(cancel_import_reminders, pattern="^cancel_import_reminders$")],
    per_message=False
)
