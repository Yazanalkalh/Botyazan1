# -*- coding: utf-8 -*-

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from bot.database.manager import db

# --- تعريف حالات المحادثة ---
# Awaiting the main content of the post (text, photo, video, etc.)
RECEIVING_CONTENT = 1
# Awaiting the inline buttons for the post
RECEIVING_BUTTONS = 2

# --- وظائف المحادثة ---

async def new_post_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """تبدأ محادثة إنشاء منشور جديد."""
    query = update.callback_query
    await query.answer()
    
    # حذف أي منشورات مؤقتة قديمة للمدير
    await db.delete_temp_post(context.user_data.get('admin_id'))

    await query.edit_message_text(
        text="✍️ **إنشاء منشور جديد**\n\n"
             "أرسل الآن المحتوى الذي تريد نشره.\n"
             "يمكن أن يكون (نص، صورة مع تعليق، فيديو، ملف...)."
    )
    return RECEIVING_CONTENT


async def receive_content(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """تستقبل محتوى المنشور وتحفظه مؤقتاً في قاعدة البيانات."""
    admin_id = update.message.from_user.id
    
    # حفظ الرسالة بالكامل كما هي
    # هذا يسمح لنا بإعادة إرسالها لاحقاً بنفس التنسيق (صورة مع نص، إلخ)
    await db.save_temp_post(admin_id, update.message)

    keyboard = [
        [InlineKeyboardButton("✅ نعم، أضف أزرار", callback_data="add_buttons")],
        [InlineKeyboardButton("⏩ تخطّ، لا أريد أزرار", callback_data="skip_buttons")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_post")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "✅ تم حفظ المحتوى بنجاح.\n\n"
        "هل تريد إضافة أزرار تفاعلية (Inline Buttons) لهذا المنشور؟",
        reply_markup=reply_markup
    )
    return RECEIVING_BUTTONS


async def request_buttons_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """تطلب من المدير إرسال الأزرار بالتنسيق الصحيح."""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        text="يرجى إرسال الأزرار الآن.\n\n"
             "**التنسيق المطلوب:**\n"
             "كل سطر يحتوي على زر واحد أو أكثر.\n"
             "`النص الظاهر على الزر - رابط URL`\n\n"
             "**مثال لسطر واحد بزرين:**\n"
             "`زر 1 - google.com | زر 2 - youtube.com`\n\n"
             "**مثال لسطرين، كل سطر بزر واحد:**\n"
             "`القناة الأولى - t.me/channel1`\n"
             "`الموقع الرسمي - example.com`\n\n"
             "لإلغاء إضافة الأزرار، أرسل /cancel.",
        parse_mode='Markdown'
    )
    return RECEIVING_BUTTONS


async def receive_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    تستقبل نص الأزرار، تحلله، وتحفظه في قاعدة البيانات.
    بعد هذه الخطوة، ننتقل إلى المرحلة التالية (اختيار القنوات والجدولة).
    """
    admin_id = update.message.from_user.id
    button_text = update.message.text

    # --- تحليل الأزرار ---
    parsed_buttons = []
    try:
        rows = button_text.strip().split('\n')
        for row_text in rows:
            row_buttons = []
            buttons_in_row = row_text.split('|')
            for button_str in buttons_in_row:
                parts = button_str.split('-', 1)
                if len(parts) == 2:
                    text = parts[0].strip()
                    url = parts[1].strip()
                    # إضافة http تلقائياً إذا لم يكن موجوداً
                    if not url.startswith(('http://', 'https://', 't.me/')):
                        url = 'http://' + url
                    row_buttons.append({'text': text, 'url': url})
            if row_buttons:
                parsed_buttons.append(row_buttons)
    except Exception as e:
        await update.message.reply_text(
            f"حدث خطأ أثناء تحليل الأزرار: {e}\n"
            "يرجى التأكد من اتباع التنسيق الصحيح والمحاولة مرة أخرى، أو أرسل /cancel للإلغاء."
        )
        return RECEIVING_BUTTONS

    if not parsed_buttons:
        await update.message.reply_text(
            "لم أتمكن من تحليل أي أزرار. يرجى التأكد من التنسيق:\n"
            "`النص - الرابط`\n\n"
            "أو أرسل /cancel للإلغاء."
        )
        return RECEIVING_BUTTONS

    # حفظ الأزرار المحللة في قاعدة البيانات
    await db.update_temp_post_buttons(admin_id, parsed_buttons)
    
    await update.message.reply_text(
        "✅ تم إضافة الأزرار بنجاح!\n\n"
        "المنشور الآن جاهز بالكامل. المرحلة التالية هي اختيار القنوات وتحديد وقت النشر."
    )
    
    # --- هنا سنقوم لاحقاً باستدعاء وظيفة المرحلة التالية ---
    # preview_and_select_channels(update, context)
    
    return ConversationHandler.END


async def post_creation_finished(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    يتم استدعاؤها عند تخطي إضافة الأزرار.
    المنشور الآن جاهز بدون أزرار.
    """
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        text="✅ تم إعداد المنشور بنجاح (بدون أزرار).\n\n"
             "المرحلة التالية هي اختيار القنوات وتحديد وقت النشر."
    )
    
    # --- هنا سنقوم لاحقاً باستدعاء وظيفة المرحلة التالية ---
    # preview_and_select_channels(update, context)
    
    return ConversationHandler.END


async def cancel_post_creation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """تلغي عملية إنشاء المنشور وتحذف البيانات المؤقتة."""
    # تحديد مصدر الإلغاء (من زر أو من أمر نصي)
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        admin_id = query.from_user.id
        message_sender = query.edit_message_text
    else: # if called from a message command like /cancel
        admin_id = update.message.from_user.id
        message_sender = update.message.reply_text

    # حذف المنشور المؤقت من قاعدة البيانات
    await db.delete_temp_post(admin_id)

    await message_sender(
        text="تم إلغاء عملية إنشاء المنشور بنجاح.",
        reply_markup=None # Ensure any inline keyboards are removed
    )
    # لا نعود إلى لوحة التحكم الرئيسية تلقائياً، لكي لا تكون مربكة
    return ConversationHandler.END


def get_publishing_handlers() -> list:
    """تُرجع قائمة بالمعالجات الخاصة بنظام النشر."""
    
    publishing_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(new_post_start, pattern="^new_post$")],
        states={
            RECEIVING_CONTENT: [
                MessageHandler(filters.ALL & ~filters.COMMAND, receive_content)
            ],
            RECEIVING_BUTTONS: [
                CallbackQueryHandler(request_buttons_input, pattern="^add_buttons$"),
                CallbackQueryHandler(post_creation_finished, pattern="^skip_buttons$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_buttons),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_post_creation, pattern="^cancel_post$"),
            CommandHandler("cancel", cancel_post_creation)
        ],
        per_message=False,
        # إذا انتهت المحادثة بشكل غير متوقع، نلغيها
        conversation_timeout=300  # 5 minutes
    )

    return [publishing_conv_handler]
