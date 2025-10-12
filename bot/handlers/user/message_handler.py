# -*- coding: utf-8 -*-

from aiogram import types, Dispatcher

from config import ADMIN_USER_ID
from bot.handlers.user.start import is_user_subscribed

async def handle_user_message(message: types.Message):
    """
    يعالج أي رسالة من المستخدم، ويرسلها للمدير مع معلومات الرد المضمنة.
    """
    user_id = message.from_user.id
    
    if not await is_user_subscribed(user_id, message.bot):
        return

    try:
        # بناء معلومات الرد التي سيتم إضافتها
        reply_info = (
            f"\n\n--- معلومات الرد ---\n"
            f"User ID: `{user_id}`\n"
            f"Message ID: `{message.message_id}`\n"
            f"--------------------"
        )
        
        # التعامل مع النصوص والوسائط بشكل مختلف لضمان وصول المعلومات
        if message.content_type == types.ContentType.TEXT:
            # للرسائل النصية: نرسل رسالة جديدة تجمع النص الأصلي ومعلومات الرد
            await message.bot.send_message(
                chat_id=ADMIN_USER_ID,
                text=message.text + reply_info,
                parse_mode=types.ParseMode.MARKDOWN
            )
        else:
            # لبقية الأنواع (صور، ملفات...): نستخدم copy_to ونضيف المعلومات للتعليق
            await message.copy_to(
                chat_id=ADMIN_USER_ID,
                caption=(message.caption or "") + reply_info,
                parse_mode=types.ParseMode.MARKDOWN
            )

        # إرسال رسالة تأكيد للمستخدم
        await message.reply("✅ تم استلام رسالتك بنجاح، سيتم الرد عليك قريباً.")

    except Exception as e:
        print(f"فشل في معالجة الرسالة من المستخدم {user_id}: {e}")
        await message.reply("عذراً، حدث خطأ أثناء محاولة إرسال رسالتك.")


def register_message_handlers(dp: Dispatcher):
    """تسجيل معالج الرسائل."""
    dp.register_message_handler(
        handle_user_message, 
        content_types=types.ContentTypes.ANY
    )
