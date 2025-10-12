# -*- coding: utf-8 -*-

import math
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, filters
)
from bot.database.manager import db

# --- состояний ---
SELECTING_ACTION, ADDING_REMINDER, IMPORTING_REMINDERS = range(3)
ITEMS_PER_PAGE = 8 # عدد العناصر في كل صفحة

async def reminders_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """يعرض لوحة تحكم التذكيرات."""
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("➕ إضافة ذكر جديد", callback_data="add_reminder")],
        [InlineKeyboardButton("📥 استيراد من ملف", callback_data="import_reminders")],
        [InlineKeyboardButton("👁️ عرض جميع الأذكار", callback_data="view_all_reminders_page_1")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel_back")],
    ]
    
    await query.edit_message_text(
        text="اختر الإجراء المتعلق بالأذكار:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECTING_ACTION

# --- منطق عرض الصفحات ---
async def view_reminders_page(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """يعرض صفحة محددة من الأذكار."""
    query = update.callback_query
    await query.answer()
    
    # استخراج رقم الصفحة من callback_data (e.g., "view_all_reminders_page_1")
    page = int(query.data.split('_')[-1])

    total_reminders = await db.count_reminders()
    if total_reminders == 0:
        await query.edit_message_text(
            text="لا توجد أي أذكار محفوظة حالياً.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ إضافة ذكر", callback_data="add_reminder")],
                [InlineKeyboardButton("🔙 رجوع", callback_data="reminders_panel_back")]
            ])
        )
        return SELECTING_ACTION

    total_pages = math.ceil(total_reminders / ITEMS_PER_PAGE)
    reminders_on_page = await db.get_reminders_by_page(page=page, limit=ITEMS_PER_PAGE)

    keyboard = []
    for reminder in reminders_on_page:
        # عرض أول 30 حرفاً من الذكر على الزر
        reminder_text = reminder['text'][:30] + '...' if len(reminder['text']) > 30 else reminder['text']
        keyboard.append([
            InlineKeyboardButton(reminder_text, callback_data=f"noop"), # noop = no operation
            InlineKeyboardButton("🗑️", callback_data=f"delete_reminder_{reminder['_id']}_{page}")
        ])

    # --- بناء أزرار التنقل ---
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("◀️ السابق", callback_data=f"view_all_reminders_page_{page-1}"))
    
    nav_buttons.append(InlineKeyboardButton(f"صفحة {page}/{total_pages}", callback_data="noop"))

    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("التالي ▶️", callback_data=f"view_all_reminders_page_{page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append([
        InlineKeyboardButton("➕ إضافة المزيد", callback_data="add_reminder"),
        InlineKeyboardButton("🔙 رجوع", callback_data="reminders_panel_back")
    ])

    await query.edit_message_text(
        text=f"قائمة الأذكار (صفحة {page}):",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECTING_ACTION

# --- منطق الحذف ---
async def delete_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """يحذف ذكراً ويعيد عرض الصفحة الحالية."""
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split('_')
    reminder_id = parts[2]
    page_to_return = int(parts[3])

    await db.delete_reminder(reminder_id)

    # إعادة تحميل نفس الصفحة بعد الحذف
    # تعديل query.data بشكل مصطنع لاستدعاء وظيفة عرض الصفحة
    context.callback_query.data = f"view_all_reminders_page_{page_to_return}"
    return await view_reminders_page(update, context)

# --- بقية وظائف إضافة واستيراد التذكيرات تبقى كما هي ---
async def request_reminder_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="أرسل الآن نص الذكر الجديد:")
    return ADDING_REMINDER

async def handle_reminder_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await db.add_reminder(update.message.text)
    await update.message.reply_text("✅ تم حفظ الذكر بنجاح.")
    
    # العودة إلى قائمة التذكيرات بعد الإضافة
    # محاكاة ضغطة زر الرجوع
    from bot.handlers.admin.main_panel import reminders_panel_callback
    await reminders_panel_callback(update, context)
    return ConversationHandler.END

async def request_reminders_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="أرسل الآن ملف .txt يحتوي على الأذكار (كل ذكر في سطر).")
    return IMPORTING_REMINDERS

async def handle_reminders_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    document = update.message.document
    if not document.file_name.endswith('.txt'):
        await update.message.reply_text("الملف غير صالح. يرجى إرسال ملف بصيغة .txt")
        return IMPORTING_REMINDERS

    file = await context.bot.get_file(document.file_id)
    file_content_bytes = await file.download_as_bytearray()
    file_content = file_content_bytes.decode('utf-8')
    
    reminders = [line.strip() for line in file_content.splitlines() if line.strip()]
    
    count = 0
    for reminder_text in reminders:
        await db.add_reminder(reminder_text)
        count += 1
        
    await update.message.reply_text(f"✅ تم استيراد وحفظ {count} ذكراً بنجاح.")
    
    from bot.handlers.admin.main_panel import reminders_panel_callback
    await reminders_panel_callback(update, context)
    return ConversationHandler.END


# --- بناء المعالجات ---
reminders_panel_handler = CallbackQueryHandler(reminders_panel, pattern="^reminders_panel$")
reminders_panel_back_handler = CallbackQueryHandler(reminders_panel, pattern="^reminders_panel_back$")

# معالج جديد لصفحات التذكيرات
reminders_page_handler = CallbackQueryHandler(view_reminders_page, pattern=r"^view_all_reminders_page_\d+$")
delete_reminder_handler = CallbackQueryHandler(delete_reminder, pattern=r"^delete_reminder_.+_\d+$")

add_reminder_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(request_reminder_input, pattern="^add_reminder$")],
    states={
        ADDING_REMINDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reminder_input)],
    },
    fallbacks=[],
    per_message=False
)

import_reminders_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(request_reminders_file, pattern="^import_reminders$")],
    states={
        IMPORTING_REMINDERS: [MessageHandler(filters.Document.TXT, handle_reminders_file)],
    },
    fallbacks=[],
    per_message=False
)
