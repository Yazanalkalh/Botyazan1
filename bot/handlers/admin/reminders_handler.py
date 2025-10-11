# -*- coding: utf-8 -*-

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    CommandHandler,
)
import io

from bot.database.manager import (
    add_reminder,
    get_all_reminders,
    delete_reminder,
)

(
    AWAIT_REMINDER_TEXT,
    AWAIT_REMINDER_FILE,
) = range(2)

# ---- 1. الواجهة الرئيسية لوحدة التذكيرات ----

async def reminders_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """يعرض الأزرار الفرعية الخاصة بإدارة التذكيرات."""
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("➕ إضافة تذكير جديد", callback_data='add_new_reminder')],
        [InlineKeyboardButton("📋 عرض جميع التذكيرات", callback_data='view_all_reminders')],
        [InlineKeyboardButton("📂 استيراد تذكيرات من ملف", callback_data='import_reminders_file')],
        [InlineKeyboardButton("🔙 رجوع للوحة التحكم الرئيسية", callback_data='back_to_main_panel')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text="اختر الإجراء المطلوب لإدارة التذكيرات:", reply_markup=reply_markup
    )

# ---- 2. إضافة تذكير جديد (بداية المحادثة) ----

async def ask_for_reminder_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """يطلب من المدير إرسال نص التذكير الجديد."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="أرسل الآن نص الذكر أو الدعاء الذي تريد إضافته.\nلإلغاء الأمر، أرسل /cancel")
    
    return AWAIT_REMINDER_TEXT

async def save_reminder_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """يحفظ النص الذي أرسله المدير في قاعدة البيانات."""
    new_reminder_text = update.message.text
    
    if add_reminder(new_reminder_text):
        await update.message.reply_text("✅ تم حفظ التذكير بنجاح!")
    else:
        await update.message.reply_text("❌ حدث خطأ أثناء الحفظ.")
        
    await show_reminders_panel_after_action(update, context)
    return ConversationHandler.END

# ---- 3. عرض وحذف التذكيرات (هنا تم التعديل) ----

async def view_all_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """يعرض كل التذكيرات المحفوظة مع زر حذف بجانب كل واحد."""
    query = update.callback_query
    await query.answer()

    all_reminders = get_all_reminders()
    
    # --- تعديل 1: إضافة زر "إضافة أول تذكير" إذا كانت القائمة فارغة ---
    if not all_reminders:
        keyboard = [
            [InlineKeyboardButton("➕ إضافة أول تذكير", callback_data='add_new_reminder')],
            [InlineKeyboardButton("🔙 رجوع", callback_data='reminders_panel_from_view')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="لا توجد أي تذكيرات محفوظة حالياً.", reply_markup=reply_markup)
        return

    keyboard = []
    for reminder in all_reminders:
        reminder_text_preview = reminder['text'][:50] + '...' if len(reminder['text']) > 50 else reminder['text']
        reminder_id = str(reminder['_id'])
        
        delete_button = InlineKeyboardButton("🗑️ حذف", callback_data=f'delete_reminder_{reminder_id}')
        text_button = InlineKeyboardButton(reminder_text_preview, callback_data=f'dummy_{reminder_id}')
        
        keyboard.append([text_button, delete_button])

    # --- تعديل 2: إضافة زر "إضافة المزيد" بجانب زر الرجوع ---
    bottom_row = [
        InlineKeyboardButton("🔙 رجوع", callback_data='reminders_panel_from_view'),
        InlineKeyboardButton("➕ إضافة المزيد", callback_data='add_new_reminder')
    ]
    keyboard.append(bottom_row)
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text="قائمة التذكيرات المحفوظة:", reply_markup=reply_markup)


async def confirm_delete_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """يحذف التذكير بعد الضغط على زر الحذف."""
    query = update.callback_query
    reminder_id = query.data.split('_')[2]
    
    if delete_reminder(reminder_id):
        await query.answer("🗑️ تم الحذف بنجاح!", show_alert=True)
        # بعد الحذف، أعد عرض القائمة المحدثة
        # هذا سيضمن ظهور الأزرار الجديدة حتى بعد الحذف
        await view_all_reminders(update, context)
    else:
        await query.answer("❌ فشلت عملية الحذف.", show_alert=True)

# ---- 4. استيراد تذكيرات من ملف ----

async def ask_for_reminder_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """يطلب من المدير إرسال ملف txt."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="أرسل الآن ملف نصي (`.txt`) يحتوي على التذكيرات (كل تذكير في سطر منفصل).\nلإلغاء الأمر، أرسل /cancel")
    
    return AWAIT_REMINDER_FILE

async def process_reminder_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """يعالج الملف ويحفظ التذكيرات في قاعدة البيانات."""
    document = update.message.document
    if not document or not document.file_name.lower().endswith('.txt'):
        await update.message.reply_text("يرجى إرسال ملف بصيغة `.txt` فقط.")
        return AWAIT_REMINDER_FILE

    file = await document.get_file()
    file_content_bytes = await file.read_to_bytearray()
    
    try:
        file_text = file_content_bytes.decode('utf-8')
        lines = file_text.splitlines()
        count = 0
        for line in lines:
            if line.strip():
                add_reminder(line.strip())
                count += 1
        await update.message.reply_text(f"✅ تم استيراد وحفظ {count} تذكير بنجاح!")
    except Exception as e:
        await update.message.reply_text(f"حدث خطأ أثناء قراءة الملف: {e}")
    
    await show_reminders_panel_after_action(update, context)
    return ConversationHandler.END

# ---- 5. وظائف مساعدة للإلغاء والرجوع ----

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """يلغي العملية الحالية ويرجع للوحة التذكيرات."""
    await update.message.reply_text("تم إلغاء العملية.")
    await show_reminders_panel_after_action(update, context)
    return ConversationHandler.END

async def show_reminders_panel_after_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """دالة مساعدة لإظهار لوحة التذكيرات بعد انتهاء محادثة."""
    keyboard = [
        [InlineKeyboardButton("➕ إضافة تذكير جديد", callback_data='add_new_reminder')],
        [InlineKeyboardButton("📋 عرض جميع التذكيرات", callback_data='view_all_reminders')],
        [InlineKeyboardButton("📂 استيراد تذكيرات من ملف", callback_data='import_reminders_file')],
        [InlineKeyboardButton("🔙 رجوع للوحة التحكم الرئيسية", callback_data='back_to_main_panel')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text="اختر الإجراء المطلوب لإدارة التذكيرات:", reply_markup=reply_markup)

# ---- 6. تجميع المعالجات (Handlers) ----

add_reminder_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(ask_for_reminder_text, pattern='^add_new_reminder$')],
    states={ AWAIT_REMINDER_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_reminder_text)] },
    fallbacks=[CommandHandler('cancel', cancel_conversation)],
)

import_reminders_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(ask_for_reminder_file, pattern='^import_reminders_file$')],
    states={ AWAIT_REMINDER_FILE: [MessageHandler(filters.Document.TXT, process_reminder_file)] },
    fallbacks=[CommandHandler('cancel', cancel_conversation)],
)

reminders_panel_handler = CallbackQueryHandler(reminders_panel, pattern='^admin_panel_02$')
view_reminders_handler = CallbackQueryHandler(view_all_reminders, pattern='^view_all_reminders$')
delete_reminder_handler = CallbackQueryHandler(confirm_delete_reminder, pattern='^delete_reminder_')
reminders_panel_from_view_handler = CallbackQueryHandler(reminders_panel, pattern='^reminders_panel_from_view$')
