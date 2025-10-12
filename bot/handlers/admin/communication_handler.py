# -*- coding: utf-8 -*-

from aiogram import types, Dispatcher
from config import ADMIN_USER_ID
from bot.database.manager import db

async def reply_to_user(message: types.Message):
    """
    يعالج ردود المدير باستخدام نظام الربط في قاعدة البيانات.
    """
    if message.from_user.id != ADMIN_USER_ID or not message.reply_to_message:
        return

    admin_message_id = message.reply_to_message.message_id
    
    # --- البحث في "سجل البريد" عن المعلومات الصحيحة ---
    forward_info = await db.get_forwarded_message_info(admin_message_id)

    if not forward_info:
        return

    original_user_id = forward_info.get("user_id")
    original_message_id = forward_info.get("user_message_id")

    try:
        # --- الإرسال كرد مباشر للمستخدم الأصلي ---
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
