
# -*- coding: utf-8 -*-

from aiogram import types, Dispatcher
from config import ADMIN_USER_ID
from bot.database.manager import db

async def reply_to_user(message: types.Message):
    """
    يعالج ردود المدير باستخدام نظام الربط في قاعدة البيانات.
    """
    # 1. التأكد من أن المرسل هو المدير، وأن الرسالة هي رد
    if message.from_user.id != ADMIN_USER_ID or not message.reply_to_message:
        return

    # 2. الحصول على "رقم الإيصال" (معرف رسالة المدير التي يتم الرد عليها)
    admin_message_id = message.reply_to_message.message_id
    
    # 3. البحث في "سجل البريد" عن المعلومات الصحيحة
    link_info = await db.get_message_link_info(admin_message_id)

    # إذا لم نجد معلومات، فهذا يعني أنها ليست رسالة من مستخدم (نتجاهلها)
    if not link_info:
        return

    original_user_id = link_info.get("user_id")
    original_message_id = link_info.get("user_message_id")

    try:
        # 4. إرسال الرد كرد مباشر للمستخدم الأصلي
        await message.bot.send_message(
            chat_id=original_user_id,
            text=message.text,
            reply_to_message_id=original_message_id
        )
        # 5. إعلام المدير بنجاح الإرسال
        await message.reply("✅ تم إرسال ردك بنجاح.")

    except Exception as e:
        await message.reply(f"❌ فشل إرسال الرد. الخطأ: {e}")


def register_communication_handlers(dp: Dispatcher):
    """وظيفة التسجيل التلقائي لهذه الوحدة."""
    # هذا المعالج سيعمل فقط عندما يرد المدير على أي رسالة نصية
    dp.register_message_handler(
        reply_to_user, 
        is_reply=True, 
        content_types=types.ContentTypes.TEXT
    )
