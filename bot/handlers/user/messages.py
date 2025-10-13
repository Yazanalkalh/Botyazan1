# -*- coding: utf-8 -*-

import logging
from aiogram import types, Dispatcher, Bot

from config import ADMIN_USER_ID
from bot.database.manager import db
from bot.handlers.user.start import is_user_subscribed

logger = logging.getLogger(__name__)

# --- 💡 تم إصلاح هذه الدالة بالكامل 💡 ---
async def send_reply_from_data(bot: Bot, chat_id: int, reply_data: dict):
    """
    يقوم بإعادة إرسال الرسالة المخزنة باستخدام الطريقة الصحيحة (copy_message).
    """
    try:
        # نسترجع بيانات الرسالة الأصلية التي حفظها المدير
        message_info = reply_data.get('message', {})
        from_chat_id = message_info.get('chat', {}).get('id')
        message_id = message_info.get('message_id')

        if from_chat_id and message_id:
            await bot.copy_message(chat_id=chat_id, from_chat_id=from_chat_id, message_id=message_id)
        else:
             # حل احتياطي في حال كانت البيانات محفوظة بشكل قديم (نص فقط)
            await bot.send_message(chat_id=chat_id, text=message_info.get('text', '...'))

    except Exception as e:
        logger.error(f"فشل إرسال الرد التلقائي للمستخدم {chat_id}: {e}")

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
        logger.error(f"فشل إرسال بطاقة المستخدم: {e}")

# --- 💡 تم إعادة بناء هذه الدالة بالكامل بالترتيب المنطقي الصحيح 💡 ---
async def handle_user_message(message: types.Message):
    """
    يعالج أي رسالة من المستخدم بالترتيب الصحيح:
    1. الرد التلقائي أولاً.
    2. قواعد الحماية ثانياً.
    3. إعادة التوجيه أخيراً.
    """
    user = message.from_user
    bot = message.bot
    
    # نتجاهل رسائل المدير
    if user.id == ADMIN_USER_ID:
        return

    # --- الخطوة 1: التحقق من الرد التلقائي (له الأولوية القصوى) ---
    if message.text: # message.text يتحقق من وجود نص سواء كان لوحده أو مع وسائط
        reply_data = await db.find_auto_reply_by_keyword(message.text)
        if reply_data:
            await send_reply_from_data(bot, message.chat.id, reply_data)
            return # وجدنا رداً، نتوقف هنا

    # --- الخطوة 2: تطبيق قواعد الحماية والأمان ---
    settings = await db.get_security_settings()

    # التحقق من حالة البوت العامة
    if settings.get("bot_status") == "inactive":
        return # نتجاهل الرسالة تماماً

    # التحقق من الوسائط الممنوعة
    blocked_media = settings.get("blocked_media", {})
    rejection_message = await db.get_text("security_rejection_message")
    
    checks = {
        "photo": message.photo and blocked_media.get("photo"),
        "video": message.video and blocked_media.get("video"),
        "sticker": message.sticker and blocked_media.get("sticker"),
        "document": message.document and blocked_media.get("document"),
        "audio": message.audio and blocked_media.get("audio"),
        "voice": message.voice and blocked_media.get("voice"),
        "link": (message.entities and any(e.type in ['url', 'text_link'] for e in message.entities)) and blocked_media.get("link"),
    }
    
    if any(checks.values()):
        try:
            await message.reply(rejection_message)
        except Exception: pass
        return # نرفض الرسالة ونتوقف هنا
        
    # --- الخطوة 3: إذا مرت الرسالة، نطبق المنطق العادي ---
    if not await is_user_subscribed(user.id, bot):
        return

    # إعادة التوجيه للمدير
    try:
        await send_user_card_to_admin(user, bot)
        copied_message = await message.copy_to(ADMIN_USER_ID)
        await db.log_message_link(
            admin_message_id=copied_message.message_id,
            user_id=user.id,
            user_message_id=message.message_id
        )
        await message.reply("✅ تم استلام رسالتك بنجاح، سيتم الرد عليك قريباً.")
    except Exception as e:
        logger.error(f"فشل في معالجة الرسالة من المستخدم {user.id}: {e}")
        await message.reply("عذراً، حدث خطأ أثناء إرسال رسالتك.")


def register_messages_handler(dp: Dispatcher):
    """وظيفة التسجيل التلقائي لهذه الوحدة."""
    dp.register_message_handler(handle_user_message, content_types=types.ContentTypes.ANY)
