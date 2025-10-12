# -*- coding: utf-8 -*-

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from telegram.constants import ParseMode
from datetime import datetime
import pytz

from bot.database.manager import db

# إعداد اللوجر
logger = logging.getLogger(__name__)

# --- تعريف حالات المحادثة ---
RECEIVING_CONTENT, RECEIVING_BUTTONS, SELECTING_CHANNELS, AWAITING_SCHEDULE_TIME = range(4)

# --- وظائف المحادثة ---

async def new_post_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """تبدأ محادثة إنشاء منشور جديد."""
    query = update.callback_query
    await query.answer()
    admin_id = query.from_user.id
    context.user_data['admin_id'] = admin_id
    await db.delete_temp_post(admin_id)

    await query.edit_message_text(
        text="✍️ **إنشاء منشور جديد**\n\nأرسل الآن المحتوى الذي تريد نشره.",
        parse_mode=ParseMode.MARKDOWN_V2
    )
    return RECEIVING_CONTENT

async def receive_content(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """تستقبل محتوى المنشور وتحفظه مؤقتاً."""
    admin_id = update.message.from_user.id
    await db.save_temp_post(admin_id, update.message)

    keyboard = [
        [InlineKeyboardButton("✅ نعم، أضف أزرار", callback_data="add_buttons")],
        [InlineKeyboardButton("⏩ تخطّ", callback_data="skip_buttons")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_post")],
    ]
    await update.message.reply_text(
        "✅ تم حفظ المحتوى.\n\nهل تريد إضافة أزرار تفاعلية؟",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return RECEIVING_BUTTONS

async def request_buttons_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """تطلب من المدير إرسال الأزرار."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        text="يرجى إرسال الأزرار الآن بالتنسيق التالي:\n`النص - الرابط`\n`زر آخر - رابط آخر`\n\nلفصل الأزرار في نفس السطر، استخدم `|`\n`زر1 - رابط1 | زر2 - رابط2`",
        parse_mode=ParseMode.MARKDOWN
    )
    return RECEIVING_BUTTONS

async def receive_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """تستقبل الأزرار وتحللها."""
    admin_id = update.message.from_user.id
    button_text = update.message.text
    parsed_buttons = []
    try:
        rows = button_text.strip().split('\n')
        for row_text in rows:
            row_buttons = []
            buttons_in_row = row_text.split('|')
            for button_str in buttons_in_row:
                parts = button_str.split('-', 1)
                if len(parts) == 2:
                    text, url = parts[0].strip(), parts[1].strip()
                    if not url.startswith(('http://', 'https://', 't.me/')):
                        url = 'http://' + url
                    row_buttons.append({'text': text, 'url': url})
            if row_buttons:
                parsed_buttons.append(row_buttons)
    except Exception as e:
        await update.message.reply_text(f"حدث خطأ: {e}\nيرجى المحاولة مرة أخرى.")
        return RECEIVING_BUTTONS

    if not parsed_buttons:
        await update.message.reply_text("لم أتمكن من تحليل أي أزرار. يرجى التأكد من التنسيق.")
        return RECEIVING_BUTTONS

    await db.update_temp_post_buttons(admin_id, parsed_buttons)
    await update.message.reply_text("✅ تم إضافة الأزرار بنجاح.")
    return await preview_and_select_channels(update, context)

async def post_creation_finished(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """يتم استدعاؤها عند تخطي إضافة الأزرار."""
    query = update.callback_query
    await query.answer()
    return await preview_and_select_channels(update, context)

async def preview_and_select_channels(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """تعرض معاينة للمنشور وتطلب اختيار القنوات."""
    admin_id = context.user_data.get('admin_id')
    temp_post = await db.get_temp_post(admin_id)

    if not temp_post:
        await update.effective_message.reply_text("حدث خطأ، لم أجد المنشور المؤقت.")
        return ConversationHandler.END

    message_data = temp_post.get("post_data")
    buttons = temp_post.get("buttons", [])
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(**btn) for btn in row] for row in buttons]) if buttons else None

    # إرسال المعاينة
    await context.bot.copy_message(
        chat_id=admin_id,
        from_chat_id=message_data['chat']['id'],
        message_id=message_data['message_id'],
        reply_markup=reply_markup
    )
    
    # عرض قائمة القنوات
    channels = await db.get_all_approved_channels()
    if not channels:
        await update.effective_message.reply_text("لم يتم العثور على أي قنوات معتمدة للنشر. يرجى إضافة البوت كمشرف في قناة أولاً والموافقة عليها.")
        return ConversationHandler.END

    keyboard = [[InlineKeyboardButton(ch['title'], callback_data=f"select_channel_{ch['channel_id']}")] for ch in channels]
    keyboard.append([InlineKeyboardButton("📢 النشر في جميع القنوات", callback_data="select_channel_all")])
    keyboard.append([InlineKeyboardButton("❌ إلغاء", callback_data="cancel_post")])

    await update.effective_message.reply_text(
        "تم إعداد المنشور. اختر القناة التي تريد النشر فيها:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECTING_CHANNELS

async def channel_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """تعالج اختيار قناة النشر."""
    query = update.callback_query
    await query.answer()
    
    channel_info = query.data.replace("select_channel_", "")
    context.user_data['target_channels'] = [int(channel_info)] if channel_info != "all" else "all"

    keyboard = [
        [InlineKeyboardButton("🚀 النشر الآن", callback_data="publish_now")],
        [InlineKeyboardButton("⏰ جدولة النشر", callback_data="schedule_post")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_post_creation")],
    ]
    await query.edit_message_text("اختر وقت النشر:", reply_markup=InlineKeyboardMarkup(keyboard))
    return AWAITING_SCHEDULE_TIME

async def publish_now(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """تقوم بنشر الرسالة فوراً."""
    query = update.callback_query
    await query.answer()
    admin_id = context.user_data.get('admin_id')
    target_channels = context.user_data.get('target_channels')
    
    # منطق النشر الفعلي سيتم إضافته هنا
    
    await query.edit_message_text("تم استلام أمر النشر الفوري. (سيتم تنفيذ النشر قريباً)")
    await db.delete_temp_post(admin_id)
    return ConversationHandler.END

async def request_schedule_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """تطلب من المدير إرسال وقت الجدولة."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("أرسل وقت وتاريخ النشر.\nمثال: `25-12-2025 09:30`")
    return AWAITING_SCHEDULE_TIME

async def receive_schedule_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """تستقبل وقت الجدولة وتحفظ المنشور."""
    time_str = update.message.text
    
    # منطق التحقق من الوقت وحفظ المنشور المجدول سيتم إضافته هنا
    
    await update.message.reply_text(f"تم استلام وقت الجدولة: {time_str}. (سيتم تنفيذ الجدولة قريباً)")
    admin_id = context.user_data.get('admin_id')
    await db.delete_temp_post(admin_id)
    return ConversationHandler.END

async def cancel_post_creation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """تلغي العملية."""
    query = update.callback_query
    await query.answer()
    admin_id = context.user_data.get('admin_id')
    await db.delete_temp_post(admin_id)
    await query.edit_message_text("تم إلغاء النشر.")
    return ConversationHandler.END

def get_publishing_handlers() -> list:
    """تُرجع قائمة بالمعالجات الخاصة بنظام النشر."""
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(new_post_start, pattern="^new_post$")],
        states={
            RECEIVING_CONTENT: [MessageHandler(filters.ALL & ~filters.COMMAND, receive_content)],
            RECEIVING_BUTTONS: [
                CallbackQueryHandler(request_buttons_input, pattern="^add_buttons$"),
                CallbackQueryHandler(post_creation_finished, pattern="^skip_buttons$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_buttons),
            ],
            SELECTING_CHANNELS: [CallbackQueryHandler(channel_selected, pattern="^select_channel_")],
            AWAITING_SCHEDULE_TIME: [
                CallbackQueryHandler(publish_now, pattern="^publish_now$"),
                CallbackQueryHandler(request_schedule_time, pattern="^schedule_post$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_schedule_time),
                CallbackQueryHandler(new_post_start, pattern="^back_to_post_creation$"), # Simplified back action
            ],
        },
        fallbacks=[CallbackQueryHandler(cancel_post_creation, pattern="^cancel_post$")],
        per_message=False,
    )
    return [conv_handler]
