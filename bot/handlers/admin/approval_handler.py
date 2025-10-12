# -*- coding: utf-8 -*-

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ChatMemberHandler, CallbackQueryHandler
from telegram.constants import ChatMemberStatus
from config import ADMIN_USER_ID
from bot.database.manager import db # <-- التصحيح الجذري

async def new_member_handler_func(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    my_chat_member = update.my_chat_member
    if my_chat_member.new_chat_member.status == ChatMemberStatus.ADMINISTRATOR:
        chat = my_chat_member.chat
        
        # التأكد من أن القناة ليست معتمدة بالفعل
        is_approved = await db.is_channel_approved(chat.id) # <-- التصحيح الجذري
        if is_approved:
            return

        text = (f"سيدي المدير، تم إضافتي كمشرف في القناة التالية:\n\n"
                f"الاسم: {chat.title}\n"
                f"المعرف: @{chat.username}\n"
                f"ID: `{chat.id}`\n\n"
                "هل توافق على إضافتها إلى قائمة القنوات المعتمدة للنشر؟")
        
        keyboard = [
            [
                InlineKeyboardButton("✅ موافقة", callback_data=f"approve_{chat.id}_{chat.title}_{chat.username}"),
                InlineKeyboardButton("❌ رفض", callback_data=f"reject_{chat.id}")
            ]
        ]
        await context.bot.send_message(
            chat_id=ADMIN_USER_ID,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='MarkdownV2'
        )

async def channel_approval_handler_func(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data.split('_')
    action = data[0]
    chat_id = int(data[1])

    if action == "approve":
        title = data[2]
        username = data[3]
        await db.add_approved_channel(channel_id=chat_id, title=title, username=username) # <-- التصحيح الجذري
        await query.edit_message_text(f"✅ تم الموافقة على قناة '{title}' وإضافتها بنجاح.")
    
    elif action == "reject":
        try:
            await context.bot.leave_chat(chat_id)
            await query.edit_message_text(f"❌ تم رفض القناة ومغادرتها بنجاح.")
        except Exception as e:
            await query.edit_message_text(f"❌ تم رفض القناة، ولكن لم أتمكن من المغادرة. الخطأ: {e}")

new_member_handler = ChatMemberHandler(new_member_handler_func, ChatMemberHandler.MY_CHAT_MEMBER)
channel_approval_handler = CallbackQueryHandler(channel_approval_handler_func, pattern="^(approve|reject)_")
