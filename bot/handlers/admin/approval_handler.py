# -*- coding: utf-8 -*-

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ChatMemberHandler, CallbackQueryHandler
from config import ADMIN_USER_ID
from bot.database.manager import add_approved_channel, is_channel_approved

# --- شرح ---
# هذا هو "حارس الأمن الذكي". يكتشف تلقائيًا عندما يتم إضافة البوت كمشرف
# في قناة جديدة ويرسل طلب موافقة للمدير.

async def track_new_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يتم تفعيله عندما يتغير وضع البوت في محادثة (مثل ترقيته لمشرف)."""
    if not update.my_chat_member:
        return

    new_member_status = update.my_chat_member.new_chat_member
    
    # نهتم فقط عندما يصبح البوت مشرفًا
    if new_member_status.status == 'administrator':
        channel_id = update.my_chat_member.chat.id
        channel_title = update.my_chat_member.chat.title
        
        # تحقق مما إذا كانت القناة معتمدة بالفعل لتجنب إرسال طلبات متكررة
        if await is_channel_approved(channel_id):
            return

        text = (
            f"⚠️ **طلب موافقة جديد** ⚠️\n\n"
            f"تمت إضافة البوت كمشرف في القناة التالية:\n"
            f"**الاسم:** {channel_title}\n"
            f"**المعرف:** `{channel_id}`\n\n"
            f"هل توافق على اعتماد هذه القناة ليتمكن البوت من النشر فيها؟"
        )
        keyboard = [
            [
                InlineKeyboardButton("✅ موافقة", callback_data=f"approve_channel_{channel_id}_{channel_title}"),
                InlineKeyboardButton("❌ رفض", callback_data=f"reject_channel_{channel_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=ADMIN_USER_ID, text=text, reply_markup=reply_markup, parse_mode='Markdown')

async def channel_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يعالج قرار المدير (موافقة أو رفض) بخصوص القناة الجديدة."""
    query = update.callback_query
    await query.answer()
    
    data = query.data.split("_")
    action = data[0]
    channel_id = int(data[2])

    if action == "approve":
        # نفكك العنوان من البيانات، مع مراعاة أنه قد يحتوي على "_"
        channel_title = "_".join(data[3:])
        await add_approved_channel(channel_id, channel_title)
        await query.edit_message_text(f"✅ تم اعتماد القناة '{channel_title}' بنجاح.")
        try:
            # إرسال رسالة ترحيب في القناة بعد الموافقة
            await context.bot.send_message(chat_id=channel_id, text="تم تفعيل البوت بنجاح في هذه القناة.")
        except Exception as e:
            await context.bot.send_message(chat_id=ADMIN_USER_ID, text=f"لم أتمكن من إرسال رسالة ترحيب في القناة '{channel_title}'. قد لا أملك صلاحية إرسال الرسائل.\nالخطأ: {e}")

    elif action == "reject":
        original_message = query.message.text
        await query.edit_message_text(f"{original_message}\n\n--- \n❌ تم رفض القناة. سيقوم البوت بمغادرتها الآن.")
        try:
            await context.bot.leave_chat(chat_id=channel_id)
        except Exception:
            # قد لا يتمكن من المغادرة إذا تمت إزالة صلاحياته بالفعل
            pass

channel_approval_tracker = ChatMemberHandler(track_new_channel, ChatMemberHandler.MY_CHAT_MEMBER)
channel_decision_handler = CallbackQueryHandler(channel_decision, pattern="^(approve|reject)_channel_")
