# -*- coding: utf-8 -*-

from aiogram import types, Dispatcher
from bot.database.manager import db

async def start_command(message: types.Message):
    """
    هذا المعالج يستجيب لأمر /start.
    """
    # حفظ المستخدم في قاعدة البيانات
    await db.add_user(message.from_user)
    
    # بناء الأزرار
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton(text="📅 التاريخ", callback_data="show_date"),
        types.InlineKeyboardButton(text="⏰ الساعة الآن", callback_data="show_time"),
        types.InlineKeyboardButton(text="📿 أذكار اليوم", callback_data="show_reminder"),
        types.InlineKeyboardButton(text="📨 تواصل مع الإدارة", callback_data="contact_admin")
    )

    welcome_text = (await db.get_text("welcome_message")).format(user_mention=message.from_user.get_mention(as_html=True))
    
    await message.answer(
        text=welcome_text,
        reply_markup=keyboard,
        parse_mode=types.ParseMode.HTML
    )

def register_start_handlers(dp: Dispatcher):
    """تسجيل معالجات المستخدم."""
    dp.register_message_handler(start_command, commands=["start"])
