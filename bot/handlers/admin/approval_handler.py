# -*- coding: utf-8 -*-

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ChatMemberHandler, CallbackQueryHandler
from telegram.constants import ChatMemberStatus
from config import ADMIN_USER_ID
from bot.database.manager import db

async def new_member_handler_func(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    my_chat_member = update.my_chat_member
    if my_chat_member.new_chat_member.status == ChatMemberStatus.ADMINISTRATOR:
        chat = my_chat_member.chat
        
        is_approved = await db.is_channel_approved(chat.id)
        if is_approved:
            return

        username = chat.username or "لا يوجد"
        text = (f"سيدي المدير، تم إضافتي كمشرف في القناة التالية:\n\n"
                f"الاسم: {chat.title}\n"
                f"المعرف: @{username}\n"
                f"ID: `{chat.id}`\n\n"
                "هل توافق على إضافتها إلى قائمة القنوات المعتمدة للنشر؟")
        
        # نمرر البيانات في callback_data
        callback_data_approve = f"approve_{chat.id}_{chat.title}_{username}"
        callback_data_reject = f"reject_{chat.id}"
        
        # التأكد من أن طول البيانات لا يتجاوز 64 بايت
        if len(callback_data_approve.encode('utf-8')) > 64:
             callback_data_approve = f"approve_{chat.id}" # نسخة مختصرة إذا كان الاسم طويلاً
             await context.bot.send_message(chat_id=ADMIN_USER_ID, text=f"تنبيه: اسم القناة ({chat.title}) طويل جداً، سيتم استخدام المعرف فقط.")


        keyboard = [
            [
                InlineKeyboardButton("✅ موافقة", callback_data=callback_data_approve),
                InlineKeyboardButton("❌ رفض", callback_data=callback_data_reject)
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
        title = "N/A"
        username = "N/A"
        # محاولة استخراج الاسم والمعرف إذا كانا موجودين
        if len(data) > 2:
            title = data[2]
            if len(data) > 3:
                username = data[3]
        
        # إذا لم نتمكن من الحصول على الاسم من الزر، نحاول الحصول عليه من التلغرام
        if title == "N/A":
            try:
                chat = await context.bot.get_chat(chat_id)
                title = chat.title
                username = chat.username or "لا يوجد"
            except Exception as e:
                print(f"فشل في الحصول على بيانات القناة {chat_id}: {e}")
                title = f"قناة {chat_id}"

        await db.add_approved_channel(channel_id=chat_id, title=title, username=username)
        await query.edit_message_text(f"✅ تم الموافقة على قناة '{title}' وإضافتها بنجاح.")
    
    elif action == "reject":
        try:
            chat_title = ""
            try:
                chat = await context.bot.get_chat(chat_id)
                chat_title = f"'{chat.title}'"
            except:
                pass

            await context.bot.leave_chat(chat_id)
            await query.edit_message_text(f"❌ تم رفض القناة {chat_title} ومغادرتها بنجاح.")
        except Exception as e:
            await query.edit_message_text(f"❌ تم رفض القناة، ولكن لم أتمكن من المغادرة. الخطأ: {e}")

new_member_handler = ChatMemberHandler(new_member_handler_func, ChatMemberHandler.MY_CHAT_MEMBER)
channel_approval_handler = CallbackQueryHandler(channel_approval_handler_func, pattern="^(approve|reject)_")
