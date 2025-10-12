# -*- coding: utf-8 -*-

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, filters
from config import ADMIN_USER_ID
from bot.handlers.user.start import is_user_subscribed  # <-- استدعاء "حارس الأمن" الخبير
from bot.database.manager import db

async def message_forwarder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    يعيد توجيه أي رسالة من المستخدم إلى المدير، بعد التحقق من الاشتراك.
    """
    user = update.effective_user
    
    # --- استدعاء "حارس الأمن" الخبير أولاً ---
    not_subscribed_channels = await is_user_subscribed(user.id, context)
    
    if not_subscribed_channels:
        # إذا لم يكن مشتركاً، أرسل له رسالة الاشتراك الإجباري بدلاً من توجيه رسالته
        force_sub_message = await db.get_text("force_sub_message", "عذراً، يجب عليك الاشتراك في القنوات التالية لاستخدام البوت:")
        keyboard = []
        for channel in not_subscribed_channels:
            keyboard.append([InlineKeyboardButton(channel['title'], url=f"https://t.me/{channel['channel_id']}")])
        keyboard.append([InlineKeyboardButton("✅ لقد اشتركت، تحقق مرة أخرى", callback_data="check_subscription")])
        
        await update.message.reply_text(
            force_sub_message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # --- إذا كان مشتركاً، قم بإعادة توجيه الرسالة ---
    try:
        await context.bot.forward_message(
            chat_id=ADMIN_USER_ID,
            from_chat_id=user.id,
            message_id=update.message.message_id
        )
    except Exception as e:
        print(f"Failed to forward message from {user.id}: {e}")
        # يمكنك إرسال رسالة للمستخدم هنا لإبلاغه بحدوث خطأ
        # await update.message.reply_text("عذراً، لم أتمكن من توصيل رسالتك. يرجى المحاولة مرة أخرى لاحقاً.")

# معالج لجميع أنواع الرسائل (نص، صور، فيديو، الخ) التي ليست أوامر
message_forwarder_handler = MessageHandler(filters.ALL & ~filters.COMMAND, message_forwarder)
