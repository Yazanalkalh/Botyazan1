# -*- coding: utf-8 -*-

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ChatMemberHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ChatMemberStatus

from config import ADMIN_USER_ID
from bot.database.manager import add_approved_channel, is_channel_approved

async def track_channel_addition(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    result = update.chat_member
    
    was_member = result.old_chat_member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]
    is_now_admin = result.new_chat_member.status == ChatMemberStatus.ADMINISTRATOR
    is_channel = result.chat.type == 'channel'

    if was_member and is_now_admin and is_channel:
        chat = result.chat
        
        if is_channel_approved(chat.id):
            return

        text = (
            "🔔 **تنبيه إداري: طلب إضافة قناة جديدة**\n\n"
            f"تمت إضافة البوت كمشرف في القناة التالية:\n\n"
            f"**- اسم القناة:** {chat.title}\n"
            f"**- معرف القناة:** `{chat.id}`\n\n"
            "هل توافق على إضافة هذه القناة إلى قائمة القنوات المعتمدة للنشر؟"
        )
        
        # نمرر العنوان كجزء من البيانات لأنه قد لا يكون متاحاً لاحقاً
        # نستخدم ترميزاً بسيطاً للتعامل مع العناوين التي قد تحتوي على "_"
        encoded_title = str(chat.title).replace("_", "-")
        keyboard = [
            [
                InlineKeyboardButton("✅ موافقة", callback_data=f"approve_channel_{chat.id}_{encoded_title}"),
                InlineKeyboardButton("❌ رفض", callback_data=f"reject_channel_{chat.id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(chat_id=ADMIN_USER_ID, text=text, reply_markup=reply_markup, parse_mode='Markdown')

async def approval_decision_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    data = query.data.split('_')
    action = data[0]
    channel_id = int(data[2])

    if action == "approve":
        channel_title = data[3].replace("-", "_") # استعادة العنوان الأصلي
        add_approved_channel(channel_id, channel_title)
        await query.edit_message_text(text=f"✅ **تمت الموافقة على القناة:**\n\n- {channel_title}\n- `{channel_id}`\n\nأصبحت الآن ضمن القنوات المعتمدة.")
    
    elif action == "reject":
        try:
            await context.bot.leave_chat(chat_id=channel_id)
            await query.edit_message_text(text=f"❌ **تم رفض القناة ومغادرتها بنجاح.**\n\n- معرف القناة: `{channel_id}`")
        except Exception as e:
            await query.edit_message_text(text=f"⚠️ **حدث خطأ أثناء محاولة مغادرة القناة:**\n\n`{e}`\n\nقد أكون لم أعد مشرفاً فيها. تم تسجيل الرفض.")

channel_approval_tracker = ChatMemberHandler(track_channel_addition, ChatMemberHandler.MY_CHAT_MEMBER)
channel_decision_handler = CallbackQueryHandler(approval_decision_handler, pattern="^(approve_channel_|reject_channel_)")
