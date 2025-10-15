# -*- coding: utf-8 -*-

import logging
from aiogram import types, Dispatcher, Bot

from config import ADMIN_USER_ID
from bot.database.manager import db
from bot.handlers.user.start import is_user_subscribed

logger = logging.getLogger(__name__)

async def send_reply_from_data(bot: Bot, chat_id: int, reply_data: dict):
    """
    يقوم بإعادة إرسال الرسالة المخزنة باستخدام الطريقة الصحيحة (copy_message).
    """
    try:
        message_info = reply_data.get('message', {})
        from_chat_id = message_info.get('chat', {}).get('id')
        message_id = message_info.get('message_id')

        if from_chat_id and message_id:
            await bot.copy_message(chat_id=chat_id, from_chat_id=from_chat_id, message_id=message_id)
        else:
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

# --- 💡 تم إعادة بناء هذه الدالة بالكامل لتطبيق منطق السرعة القصوى 💡 ---
async def handle_user_message(message: types.Message):
    """
    يعالج رسائل المستخدم بمنطق "الصاروخ" (الأسرع أولاً).
    """
    user = message.from_user
    bot = message.bot
    
    # نتجاهل رسائل المدير
    if user.id == ADMIN_USER_ID:
        return

    # --- الخطوة 1: التحقق من إعدادات الأمان (سريعة جدًا) ---
    # نجلب الإعدادات مرة واحدة فقط ونعيد استخدامها
    settings = await db.get_security_settings()
    if settings.get("bot_status") == "inactive":
        return # أسرع فحص، نتوقف هنا فورًا

    # --- الخطوة 2: التحقق من الرد التلقائي (سريع) ---
    if message.text:
        reply_data = await db.find_auto_reply_by_keyword(message.text)
        if reply_data:
            await send_reply_from_data(bot, message.chat.id, reply_data)
            return # وجدنا رداً، نتوقف هنا

    # --- الخطوة 3: التحقق من الوسائط الممنوعة (سريع) ---
    blocked_media = settings.get("blocked_media", {})
    
    # هذا الأسلوب أسرع من بناء قاموس في كل مرة
    if (message.photo and blocked_media.get("photo")) or \
       (message.video and blocked_media.get("video")) or \
       (message.sticker and blocked_media.get("sticker")) or \
       (message.document and blocked_media.get("document")) or \
       (message.audio and blocked_media.get("audio")) or \
       (message.voice and blocked_media.get("voice")) or \
       ((message.entities and any(e.type in ['url', 'text_link'] for e in message.entities)) and blocked_media.get("link")):
        
        rejection_message = await db.get_text("security_rejection_message")
        try:
            await message.reply(rejection_message)
        except Exception: pass
        return # نرفض الرسالة ونتوقف هنا
        
    # --- الخطوة 4: التحقق من الاشتراك الإجباري (أبطأ عملية، نتركها للنهاية) ---
    if not await is_user_subscribed(user.id, bot):
        return # إذا لم يكن مشتركًا، نتوقف هنا

    # --- الخطوة 5: إذا مرت الرسالة من كل شيء، يتم توجيهها للمدير ---
    try:
        await send_user_card_to_admin(user, bot)
        copied_message = await message.copy_to(ADMIN_USER_ID)
        await db.log_message_link(
            admin_message_id=copied_message.message_id,
            user_id=user.id,
            user_message_id=message.message_id
        )
        
        confirmation_text = await db.get_text("user_message_received")
        await message.reply(confirmation_text, parse_mode="HTML")

    except Exception as e:
        logger.error(f"فشل في معالجة الرسالة من المستخدم {user.id}: {e}")
        await message.reply("عذراً، حدث خطأ أثناء إرسال رسالتك.")


def register_messages_handler(dp: Dispatcher):
    """وظيفة التسجيل التلقائي لهذه الوحدة."""
    # نجعل هذا المعالج هو الأخير ليتم فحصه، مما يعطي الأولوية للأوامر والمعالجات المحددة
    dp.register_message_handler(handle_user_message, content_types=types.ContentTypes.ANY)
