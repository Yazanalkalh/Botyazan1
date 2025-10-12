# -*- coding: utf-8 -*-

from aiogram import types, Dispatcher

from config import ADMIN_USER_ID
from bot.handlers.user.start import is_user_subscribed
from bot.database.manager import db

async def handle_user_message(message: types.Message):
    """
    يعالج أي رسالة من المستخدم، ينسخها للمدير، ويسجلها في قاعدة البيانات.
    """
    # --- الإصلاح رقم 3: تجاهل رسائل المدير ---
    if message.from_user.id == ADMIN_USER_ID:
        return

    if not await is_user_subscribed(message.from_user.id, message.bot):
        return

    try:
        # نسخ الرسالة إلى المدير
        copied_message = await message.copy_to(ADMIN_USER_ID)
        
        # --- الإصلاح رقم 1: تسجيل الربط في قاعدة البيانات ---
        await db.log_forwarded_message(
            admin_message_id=copied_message.message_id,
            user_id=message.from_user.id,
            user_message_id=message.message_id
        )
        
        await message.reply("✅ تم استلام رسالتك بنجاح.")

    except Exception as e:
        print(f"فشل في معالجة الرسالة من المستخدم {message.from_user.id}: {e}")
        await message.reply("عذراً، حدث خطأ أثناء إرسال رسالتك.")


def register_message_handlers(dp: Dispatcher):
    dp.register_message_handler(handle_user_message, content_types=types.ContentTypes.ANY)
