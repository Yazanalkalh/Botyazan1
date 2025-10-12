# -*- coding: utf-8 -*-

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from config import ADMIN_USER_ID
import re

async def admin_reply_handler_func(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # التأكد أن الرسالة من المدير وهي رد على رسالة أخرى
    if str(update.effective_user.id) != ADMIN_USER_ID or not update.message.reply_to_message:
        return
        
    # استخراج ID المستخدم الأصلي من الرسالة التي تم الرد عليها
    original_message = update.message.reply_to_message
    user_id = None
    
    # الطريقة الأولى: من نص الرسالة التعريفية
    if original_message.text and "ID:" in original_message.text:
        match = re.search(r'ID: `(\d+)`', original_message.text)
        if match:
            user_id = int(match.group(1))

    # الطريقة الثانية (احتياطية): من الرسالة المعاد توجيهها
    elif original_message.forward_from:
        user_id = original_message.forward_from.id

    if user_id:
        try:
            # إرسال رد المدير إلى المستخدم
            await context.bot.send_message(
                chat_id=user_id,
                text=update.message.text # نص رد المدير
            )
            # إعلام المدير بنجاح الإرسال
            await update.message.reply_text("✅ تم إرسال ردك بنجاح.")
        except Exception as e:
            await update.message.reply_text(f"❌ فشل إرسال الرد. قد يكون المستخدم قد حظر البوت.\nالخطأ: {e}")
    else:
        # إذا لم يتمكن من تحديد المستخدم، لا يفعل شيئاً أو يرسل رسالة خطأ للمدير
        pass

admin_reply_handler = MessageHandler(filters.REPLY & filters.User(user_id=int(ADMIN_USER_ID)), admin_reply_handler_func)
