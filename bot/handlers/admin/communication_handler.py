# -*- coding: utf-8 -*-

from aiogram import types, Dispatcher
from config import ADMIN_USER_ID
import re

async def reply_to_user(message: types.Message):
    """
    يعالج ردود المدير على الرسائل ويقوم بإرسالها كرد مباشر للمستخدم.
    """
    if message.from_user.id != ADMIN_USER_ID or not message.reply_to_message:
        return

    original_user_id = None
    original_message_id = None

    # --- استخراج المعرفات من الرسالة التي يتم الرد عليها ---
    replied_text = message.reply_to_message.text
    if replied_text:
        # البحث عن معرف المستخدم ومعرف الرسالة باستخدام التعبيرات النمطية
        user_id_match = re.search(r"المعرف:\s*`(\d+)`", replied_text)
        message_id_match = re.search(r"معرف الرسالة للرد:\s*`(\d+)`", replied_text)

        if user_id_match:
            original_user_id = int(user_id_match.group(1))
        
        if message_id_match:
            original_message_id = int(message_id_match.group(1))

    # إذا لم نتمكن من استخراج المعرفات، نتوقف
    if not original_user_id or not original_message_id:
        return

    try:
        # --- الإرسال كرد مباشر ---
        await message.bot.send_message(
            chat_id=original_user_id,
            text=message.text, # نص رسالة المدير فقط
            reply_to_message_id=original_message_id # <-- السحر يحدث هنا
        )
        await message.reply("✅ تم إرسال ردك بنجاح كرد مباشر.")

    except Exception as e:
        await message.reply(f"❌ فشل إرسال الرد. قد يكون المستخدم قد حظر البوت.\n\nالخطأ: {e}")


def register_communication_handlers(dp: Dispatcher):
    """
    تسجيل معالج ردود المدير.
    """
    # سيعمل هذا المعالج فقط عندما يرد المدير على رسالة نصية
    dp.register_message_handler(reply_to_user, is_reply=True, content_types=types.ContentTypes.TEXT)
