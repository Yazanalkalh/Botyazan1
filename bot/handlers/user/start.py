# -*- coding: utf-8 -*-

import re
from aiogram import types, Dispatcher, Bot
from aiogram.utils.exceptions import ChatNotFound, BadRequest

from bot.database.manager import db
from config import ADMIN_USER_ID

def escape_markdown(text: str) -> str:
    """وظيفة لتعقيم النص ليكون آمناً للاستخدام مع MarkdownV2."""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

async def notify_admin_of_new_user(user: types.User, bot: Bot):
    """يرسل إشعاراً للمدير عند دخول مستخدم جديد (مع تعقيم النص)."""
    try:
        # --- الإصلاح رقم 2: تعقيم أسماء المستخدمين ---
        safe_full_name = escape_markdown(user.full_name)
        safe_username = escape_markdown(f"@{user.username}") if user.username else "لا يوجد"
        
        user_link = f"[{safe_full_name}](tg://user?id={user.id})"
        
        notification_text = (
            f"👤 *دخل شخص جديد إلى البوت*\n\n"
            f"🗣️ *اسمه:* {user_link}\n"
            f"🌀 *معرفه:* {safe_username}\n"
            f"🆔 *ايديه:* `{user.id}`"
        )
        
        await bot.send_message(
            chat_id=ADMIN_USER_ID,
            text=notification_text,
            parse_mode=types.ParseMode.MARKDOWN_V2
        )
    except Exception as e:
        print(f"فشل إرسال إشعار المستخدم الجديد: {e}")

async def is_user_subscribed(user_id: int, bot: Bot) -> bool:
    # ... الكود هنا يبقى كما هو ...
    required_channels = await db.get_subscription_channels()
    if not required_channels: return True
    for channel_username in required_channels:
        try:
            member = await bot.get_chat_member(chat_id=f"@{channel_username}", user_id=user_id)
            if member.status not in ["creator", "administrator", "member"]: return False
        except (ChatNotFound, BadRequest):
            print(f"Warning: Could not check channel @{channel_username}.")
            continue
    return True

async def show_main_menu(message: types.Message, edit_mode: bool = False):
    # ... الكود هنا يبقى كما هو ...
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    date_button_text, time_button_text, reminder_button_text = await db.get_text("date_button"), await db.get_text("time_button"), await db.get_text("reminder_button")
    keyboard.add(types.InlineKeyboardButton(text=date_button_text, callback_data="show_date"), types.InlineKeyboardButton(text=time_button_text, callback_data="show_time"), types.InlineKeyboardButton(text=reminder_button_text, callback_data="show_reminder"))
    welcome_text = (await db.get_text("welcome_message")).format(user_mention=message.chat.get_mention(as_html=True))
    if edit_mode:
        try: await message.edit_text(text=welcome_text, reply_markup=keyboard, parse_mode=types.ParseMode.HTML)
        except Exception: pass
    else: await message.answer(text=welcome_text, reply_markup=keyboard, parse_mode=types.ParseMode.HTML)

async def show_subscription_message(message: types.Message):
    # ... الكود هنا يبقى كما هو ...
    channels = await db.get_subscription_channels()
    keyboard = types.InlineKeyboardMarkup()
    text = "🛑 *عذراً، يجب عليك الاشتراك في القنوات التالية أولاً:*\n\n"
    for username in channels:
        text += f"▪️ `@{username}`\n"
        keyboard.add(types.InlineKeyboardButton(text=f"الانضمام إلى @{username}", url=f"https://t.me/{username}"))
    keyboard.add(types.InlineKeyboardButton(text="✅ لقد اشتركت، تحقق الآن", callback_data="check_subscription"))
    await message.answer(text, reply_markup=keyboard, parse_mode=types.ParseMode.MARKDOWN_V2)

async def start_command(message: types.Message):
    """المعالج الرئيسي لأمر /start."""
    user = message.from_user
    is_new = await db.add_user(user)
    if is_new:
        await notify_admin_of_new_user(user, message.bot)
    
    if await is_user_subscribed(user.id, message.bot):
        await show_main_menu(message)
    else:
        await show_subscription_message(message)

async def check_subscription_callback(call: types.CallbackQuery):
    # ... الكود هنا يبقى كما هو ...
    await call.answer(text="جاري التحقق...", show_alert=False)
    if await is_user_subscribed(call.from_user.id, call.bot):
        await show_main_menu(call.message, edit_mode=True)
    else:
        await call.answer(text="عذراً، لم تشترك في جميع القنوات بعد.", show_alert=True)

def register_start_handlers(dp: Dispatcher):
    dp.register_message_handler(start_command, commands=["start"])
    dp.register_callback_query_handler(check_subscription_callback, text="check_subscription")
