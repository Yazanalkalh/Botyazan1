# -*- coding: utf-8 -*-

from aiogram import types, Dispatcher
from config import ADMIN_USER_ID
import re

def _extract_reply_info(message: types.Message) -> (int | None, int | None):
    """
    وظيفة متخصصة لاستخراج معلومات الرد من النص أو التعليق.
    تبحث عن user_id و message_id.
    """
    text_to_search = message.text or message.caption
    if not text_to_search:
        return None, None

    # البحث عن النمط السري `user_id:123|message_id:456`
    match = re.search(r"`user_id:(\d+)\|message_id:(\d+)`", text_to_search)
    if match:
        user_id = int(match.group(1))
        message_id = int(match.group(2))
        return user_id, message_id
        
    return None, None


async def reply_to_user(message: types.Message):
    """
    يعالج ردود المدير على الرسائل المنسوخة ويرسلها كرد مباشر للمستخدم.
    """
    if message.from_user.id != ADMIN_USER_ID or not message.reply_to_message:
        return

    # استدعاء المحقق الخبير لاستخراج المعلومات من الرسالة التي يتم الرد عليها
    original_user_id, original_message_id = _extract_reply_info(message.reply_to_message)

    if not original_user_id or not original_message_id:
        return

    try:
        # الإرسال كرد مباشر للمستخدم الأصلي
        await message.bot.send_message(
            chat_id=original_user_id,
            text=message.text,
            reply_to_message_id=original_message_id
        )
        await message.reply("✅ تم إرسال ردك بنجاح.")

    except Exception as e:
        await message.reply(f"❌ فشل إرسال الرد. الخطأ: {e}")


def register_communication_handlers(dp: Dispatcher):
    """
    تسجيل معالج ردود المدير.
    """
    dp.register_message_handler(
        reply_to_user, 
        is_reply=True, 
        content_types=types.ContentTypes.TEXT
    )
