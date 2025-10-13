# -*- coding: utf-8 -*-

import logging
from aiogram import types, Dispatcher, Bot

from config import ADMIN_USER_ID
from bot.database.manager import db
from bot.handlers.user.start import is_user_subscribed

logger = logging.getLogger(__name__)

# --- دالة مساعدة لإرسال الردود المخزنة ---
async def send_reply_from_data(chat_id: int, reply_data: dict):
    """
    يقوم بإعادة إرسال الرسالة المخزنة في قاعدة البيانات.
    """
    try:
        message_content = reply_data.get('message', {})
        message_to_send = types.Message.to_object(message_content)
        await message_to_send.send_copy(chat_id)
    except Exception as e:
        logger.error(f"فشل إرسال الرد التلقائي للمستخدم {chat_id}: {e}")

# --- دالة مساعدة لإرسال بطاقة المستخدم للمدير ---
async def send_user_card_to_admin(user: types.User, bot: Bot):
    """يرسل بطاقة تعريف المستخدم إلى المدير."""
    try:
        user_link = f'<a href="tg://user?id={user.id}">{user.full_name}</a>'
        username = f"@{user.username}" if user.username else "لا يوجد"
        
        notification_text = (
            f"👤 <b>رسالة من مستخدم</b>\n\n"
            f"🗣️ <b>اسمه:</b> {user_link}\n"
            f"🌀 <b>معرفه:</b> {username}\n"
            f"🆔 <b>ايديه:</b> <code>{user.id}</code>"
        )
        
        await bot.send_message(
            chat_id=ADMIN_USER_ID,
            text=notification_text,
            parse_mode=types.ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"فشل إرسال بطاقة المستخدم: {e}")

async def handle_user_message(message: types.Message):
    """
    يعالج أي رسالة من المستخدم.
    1. يتحقق من وجود رد تلقائي أولاً.
    2. إذا لم يجد، يقوم بإعادة توجيه الرسالة للمدير.
    """
    if message.from_user.id == ADMIN_USER_ID:
        return
    if not await is_user_subscribed(message.from_user.id, message.bot):
        return

    # ====> هذا هو المنطق الصحيح <====
    # 1. التحقق من الرد التلقائي أولاً (فقط للرسائل النصية)
    if message.content_type == types.ContentType.TEXT:
        reply_data = await db.find_auto_reply_by_keyword(message.text)
        if reply_data:
            await send_reply_from_data(message.chat.id, reply_data)
            return # نتوقف هنا لأننا وجدنا رداً

    # 2. إذا لم يتم العثور على رد، نقوم بإعادة التوجيه للمدير
    try:
        await send_user_card_to_admin(message.from_user, message.bot)
        copied_message = await message.copy_to(ADMIN_USER_ID)
        await db.log_message_link(
            admin_message_id=copied_message.message_id,
            user_id=message.from_user.id,
            user_message_id=message.message_id
        )
        await message.reply("✅ تم استلام رسالتك بنجاح، سيتم الرد عليك قريباً.")

    except Exception as e:
        logger.error(f"فشل في معالجة الرسالة من المستخدم {message.from_user.id}: {e}")
        await message.reply("عذراً، حدث خطأ أثناء إرسال رسالتك.")


def register_messages_handler(dp: Dispatcher):
    """وظيفة التسجيل التلقائي لهذه الوحدة."""
    dp.register_message_handler(handle_user_message, content_types=types.ContentTypes.ANY)
