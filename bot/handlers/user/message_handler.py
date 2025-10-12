# -*- coding: utf-8 -*-

from aiogram import types, Dispatcher

from config import ADMIN_USER_ID
from bot.handlers.user.start import is_user_subscribed

async def forward_message_to_admin(message: types.Message):
    """
    يقوم بإعادة توجيه رسالة المستخدم إلى المدير.
    """
    if not await is_user_subscribed(message.from_user.id, message.bot):
        return

    try:
        # إعادة توجيه الرسالة كما هي
        await message.forward(ADMIN_USER_ID)
        
        # إرسال رسالة تأكيد للمستخدم
        await message.reply("✅ تم استلام رسالتك بنجاح.")

    except Exception as e:
        print(f"فشل في إعادة توجيه الرسالة من المستخدم {message.from_user.id}: {e}")
        await message.reply("عذراً، حدث خطأ أثناء إرسال رسالتك.")


def register_message_handlers(dp: Dispatcher):
    """تسجيل معالج الرسائل."""
    dp.register_message_handler(handle_user_message, content_types=types.ContentTypes.ANY)
