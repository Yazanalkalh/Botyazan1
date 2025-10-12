# -*- coding: utf-8 -*-

from telegram import Update
from telegram.ext import MessageHandler, filters, ContextTypes
from config import ADMIN_USER_ID

# --- شرح ---
# هذا الملف هو "مكتب المدير". يسمح للمدير بالرد على الرسائل التي تم توجيهها إليه
# من المستخدمين، ويقوم البوت بإيصال الرد بشكل سري.

async def reply_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يعالج رد المدير على رسالة موجهة من مستخدم."""
    # تأكد أن الرسالة من المدير وأنه يقوم بالرد على رسالة
    if update.effective_user.id != ADMIN_USER_ID or not update.message.reply_to_message:
        return

    replied_message = update.message.reply_to_message
    
    # تحقق مما إذا كان الرد على رسالة تعريفية أو رسالة موجهة
    user_id_to_reply = None
    if replied_message.forward_from:
        # إذا كانت الرسالة موجهة مباشرة
        user_id_to_reply = replied_message.forward_from.id
    elif replied_message.text and "رسالة جديدة من المستخدم" in replied_message.text:
        # إذا كان الرد على الرسالة التعريفية التي تحتوي على المعرف
        lines = replied_message.text.split('\n')
        for line in lines:
            if "المعرف:" in line:
                try:
                    user_id_to_reply = int(line.split('`')[1])
                    break
                except (ValueError, IndexError):
                    pass
    
    if user_id_to_reply:
        try:
            # أرسل رد المدير إلى المستخدم
            # نستخدم copy_message لإرسال كل أنواع الرسائل (نص، صورة، ملصق...)
            await context.bot.copy_message(
                chat_id=user_id_to_reply,
                from_chat_id=ADMIN_USER_ID,
                message_id=update.message.message_id
            )
            # إعلام المدير بنجاح الإرسال
            await update.message.reply_text("✅ تم إرسال ردك بنجاح.")
        except Exception as e:
            await update.message.reply_text(f"❌ لم أتمكن من إرسال الرد. قد يكون المستخدم قد حظر البوت.\nالخطأ: {e}")
    else:
        # هذا الرد ليس على رسالة من مستخدم، تجاهله
        return

# يستمع فقط للرسائل من المدير التي هي ردود
admin_reply_handler = MessageHandler(filters.User(user_id=ADMIN_USER_ID) & filters.REPLY, reply_to_user)
