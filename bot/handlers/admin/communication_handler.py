# -*- coding: utf-8 -*-

from aiogram import types, Dispatcher
from config import ADMIN_USER_ID

async def reply_to_user(message: types.Message):
    """
    يعالج ردود المدير على الرسائل المعاد توجيهها.
    """
    # التأكد من أن المرسل هو المدير، وأن الرسالة هي رد على رسالة أخرى
    if message.from_user.id != ADMIN_USER_ID or not message.reply_to_message:
        return

    # التأكد من أن الرسالة التي يتم الرد عليها هي رسالة معاد توجيهها
    if not message.reply_to_message.forward_from:
        return

    # الحصول على معرّف المستخدم الأصلي من الرسالة المعاد توجيهها
    original_user_id = message.reply_to_message.forward_from.id

    try:
        # إرسال رد المدير إلى المستخدم الأصلي
        # ملاحظة: هذه الطريقة لا تقوم بعمل "رد" على رسالة المستخدم الأصلية،
        # ولكنها تضمن وصول الرسالة إليه، وهو الأهم.
        await message.bot.send_message(
            chat_id=original_user_id,
            text=message.text
        )
        await message.reply("✅ تم إرسال ردك بنجاح.")

    except Exception as e:
        await message.reply(f"❌ فشل إرسال الرد. الخطأ: {e}")


def register_communication_handlers(dp: Dispatcher):
    """تسجيل معالج ردود المدير."""
    dp.register_message_handler(
        reply_to_user, 
        is_reply=True, 
        content_types=types.ContentTypes.TEXT
    )
