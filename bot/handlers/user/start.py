# -*- coding: utf-8 -*-

from aiogram import types, Dispatcher
from bot.database.manager import db

async def show_main_menu(message: types.Message, edit_mode: bool = False):
    """
    وظيفة مركزية لعرض القائمة الرئيسية.
    يمكنها إما إرسال رسالة جديدة أو تعديل رسالة موجودة.
    """
    # بناء الأزرار
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    date_button_text = await db.get_text("date_button")
    time_button_text = await db.get_text("time_button")
    reminder_button_text = await db.get_text("reminder_button")
    keyboard.add(
        types.InlineKeyboardButton(text=date_button_text, callback_data="show_date"),
        types.InlineKeyboardButton(text=time_button_text, callback_data="show_time"),
        types.InlineKeyboardButton(text=reminder_button_text, callback_data="show_reminder")
    )

    # جلب رسالة الترحيب
    welcome_text = (await db.get_text("welcome_message")).format(user_mention=message.chat.get_mention(as_html=True))
    
    if edit_mode:
        # إذا كنا في وضع التعديل (قادمون من زر الرجوع)، نعدل الرسالة
        try:
            await message.edit_text(
                text=welcome_text,
                reply_markup=keyboard,
                parse_mode=types.ParseMode.HTML
            )
        except Exception:
            # في حال فشل التعديل (لأن المحتوى لم يتغير)، نتجاهل الخطأ
            pass
    else:
        # إذا كنا قادمين من أمر /start، نرسل رسالة جديدة
        await message.answer(
            text=welcome_text,
            reply_markup=keyboard,
            parse_mode=types.ParseMode.HTML
        )

async def start_command(message: types.Message):
    """
    هذا المعالج يستجيب لأمر /start.
    """
    await db.add_user(message.from_user)
    await show_main_menu(message) # استدعاء الوظيفة المركزية

def register_start_handlers(dp: Dispatcher):
    """تسجيل معالجات المستخدم."""
    dp.register_message_handler(start_command, commands=["start"])
