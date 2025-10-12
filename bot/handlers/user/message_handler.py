# -*- coding: utf-8 -*-

from aiogram import types, Dispatcher, Bot

from config import ADMIN_USER_ID
from bot.handlers.user.start import is_user_subscribed
from bot.database.manager import db

async def send_user_card_to_admin(user: types.User, bot: Bot):
    """يرسل بطاقة تعريف المستخدم إلى المدير."""
    try:
        # استخدام HTML لضمان الاستقرار
        user_link = f'<a href="tg://user?id={user.id}">{user.full_name}</a>'
        username = f"@{user.username}" if user.username else "لا يوجد"
        
        notification_text = (
            f"👤 <b>رسالة من مستخدم</b>\n\n"
            f"🗣️ <b>اسمه:</b> {user_link}\n"
            f"🌀 <b>معرفه:</b> {username}\n"
            f"🆔 <b>ايديه:</b> <code>{user.id}</code>"
        )
        
        await bot.send_message(
            chat_id=ADMIN_USER_ID,
            text=notification_text,
            parse_mode=types.ParseMode.HTML
        )
    except Exception as e:
        print(f"فشل إرسال بطاقة المستخدم: {e}")


async def handle_user_message(message: types.Message):
    """
    يعالج أي رسالة من المستخدم، ينسخها للمدير، ويسجلها في قاعدة البيانات.
    """
    # تجاهل رسائل المدير نفسه
    if message.from_user.id == ADMIN_USER_ID:
        return

    if not await is_user_subscribed(message.from_user.id, message.bot):
        return

    try:
        # --- الخطوة الجديدة: إرسال بطاقة التعريف مع كل رسالة ---
        await send_user_card_to_admin(message.from_user, message.bot)

        # نسخ الرسالة إلى المدير
        copied_message = await message.copy_to(ADMIN_USER_ID)
        
        # تسجيل الربط في قاعدة البيانات (الحل المضمون)
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
