# -*- coding: utf-8 -*-

from aiogram import types, Dispatcher, Bot

from config import ADMIN_USER_ID
from bot.database.manager import db
from bot.handlers.user.start import is_user_subscribed

async def send_user_card_to_admin(user: types.User, bot: Bot):
    """يرسل بطاقة تعريف المستخدم إلى المدير."""
    try:
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
    يعالج أي رسالة من المستخدم، يرسل بطاقته، ينسخ رسالته للمدير،
    ويسجلها في قاعدة البيانات لنظام الرد.
    """
    if message.from_user.id == ADMIN_USER_ID:
        return
    if not await is_user_subscribed(message.from_user.id, message.bot):
        return

    try:
        # 1. إرسال بطاقة تعريف المستخدم
        await send_user_card_to_admin(message.from_user, message.bot)

        # 2. نسخ رسالة المستخدم إلى المدير
        copied_message = await message.copy_to(ADMIN_USER_ID)
        
        # 3. تسجيل الربط في قاعدة البيانات (هذا السطر سيعمل الآن)
        await db.log_message_link(
            admin_message_id=copied_message.message_id,
            user_id=message.from_user.id,
            user_message_id=message.message_id
        )
        
        # 4. إرسال رسالة تأكيد للمستخدم
        await message.reply("✅ تم استلام رسالتك بنجاح، سيتم الرد عليك قريباً.")

    except Exception as e:
        print(f"فشل في معالجة الرسالة من المستخدم {message.from_user.id}: {e}")
        await message.reply("عذراً، حدث خطأ أثناء إرسال رسالتك.")


def register_messages_handler(dp: Dispatcher):
    """وظيفة التسجيل التلقائي لهذه الوحدة."""
    dp.register_message_handler(handle_user_message, content_types=types.ContentTypes.ANY)
