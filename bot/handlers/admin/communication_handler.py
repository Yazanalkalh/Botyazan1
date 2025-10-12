# -*- coding: utf-8 -*-

from aiogram import types, Dispatcher
from config import ADMIN_USER_ID
import re

async def reply_to_user(message: types.Message):
    """
    يعالج ردود المدير على الرسائل المنسوخة ويقوم بإرسالها كرد مباشر للمستخدم.
    """
    # التأكد من أن المرسل هو المدير، وأن الرسالة هي رد
    if message.from_user.id != ADMIN_USER_ID or not message.reply_to_message:
        return

    original_user_id = None
    original_message_id = None
    
    # النص الذي سنبحث فيه عن المعرفات هو التعليق (caption)
    caption = message.reply_to_message.caption
    
    if caption:
        # البحث عن معرف المستخدم ومعرف الرسالة باستخدام التعبيرات النمطية
        user_id_match = re.search(r"User ID:\s*`(\d+)`", caption)
        message_id_match = re.search(r"Message ID:\s*`(\d+)`", caption)

        if user_id_match:
            original_user_id = int(user_id_match.group(1))
        
        if message_id_match:
            original_message_id = int(message_id_match.group(1))

    # إذا لم نجد المعرفات المطلوبة في التعليق، نتوقف
    if not original_user_id or not original_message_id:
        return

    try:
        # --- الإرسال كرد مباشر للمستخدم الأصلي ---
        await message.bot.send_message(
            chat_id=original_user_id,
            text=message.text, # نص رسالة المدير فقط
            reply_to_message_id=original_message_id # <-- هنا يحدث السحر
        )
        # إعلام المدير بنجاح الإرسال (اختياري)
        await message.reply("✅ تم إرسال ردك بنجاح.")

    except Exception as e:
        await message.reply(f"❌ فشل إرسال الرد. قد يكون المستخدم قد حظر البوت.\n\nالخطأ: {e}")


def register_communication_handlers(dp: Dispatcher):
    """
    تسجيل معالج ردود المدير.
    """
    # سيعمل هذا المعالج فقط عندما يرد المدير على أي نوع من الرسائل
    dp.register_message_handler(
        reply_to_user, 
        is_reply=True, 
        content_types=types.ContentTypes.TEXT
    )
