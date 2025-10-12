# -*- coding: utf-8 -*-

from aiogram import types, Dispatcher

from config import ADMIN_USER_ID
from bot.handlers.user.start import is_user_subscribed

async def forward_message_to_admin(message: types.Message):
    """
    يعالج أي رسالة من المستخدم ويقوم بإعادة توجيهها إلى المدير
    مع إضافة معلومات المستخدم ومعرف الرسالة للرد عليها.
    """
    user_id = message.from_user.id
    
    if not await is_user_subscribed(user_id, message.bot):
        return

    try:
        # 1. إعادة توجيه الرسالة الأصلية (صورة, ملف, نص...)
        await message.forward(chat_id=ADMIN_USER_ID)
        
        # 2. إرسال رسالة نصية منفصلة بمعلومات المستخدم ومعرف الرسالة
        user_info = (
            f"رسالة جديدة من:\n"
            f"الاسم: {message.from_user.full_name}\n"
            f"المعرف: `{user_id}`\n"
            f"اسم المستخدم: @{message.from_user.username if message.from_user.username else 'لا يوجد'}\n"
            f"**معرف الرسالة للرد:** `{message.message_id}`" # <-- الإضافة الأهم
        )
        await message.bot.send_message(ADMIN_USER_ID, user_info, parse_mode=types.ParseMode.MARKDOWN)

    except Exception as e:
        print(f"فشل في إعادة توجيه الرسالة من المستخدم {user_id}: {e}")


def register_message_handlers(dp: Dispatcher):
    """
    تسجيل معالج الرسائل ليلتقط كل أنواع الرسائل.
    """
    dp.register_message_handler(forward_message_to_admin, content_types=types.ContentTypes.ANY)
