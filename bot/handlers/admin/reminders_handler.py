# -*- coding: utf-8 -*-

import math
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, filters
)
from bot.database.manager import db

# --- состояний ---
ADDING_REMINDER, IMPORTING_REMINDERS = range(2)
PAGE_SIZE = 10  # عدد العناصر في كل صفحة

async def reminders_panel_handler_func(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("➕ إضافة ذكر جديد", callback_data="add_reminder")],
        [InlineKeyboardButton("📂 استيراد من ملف", callback_data="import_reminders")],
        [InlineKeyboardButton("📋 عرض جميع الأذكار", callback_data="view_reminders_1")], # ابدأ من الصفحة 1
        [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel_back")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="اختر إجراءً لإدارة الأذكار:", reply_markup=reply_markup)

async def request_reminder_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("أرسل الآن نص الذكر الجديد الذي تريد إضافته.")
    return ADDING_REMINDER

async def add_reminder_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reminder_text = update.message.text
    await db.add_reminder(reminder_text)
    await update.message.reply_text("✅ تم إضافة الذكر بنجاح!")
    
    # العودة إلى قائمة التذكيرات
    keyboard = [
        [InlineKeyboardButton("➕ إضافة ذكر جديد", callback_data="add_reminder")],
        [InlineKeyboardButton("📂 استيراد من ملف", callback_data="import_reminders")],
        [InlineKeyboardButton("📋 عرض جميع الأذكار", callback_data="view_reminders_1")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel_back")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text="اختر إجراءً لإدارة الأذكار:", reply_markup=reply_markup)
    return ConversationHandler.END

async def request_import_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("أرسل الآن ملف .txt يحتوي على الأذكار، كل ذكر في سطر منفصل.")
    return IMPORTING_REMINDERS

async def handle_import_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    document = await update.message.document.get_file()
    file_content = (await document.read()).decode('utf-8')
    reminders = file_content.splitlines()
    
    count = 0
    for reminder in reminders:
        if reminder.strip(): # تجاهل الأسطر الفارغة
            await db.add_reminder(reminder.strip())
            count += 1
            
    await update.message.reply_text(f"✅ تم استيراد وإضافة {count} ذكر بنجاح!")
    
    # العودة إلى قائمة التذكيرات
    keyboard = [
        [InlineKeyboardButton("➕ إضافة ذكر جديد", callback_data="add_reminder")],
        [InlineKeyboardButton("📂 استيراد من ملف", callback_data="import_reminders")],
        [InlineKeyboardButton("📋 عرض جميع الأذكار", callback_data="view_reminders_1")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel_back")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text="اختر إجراءً لإدارة الأذكار:", reply_markup=reply_markup)
    return ConversationHandler.END

async def view_reminders_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    page = int(query.data.split('_')[-1])

    total_reminders = await db.get_reminders_count()
    total_pages = math.ceil(total_reminders / PAGE_SIZE)
    reminders = await db.get_reminders_page(page, PAGE_SIZE)

    text = f"الأذكار (صفحة {page} من {total_pages}):\n\n"
    keyboard = []
    if not reminders:
        text += "لا توجد أذكار لعرضها."
    else:
        for reminder in reminders:
            # عرض جزء من النص ليكون الزر قصيراً
            reminder_text_short = reminder['text'][:30] + '...' if len(reminder['text']) > 30 else reminder['text']
            keyboard.append([InlineKeyboardButton(f"🗑️ {reminder_text_short}", callback_data=f"del_reminder_{reminder['_id']}_{page}")])

    # أزرار التنقل
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("◀️ السابق", callback_data=f"view_reminders_{page-1}"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("التالي ▶️", callback_data=f"view_reminders_{page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append([
        InlineKeyboardButton("➕ إضافة المزيد", callback_data="add_reminder"),
        InlineKeyboardButton("🔙 رجوع", callback_data="reminders_panel_back")
    ])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)

async def delete_reminder_handler_func(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split('_')
    reminder_id = parts[2]
    page_to_return = int(parts[3])

    await db.delete_reminder(reminder_id)

    # إعادة عرض الصفحة الحالية
    context.callback_data = f"view_reminders_{page_to_return}" # خدعة لإعادة الاستخدام
    await view_reminders_page(update, context)


def get_reminders_handlers():
    add_reminder_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(request_reminder_input, pattern="^add_reminder$")],
        states={ADDING_REMINDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_reminder_text)]},
        fallbacks=[],
        per_message=False
    )
    import_reminders_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(request_import_file, pattern="^import_reminders$")],
        states={IMPORTING_REMINDERS: [MessageHandler(filters.Document.TXT, handle_import_file)]},
        fallbacks=[],
        per_message=False
    )
    return [
        CallbackQueryHandler(reminders_panel_handler_func, pattern="^reminders_panel$"),
        CallbackQueryHandler(reminders_panel_handler_func, pattern="^reminders_panel_back$"),
        CallbackQueryHandler(view_reminders_page, pattern="^view_reminders_"),
        CallbackQueryHandler(delete_reminder_handler_func, pattern="^del_reminder_"),
        add_reminder_conv,
        import_reminders_conv,
    ]
