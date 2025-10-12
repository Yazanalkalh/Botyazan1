# -*- coding: utf-8 -*-

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from config import ADMIN_USER_ID
from bot.handlers.user.start import is_user_subscribed

async def message_forwarder_handler_func(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    
    # التحقق من الاشتراك قبل توصيل الرسالة
    if not await is_user_subscribed(user.id, context):
        # يمكن إرسال رسالة تذكير بالاشتراك هنا أو التجاهل بصمت
        return

    # رسالة تعريفية بالمرسل
    user_info = f"رسالة جديدة من:\n"
    user_info += f"الاسم: {user.first_name}\n"
    if user.username:
        user_info += f"المعرف: @{user.username}\n"
    user_info += f"ID: `{user.id}`\n\n"
    user_info += "للرد على هذه الرسالة، استخدم ميزة الرد (Reply)."

    try:
        # إرسال المعلومات أولاً
        await context.bot.send_message(
            chat_id=ADMIN_USER_ID,
            text=user_info,
            parse_mode='MarkdownV2'
        )
        # ثم إعادة توجيه الرسالة الأصلية
        await update.message.forward(chat_id=ADMIN_USER_ID)
    except Exception as e:
        print(f"فشل في توصيل رسالة من {user.id}: {e}")
        # يمكن إعلام المستخدم بحدوث خطأ هنا إذا أردنا
        await update.message.reply_text("عذراً، حدث خطأ أثناء محاولة إيصال رسالتك. يرجى المحاولة مرة أخرى لاحقاً.")

message_forwarder_handler = MessageHandler(filters.ALL & ~filters.COMMAND, message_forwarder_handler_func)
