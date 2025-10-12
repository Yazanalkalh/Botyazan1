# -*- coding: utf-8 -*-

from aiogram import types, Dispatcher

from config import ADMIN_USER_ID
from bot.handlers.user.start import is_user_subscribed

async def copy_message_to_admin(message: types.Message):
    """
    يعالج أي رسالة من المستخدم، يقوم بنسخها وإضافة معلومات الرد في التعليق.
    """
    user_id = message.from_user.id
    
    if not await is_user_subscribed(user_id, message.bot):
        return

    try:
        # بناء التعليق الذي يحتوي على معلومات الرد
        reply_info = (
            f"--- معلومات الرد ---\n"
            f"User ID: `{user_id}`\n"
            f"Message ID: `{message.message_id}`\n"
            f"--------------------"
        )
        
        # استخدام copy_message لإرسال نسخة من الرسالة مع التعليق
        # هذا يعمل مع كل أنواع الرسائل (نص، صور، ملفات...)
        await message.copy_to(
            chat_id=ADMIN_USER_ID,
            caption=reply_info,
            parse_mode=types.ParseMode.MARKDOWN
        )

    except Exception as e:
        print(f"فشل في نسخ الرسالة من المستخدم {user_id}: {e}")


def register_message_handlers(dp: Dispatcher):
    """
    تسجيل معالج الرسائل ليلتقط كل أنواع الرسائل ما عدا الأوامر.
    """
    dp.register_message_handler(
        copy_message_to_admin, 
        content_types=types.ContentTypes.ANY,
        # التأكد من أنه لا يلتقط الأوامر مثل /start
        is_command=False 
    )
