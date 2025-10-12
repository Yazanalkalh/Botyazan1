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
        # هذا هو المفتاح الذي سنستخدمه للرد
        hidden_metadata = f"\n\n`user_id:{user_id}|message_id:{message.message_id}`"

        # استخدام copy_message لإرسال نسخة من الرسالة
        # ونضيف المعلومات السرية إلى التعليق أو النص
        if message.caption:
            await message.copy_to(
                ADMIN_USER_ID,
                caption=message.caption + hidden_metadata,
                parse_mode=types.ParseMode.MARKDOWN
            )
        elif message.text:
            await message.bot.send_message(
                ADMIN_USER_ID,
                message.text + hidden_metadata,
                parse_mode=types.ParseMode.MARKDOWN
            )
        else:
            await message.copy_to(
                ADMIN_USER_ID,
                caption=hidden_metadata,
                parse_mode=types.ParseMode.MARKDOWN
            )

        # إرسال رسالة تأكيد للمستخدم
        await message.reply("✅ تم استلام رسالتك بنجاح، سيتم الرد عليك قريباً.")

    except Exception as e:
        print(f"فشل في نسخ الرسالة من المستخدم {user_id}: {e}")
        await message.reply("عذراً، حدث خطأ أثناء محاولة إرسال رسالتك.")


def register_message_handlers(dp: Dispatcher):
    """
    تسجيل معالج الرسائل.
    """
    dp.register_message_handler(
        copy_message_to_admin, 
        content_types=types.ContentTypes.ANY
    )
