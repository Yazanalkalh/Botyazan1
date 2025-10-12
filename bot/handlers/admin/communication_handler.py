# -*- coding: utf-8 -*-

from aiogram import types, Dispatcher
from config import ADMIN_USER_ID

async def reply_to_user(message: types.Message):
    """
    يعالج ردود المدير على الرسائل التي تم إعادة توجيهها من المستخدمين.
    """
    # التأكد من أن المرسل هو المدير، وأن الرسالة هي رد على رسالة أخرى
    if message.from_user.id != ADMIN_USER_ID or not message.reply_to_message:
        return

    # --- استخراج معرّف المستخدم الأصلي ---
    original_user_id = None
    
    # الطريقة الأولى والأكثر دقة: من الرسالة النصية التي أرسلناها
    if (message.reply_to_message.forward_from is None and 
        message.reply_to_message.text and "رسالة جديدة من:" in message.reply_to_message.text):
        try:
            # استخراج السطر الذي يحتوي على المعرف
            id_line = [line for line in message.reply_to_message.text.split('\n') if line.startswith("المعرف:")][0]
            # استخراج الرقم من السطر
            original_user_id = int(id_line.replace("المعرف:", "").replace("`", "").strip())
        except (IndexError, ValueError):
            pass # لم يتم العثور على المعرف بالطريقة المتوقعة

    # الطريقة الثانية (احتياطية): من الرسالة المعاد توجيهها مباشرة
    elif message.reply_to_message.forward_from:
        original_user_id = message.reply_to_message.forward_from.id

    if not original_user_id:
        # إذا لم نتمكن من العثور على معرّف المستخدم، لا نفعل شيئاً
        return

    try:
        # إرسال رد المدير إلى المستخدم الأصلي
        await message.bot.send_message(
            chat_id=original_user_id,
            text=f"✉️ **رد من الإدارة:**\n\n{message.text}",
            parse_mode=types.ParseMode.MARKDOWN
        )
        # (اختياري) إعلام المدير بأن الرد قد تم إرساله بنجاح
        await message.reply("✅ تم إرسال ردك بنجاح.")

    except Exception as e:
        await message.reply(f"❌ فشل إرسال الرد. قد يكون المستخدم قد حظر البوت.\n\nالخطأ: {e}")


def register_communication_handlers(dp: Dispatcher):
    """
    تسجيل معالج ردود المدير.
    is_reply=True تعني أنه سيعمل فقط عندما تكون الرسالة رداً.
    """
    dp.register_message_handler(reply_to_user, is_reply=True, content_types=types.ContentTypes.TEXT)
