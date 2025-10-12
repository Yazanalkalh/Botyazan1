# -*- coding: utf-8 -*-

from aiogram import types, Dispatcher
from config import ADMIN_USER_ID
import re

def _extract_reply_info(message: types.Message) -> (int | None, int | None):
    """
    وظيفة متخصصة لاستخراج معلومات الرد من نص أو تعليق.
    """
    text_to_search = message.caption or message.text
    if not text_to_search:
        return None, None

    user_id_match = re.search(r"User ID:\s*`(\d+)`", text_to_search)
    message_id_match = re.search(r"Message ID:\s*`(\d+)`", text_to_search)

    user_id = int(user_id_match.group(1)) if user_id_match else None
    message_id = int(message_id_match.group(1)) if message_id_match else None
        
    return user_id, message_id


async def reply_to_user(message: types.Message):
    """
    يعالج ردود المدير ويرسلها كرد مباشر للمستخدم.
    """
    if message.from_user.id != ADMIN_USER_ID or not message.reply_to_message:
        return

    original_user_id, original_message_id = _extract_reply_info(message.reply_to_message)

    if not original_user_id or not original_message_id:
        return

    try:
        # --- الإرسال كرد مباشر للمستخدم الأصلي ---
        # هذا هو السطر الذي تم حذفه بالخطأ وإعادته الآن
        await message.bot.send_message(
            chat_id=original_user_id,
            text=message.text,
            reply_to_message_id=original_message_id
        )
        await message.reply("✅ تم إرسال ردك بنجاح.")

    except Exception as e:
        await message.reply(f"❌ فشل إرسال الرد. الخطأ: {e}")


def register_communication_handlers(dp: Dispatcher):
    dp.register_message_handler(reply_to_user, is_reply=True, content_types=types.ContentTypes.TEXT)
