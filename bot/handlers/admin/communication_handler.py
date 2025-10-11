# -*- coding: utf-8 -*-

from telegram import Update
from telegram.ext import MessageHandler, filters, ContextTypes

from config import ADMIN_USER_ID

# --- شرح ---
# هذا هو نظام الرد السري. عندما يقوم المدير بالرد على رسالة موجهة،
# يقوم البوت بإرسال هذا الرد إلى المستخدم الأصلي.

async def reply_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يرسل رد المدير إلى المستخدم."""
    # تأكد أن المرسل هو المدير
    if update.effective_user.id != ADMIN_USER_ID:
        return

    # تأكد من أن الرسالة هي "رد" على رسالة أخرى
    if not update.message.reply_to_message:
        return

    # الرسالة التي تم الرد عليها
    replied_message = update.message.reply_to_message

    # نستخرج معرف المستخدم الأصلي من الرسالة المُعادة توجيهها
    original_user_id = None

    # إذا كانت الرسالة من النوع ForwardedMessage
    if replied_message.forward_from:
        original_user_id = replied_message.forward_from.id
    # إذا كانت الرسالة نصية تحتوي على المعرف (طريقتنا الاحتياطية)
    elif replied_message.text and "المعرف:" in replied_message.text:
        try:
            # نبحث عن السطر الذي يحتوي على المعرف ونستخرجه
            lines = replied_message.text.split('\n')
            for line in lines:
                if "المعرف:" in line:
                    original_user_id = int(line.split('`')[1])
                    break
        except (ValueError, IndexError):
            # فشل في استخراج المعرف
            await update.message.reply_text("لم أتمكن من العثور على معرف المستخدم في هذه الرسالة.")
            return

    if original_user_id:
        try:
            # أرسل رسالة المدير (الرد) إلى المستخدم الأصلي
            await context.bot.copy_message(
                chat_id=original_user_id,
                from_chat_id=update.effective_chat.id,
                message_id=update.message.message_id
            )
            await update.message.reply_text("✅ تم إرسال ردك بنجاح.")
        except Exception as e:
            await update.message.reply_text(f"⚠️ فشل إرسال الرد. قد يكون المستخدم قد حظر البوت.\n\nالخطأ: {e}")
    else:
        # هذه الرسالة ليست رداً على رسالة مستخدم يمكن التعرف عليها
        pass


# المعالج يستمع فقط للرسائل التي هي "ردود" من المدير
admin_reply_handler = MessageHandler(filters.REPLY & filters.User(user_id=ADMIN_USER_ID), reply_to_user)
